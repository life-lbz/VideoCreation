from __future__ import annotations

import json
import sqlite3
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.models import TaskStatus, VideoTask


PLANS: dict[str, dict[str, Any]] = {
    "starter": {"id": "starter", "name": "基础版", "monthlyCredits": 160, "price": 0},
    "creator": {"id": "creator", "name": "创作者版", "monthlyCredits": 600, "price": 299},
    "team": {"id": "team", "name": "团队版", "monthlyCredits": 2000, "price": 999},
}


class InsufficientCreditsError(RuntimeError):
    pass


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def now_ms() -> int:
    return int(time.time() * 1000)


def month_start_ms() -> int:
    now = datetime.now(UTC)
    return int(datetime(now.year, now.month, 1, tzinfo=UTC).timestamp() * 1000)


def next_month_start_ms() -> int:
    now = datetime.now(UTC)
    year, month = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)
    return int(datetime(year, month, 1, tzinfo=UTC).timestamp() * 1000)


class AppStore:
    def __init__(self, database_path: str | Path) -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, factory=ClosingConnection)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS account (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    plan_id TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                INSERT OR IGNORE INTO account (id, plan_id, updated_at)
                VALUES (1, 'starter', 0);

                CREATE TABLE IF NOT EXISTS reservations (
                    idempotency_key TEXT PRIMARY KEY,
                    task_id TEXT UNIQUE,
                    credits INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    settled_at INTEGER
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS works (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    ratio TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    resolution TEXT NOT NULL DEFAULT '720p',
                    result_url TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS billing_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                """
            )
            work_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(works)").fetchall()
            }
            if "resolution" not in work_columns:
                connection.execute(
                    "ALTER TABLE works ADD COLUMN resolution TEXT NOT NULL DEFAULT '720p'"
                )

    def _plan_id(self, connection: sqlite3.Connection) -> str:
        row = connection.execute("SELECT plan_id FROM account WHERE id = 1").fetchone()
        return str(row["plan_id"])

    def _usage_values(self, connection: sqlite3.Connection) -> tuple[int, int]:
        start = month_start_ms()
        used = connection.execute(
            "SELECT COALESCE(SUM(credits), 0) AS value FROM reservations WHERE state = 'charged' AND created_at >= ?",
            (start,),
        ).fetchone()["value"]
        reserved = connection.execute(
            "SELECT COALESCE(SUM(credits), 0) AS value FROM reservations WHERE state = 'reserved' AND created_at >= ?",
            (start,),
        ).fetchone()["value"]
        return int(used), int(reserved)

    def get_usage(self) -> dict[str, Any]:
        with self._connect() as connection:
            plan = PLANS[self._plan_id(connection)]
            used, reserved = self._usage_values(connection)
            limit = int(plan["monthlyCredits"])
            return {
                "plan": plan,
                "monthlyLimit": limit,
                "usedCredits": used,
                "reservedCredits": reserved,
                "availableCredits": max(0, limit - used - reserved),
                "renewsAt": next_month_start_ms(),
            }

    def reserve(self, idempotency_key: str, credits: int) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT 1 FROM reservations WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if existing:
                connection.commit()
                return
            plan = PLANS[self._plan_id(connection)]
            used, reserved = self._usage_values(connection)
            if used + reserved + credits > int(plan["monthlyCredits"]):
                connection.rollback()
                raise InsufficientCreditsError("本月可用创作额度不足")
            connection.execute(
                "INSERT INTO reservations (idempotency_key, credits, state, created_at) VALUES (?, ?, 'reserved', ?)",
                (idempotency_key, credits, now_ms()),
            )
            connection.commit()

    def release(self, idempotency_key: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE reservations SET state = 'released', settled_at = ? WHERE idempotency_key = ? AND state = 'reserved'",
                (now_ms(), idempotency_key),
            )

    @staticmethod
    def _task_payload(task: VideoTask) -> str:
        payload = task.model_dump(mode="json")
        payload["externalTaskId"] = task.externalTaskId
        payload["idempotencyKey"] = task.idempotencyKey
        return json.dumps(payload, ensure_ascii=False)

    def save_task(self, task: VideoTask) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks (task_id, idempotency_key, payload_json, status, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (task.id, task.idempotencyKey, self._task_payload(task), task.status.value, now_ms()),
            )
            connection.execute(
                "UPDATE reservations SET task_id = ? WHERE idempotency_key = ?",
                (task.id, task.idempotencyKey),
            )

    def sync_task(self, task: VideoTask) -> None:
        with self._lock:
            self.save_task(task)
            with self._connect() as connection:
                if task.status == TaskStatus.SUCCEEDED:
                    connection.execute(
                        "UPDATE reservations SET state = 'charged', settled_at = ? WHERE task_id = ? AND state = 'reserved'",
                        (now_ms(), task.id),
                    )
                    if task.resultUrl:
                        title = task.input.prompt.strip().rstrip("。！？")[:18] or "未命名作品"
                        connection.execute(
                            """
                            INSERT OR IGNORE INTO works
                            (task_id, title, prompt, ratio, duration, resolution, result_url, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                task.id,
                                title,
                                task.input.prompt,
                                task.input.ratio,
                                task.input.duration,
                                task.input.resolution,
                                task.resultUrl,
                                task.completedAt or now_ms(),
                            ),
                        )
                elif task.status in {TaskStatus.FAILED, TaskStatus.CANCELLED}:
                    connection.execute(
                        "UPDATE reservations SET state = 'released', settled_at = ? WHERE task_id = ? AND state = 'reserved'",
                        (now_ms(), task.id),
                    )

    def get_task_by_idempotency(self, idempotency_key: str) -> VideoTask | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM tasks WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
        return VideoTask.model_validate_json(row["payload_json"]) if row else None

    def get_task(self, task_id: str) -> VideoTask | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
        return VideoTask.model_validate_json(row["payload_json"]) if row else None

    def list_active_tasks(self) -> list[VideoTask]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM tasks WHERE status IN ('queued', 'generating', 'post_processing')"
            ).fetchall()
        return [VideoTask.model_validate_json(row["payload_json"]) for row in rows]

    def list_works(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT task_id, title, prompt, ratio, duration, resolution, result_url, created_at FROM works ORDER BY created_at DESC"
            ).fetchall()
        return [
            {
                "id": row["task_id"],
                "title": row["title"],
                "prompt": row["prompt"],
                "ratio": row["ratio"],
                "duration": row["duration"],
                "resolution": row["resolution"],
                "resultUrl": row["result_url"],
                "createdAt": row["created_at"],
            }
            for row in rows
        ]

    def delete_work(self, task_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM works WHERE task_id = ?", (task_id,))
            return cursor.rowcount > 0

    def get_billing(self) -> dict[str, Any]:
        usage = self.get_usage()
        with self._connect() as connection:
            charges = connection.execute(
                """
                SELECT r.task_id, r.credits, r.state, r.created_at, w.title
                FROM reservations r LEFT JOIN works w ON w.task_id = r.task_id
                WHERE r.created_at >= ? ORDER BY r.created_at DESC LIMIT 50
                """,
                (month_start_ms(),),
            ).fetchall()
            events = connection.execute(
                "SELECT kind, description, created_at FROM billing_events ORDER BY created_at DESC LIMIT 50"
            ).fetchall()
        return {
            **usage,
            "plans": list(PLANS.values()),
            "records": [
                {
                    "taskId": row["task_id"],
                    "title": row["title"] or "视频生成任务",
                    "credits": row["credits"],
                    "status": row["state"],
                    "createdAt": row["created_at"],
                }
                for row in charges
            ],
            "events": [
                {
                    "kind": row["kind"],
                    "description": row["description"],
                    "createdAt": row["created_at"],
                }
                for row in events
            ],
        }

    def change_plan(self, plan_id: str) -> dict[str, Any]:
        if plan_id not in PLANS:
            raise ValueError("不存在该套餐")
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            used, reserved = self._usage_values(connection)
            if used + reserved > int(PLANS[plan_id]["monthlyCredits"]):
                connection.rollback()
                raise InsufficientCreditsError("当前用量超过目标套餐额度，暂时无法切换")
            previous = self._plan_id(connection)
            connection.execute(
                "UPDATE account SET plan_id = ?, updated_at = ? WHERE id = 1",
                (plan_id, now_ms()),
            )
            if previous != plan_id:
                connection.execute(
                    "INSERT INTO billing_events (kind, description, created_at) VALUES ('plan_change', ?, ?)",
                    (f"套餐从 {PLANS[previous]['name']} 切换为 {PLANS[plan_id]['name']}", now_ms()),
                )
            connection.commit()
        return self.get_billing()
