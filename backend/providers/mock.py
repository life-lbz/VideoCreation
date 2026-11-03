from __future__ import annotations

import threading
import time
import uuid

from backend.models import CostEstimate, GenerationInput, TaskStatus, VideoTask
from backend.providers.base import VideoProvider

DEFAULT_RESULT = "/assets/demo-loop.mp4"


def now_ms() -> int:
    return int(time.time() * 1000)


def current_task_state(task: VideoTask, current_time_ms: int | None = None) -> VideoTask:
    if task.status == TaskStatus.CANCELLED:
        return task

    current_time_ms = current_time_ms if current_time_ms is not None else now_ms()
    elapsed = current_time_ms - task.createdAt
    update: dict[str, object]

    if elapsed < 1_200:
        update = {"status": TaskStatus.QUEUED, "progress": 12, "stage": "正在分配创作资源"}
    elif elapsed < 5_800:
        progress = min(78, round(20 + ((elapsed - 1_200) / 4_600) * 58))
        update = {"status": TaskStatus.GENERATING, "progress": progress, "stage": "正在生成镜头与光影"}
    elif elapsed < 7_400:
        update = {"status": TaskStatus.POST_PROCESSING, "progress": 91, "stage": "正在完成画面与编码"}
    else:
        update = {
            "status": TaskStatus.SUCCEEDED,
            "progress": 100,
            "stage": "视频已经生成",
            "resultUrl": DEFAULT_RESULT,
            "completedAt": task.completedAt or current_time_ms,
        }
    return task.model_copy(update=update)


class MockVideoProvider(VideoProvider):
    def __init__(self) -> None:
        self._tasks: dict[str, VideoTask] = {}
        self._idempotency_index: dict[str, str] = {}
        self._lock = threading.RLock()

    def get_capabilities(self) -> dict[str, object]:
        return {
            "provider": "mock",
            "modelAlias": "video_standard",
            "ratios": ["9:16", "16:9", "1:1"],
            "durations": [5, 8, 10, 15],
            "resolutions": ["480p", "720p", "1080p"],
            "supportsTextToVideo": True,
            "supportsReferenceImage": False,
        }

    def restore_task(self, task: VideoTask) -> None:
        with self._lock:
            self._tasks[task.id] = task
            self._idempotency_index[task.idempotencyKey] = task.id

    def estimate(self, generation_input: GenerationInput) -> CostEstimate:
        quality_factor = {"fast": 0.72, "standard": 1.0, "pro": 1.7}[generation_input.quality]
        resolution_factor = {"480p": 0.58, "720p": 1.0, "1080p": 1.8}[generation_input.resolution]
        audio_factor = 1.15 if generation_input.generateAudio else 1.0
        raw_credits = generation_input.duration * quality_factor * resolution_factor * audio_factor
        credits = max(1, int(-(-raw_credits // 1)))
        estimated_seconds = {"fast": 32, "standard": 48, "pro": 75}[generation_input.quality]
        return CostEstimate(
            credits=credits,
            estimatedSeconds=estimated_seconds,
            priceVersion="mock-2026-08",
        )

    def create_task(self, generation_input: GenerationInput, idempotency_key: str) -> VideoTask:
        with self._lock:
            existing_id = self._idempotency_index.get(idempotency_key)
            if existing_id:
                return current_task_state(self._tasks[existing_id])

            task = VideoTask(
                id=f"gen_{uuid.uuid4().hex[:18]}",
                externalTaskId=f"mock_{uuid.uuid4().hex[:8]}",
                idempotencyKey=idempotency_key,
                status=TaskStatus.QUEUED,
                progress=4,
                stage="任务已进入队列",
                createdAt=now_ms(),
                input=generation_input,
            )
            self._tasks[task.id] = task
            self._idempotency_index[idempotency_key] = task.id
            return task

    def get_task(self, task_id: str) -> VideoTask | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            updated = current_task_state(task)
            self._tasks[task_id] = updated
            return updated

    def cancel_task(self, task_id: str) -> VideoTask | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            if task.status == TaskStatus.SUCCEEDED:
                return task
            cancelled = task.model_copy(
                update={
                    "status": TaskStatus.CANCELLED,
                    "stage": "任务已取消",
                    "cancelledAt": now_ms(),
                }
            )
            self._tasks[task_id] = cancelled
            return cancelled
