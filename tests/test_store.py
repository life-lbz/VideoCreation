from __future__ import annotations

import unittest
import time
from tempfile import TemporaryDirectory

from backend.models import GenerationInput, TaskStatus, VideoTask
from backend.store import AppStore


class AppStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.store = AppStore(f"{self.temp_dir.name}/store.db")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def task(self, task_id: str, status: TaskStatus, result_url: str | None = None) -> VideoTask:
        created_at = int(time.time() * 1000)
        return VideoTask(
            id=task_id,
            externalTaskId=task_id,
            idempotencyKey=f"key-{task_id}",
            status=status,
            progress=100 if status == TaskStatus.SUCCEEDED else 4,
            stage="测试任务",
            createdAt=created_at,
            completedAt=created_at + 100_000 if status == TaskStatus.SUCCEEDED else None,
            resultUrl=result_url,
            input=GenerationInput(prompt="真实作品入库测试", duration=8),
        )

    def test_successful_task_charges_credits_and_creates_work(self) -> None:
        task = self.task("success", TaskStatus.QUEUED)
        self.store.reserve(task.idempotencyKey, 8)
        self.store.save_task(task)
        self.assertEqual(self.store.get_usage()["reservedCredits"], 8)

        completed = task.model_copy(
            update={
                "status": TaskStatus.SUCCEEDED,
                "progress": 100,
                "resultUrl": "https://example.com/video.mp4",
                "completedAt": task.createdAt + 100_000,
            }
        )
        self.store.sync_task(completed)
        usage = self.store.get_usage()
        self.assertEqual(usage["reservedCredits"], 0)
        self.assertEqual(usage["usedCredits"], 8)
        self.assertEqual(len(self.store.list_works()), 1)

    def test_cancelled_task_releases_reservation(self) -> None:
        task = self.task("cancelled", TaskStatus.QUEUED)
        self.store.reserve(task.idempotencyKey, 8)
        self.store.save_task(task)
        self.store.sync_task(task.model_copy(update={"status": TaskStatus.CANCELLED}))
        usage = self.store.get_usage()
        self.assertEqual(usage["reservedCredits"], 0)
        self.assertEqual(usage["usedCredits"], 0)


if __name__ == "__main__":
    unittest.main()
