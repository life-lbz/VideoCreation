from __future__ import annotations

import json
import math
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from backend.models import CostEstimate, GenerationInput, TaskStatus, VideoTask
from backend.providers.base import VideoProvider


class ProviderNotConfiguredError(RuntimeError):
    code = "PROVIDER_NOT_CONFIGURED"


class ProviderApiError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 502, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class VolcengineConfig:
    api_key: str | None
    model_id: str
    fast_model_id: str
    base_url: str
    watermark: bool = True


class VolcengineVideoProvider(VideoProvider):
    """火山方舟 Seedance 视频生成适配器。"""

    MODEL_MANAGEMENT_URL = (
        "https://console.volcengine.com/ark/region%3Aark%2Bcn-beijing/"
        "openManagement?OpenTokenDrawer=false"
    )

    def __init__(self, config: VolcengineConfig) -> None:
        self.config = config
        self._tasks: dict[str, VideoTask] = {}
        self._idempotency_index: dict[str, str] = {}
        self._lock = threading.RLock()

    def _require_api_key(self) -> str:
        if not self.config.api_key:
            raise ProviderNotConfiguredError("ARK_API_KEY is not configured")
        return self.config.api_key

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload else None
        request = urllib.request.Request(
            f"{self.config.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self._require_api_key()}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                detail = {}
            error = detail.get("error", detail) if isinstance(detail, dict) else {}
            code = str(error.get("code", "PROVIDER_HTTP_ERROR"))
            message = str(error.get("message", "视频供应商请求失败"))
            # Providers may echo request details; never expose the bearer key.
            if self.config.api_key:
                code = code.replace(self.config.api_key, "[redacted]")
                message = message.replace(self.config.api_key, "[redacted]")
            raise ProviderApiError(
                code=code,
                message=message,
                status_code=exc.code,
                retryable=exc.code == 429 or exc.code >= 500,
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ProviderApiError(
                code="PROVIDER_UNAVAILABLE",
                message="暂时无法连接视频供应商",
                status_code=503,
                retryable=True,
            ) from exc
        except json.JSONDecodeError as exc:
            raise ProviderApiError(
                code="INVALID_PROVIDER_RESPONSE",
                message="视频供应商返回了无法解析的数据",
                status_code=502,
                retryable=True,
            ) from exc

    def get_capabilities(self) -> dict[str, object]:
        return {
            "provider": "volcengine_ark",
            "modelAlias": "video_standard",
            "modelId": self.config.model_id,
            "ratios": ["9:16", "16:9", "1:1"],
            "durations": [5, 8, 10, 15],
            "resolutions": ["480p", "720p", "1080p"],
            "supportsTextToVideo": True,
            "supportsReferenceImage": True,
        }

    def restore_task(self, task: VideoTask) -> None:
        with self._lock:
            self._tasks[task.id] = task
            self._idempotency_index[task.idempotencyKey] = task.id

    def estimate(self, generation_input: GenerationInput) -> CostEstimate:
        quality_factor = {"fast": 0.72, "standard": 1.0, "pro": 1.7}[generation_input.quality]
        resolution_factor = {"480p": 0.58, "720p": 1.0, "1080p": 1.8}[generation_input.resolution]
        audio_factor = 1.15 if generation_input.generateAudio else 1.0
        credits = max(
            1,
            math.ceil(generation_input.duration * quality_factor * resolution_factor * audio_factor),
        )
        estimated_seconds = {"fast": 45, "standard": 90, "pro": 120}[generation_input.quality]
        return CostEstimate(
            credits=credits,
            estimatedSeconds=estimated_seconds,
            priceVersion="ark-seedance-2026-08",
        )

    def create_task(self, generation_input: GenerationInput, idempotency_key: str) -> VideoTask:
        with self._lock:
            existing_id = self._idempotency_index.get(idempotency_key)
            if existing_id:
                return self.get_task(existing_id) or self._tasks[existing_id]

            use_fast_model = (
                generation_input.quality == "fast"
                and generation_input.resolution != "1080p"
            )
            model_id = self.config.fast_model_id if use_fast_model else self.config.model_id
            response = self._request_json(
                "POST",
                "/contents/generations/tasks",
                {
                    "model": model_id,
                    "content": [{"type": "text", "text": generation_input.prompt}],
                    "ratio": generation_input.ratio,
                    "duration": generation_input.duration,
                    "resolution": generation_input.resolution,
                    "generate_audio": generation_input.generateAudio,
                    "watermark": self.config.watermark,
                },
            )
            external_id = str(response.get("id", ""))
            if not external_id:
                raise ProviderApiError(
                    "INVALID_PROVIDER_RESPONSE",
                    "视频供应商没有返回任务 ID",
                    retryable=True,
                )
            created_at = int(time.time() * 1000)
            task = VideoTask(
                id=external_id,
                externalTaskId=external_id,
                idempotencyKey=idempotency_key,
                status=TaskStatus.QUEUED,
                progress=4,
                stage="任务已提交到火山方舟",
                createdAt=created_at,
                input=generation_input,
            )
            self._tasks[external_id] = task
            self._idempotency_index[idempotency_key] = external_id
            return task

    def get_task(self, task_id: str) -> VideoTask | None:
        with self._lock:
            local_task = self._tasks.get(task_id)
            if local_task is None:
                return None
            response = self._request_json("GET", f"/contents/generations/tasks/{task_id}")
            external_status = str(response.get("status", "queued"))
            status_map = {
                "queued": (TaskStatus.QUEUED, 12, "正在等待火山方舟创作资源"),
                "running": (TaskStatus.GENERATING, 58, "Seedance 正在生成视频"),
                "succeeded": (TaskStatus.SUCCEEDED, 100, "视频已经生成"),
                "failed": (TaskStatus.FAILED, 100, "视频生成失败"),
                "cancelled": (TaskStatus.CANCELLED, local_task.progress, "任务已取消"),
                "expired": (TaskStatus.FAILED, 100, "视频任务已过期"),
            }
            status_value, progress, stage = status_map.get(
                external_status,
                (TaskStatus.GENERATING, local_task.progress, "正在同步视频任务"),
            )
            content = response.get("content") or {}
            video_url = content.get("video_url") if isinstance(content, dict) else None
            provider_error = response.get("error") or {}
            error_code = str(provider_error.get("code", "")) if isinstance(provider_error, dict) else ""
            if self.config.api_key:
                error_code = error_code.replace(self.config.api_key, "[redacted]")
            error_message = None
            action_url = None
            if status_value == TaskStatus.FAILED:
                if error_code == "SetLimitExceeded":
                    stage = "火山方舟额度或模型权限受限"
                    error_message = (
                        "火山方舟已暂停该模型：账号达到安心体验模式推理上限。"
                        "请前往模型开通管理调整或关闭安心体验模式后重试。"
                    )
                    action_url = self.MODEL_MANAGEMENT_URL
                elif isinstance(provider_error, dict) and provider_error.get("message"):
                    error_message = str(provider_error["message"])
                    if self.config.api_key:
                        error_message = error_message.replace(self.config.api_key, "[redacted]")
                else:
                    error_message = "视频供应商未能完成该任务，请检查模型权限、余额和参数后重试。"
            updated_at = int(time.time() * 1000)
            updated = local_task.model_copy(
                update={
                    "status": status_value,
                    "progress": progress,
                    "stage": stage,
                    "resultUrl": video_url,
                    "completedAt": updated_at if status_value == TaskStatus.SUCCEEDED else None,
                    "errorCode": error_code or None,
                    "errorMessage": error_message,
                    "actionUrl": action_url,
                }
            )
            self._tasks[task_id] = updated
            return updated

    def cancel_task(self, task_id: str) -> VideoTask | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            self._request_json("DELETE", f"/contents/generations/tasks/{task_id}")
            cancelled = task.model_copy(
                update={
                    "status": TaskStatus.CANCELLED,
                    "stage": "任务已取消",
                    "cancelledAt": int(time.time() * 1000),
                }
            )
            self._tasks[task_id] = cancelled
            return cancelled
