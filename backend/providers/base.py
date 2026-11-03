from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.models import CostEstimate, GenerationInput, VideoTask


class VideoProvider(ABC):
    """供应商无关的视频生成协议。"""

    @abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def estimate(self, generation_input: GenerationInput) -> CostEstimate:
        raise NotImplementedError

    @abstractmethod
    def create_task(self, generation_input: GenerationInput, idempotency_key: str) -> VideoTask:
        raise NotImplementedError

    @abstractmethod
    def get_task(self, task_id: str) -> VideoTask | None:
        raise NotImplementedError

    @abstractmethod
    def cancel_task(self, task_id: str) -> VideoTask | None:
        raise NotImplementedError

    def restore_task(self, task: VideoTask) -> None:
        """Restore a persisted active task after an application restart."""
        return None
