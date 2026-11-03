"""Fixed-endpoint video adapters. No credential or upstream body is logged."""
from __future__ import annotations

import json
import time
import uuid
import urllib.request
import urllib.error
import threading
from functools import wraps

from backend.models import VideoTask, TaskStatus
from backend.providers.volcengine import VolcengineVideoProvider, ProviderApiError, ProviderNotConfiguredError


def synchronized(function):
    @wraps(function)
    def wrapped(self, *args, **kwargs):
        with self._lock:
            return function(self, *args, **kwargs)
    return wrapped

SPECS = {
    "volcengine": dict(name="火山方舟", baseUrl="https://ark.cn-beijing.volces.com/api/v3", models=["Seedance 2.0", "Seedance 2.0 Fast"], ratios=["9:16", "16:9", "1:1"], durations=[5, 8, 10, 15], resolutions=["480p", "720p", "1080p"], supportsAudio=True, maxPromptLength=1200, supportsCancel=True, note="使用北京区域方舟 API Key；模型需开通权限。"),
    "wan": dict(name="通义万相", baseUrl="https://dashscope.aliyuncs.com/api/v1", models=["wan2.6-t2v"], ratios=["9:16", "16:9", "1:1"], durations=[5, 10, 15], resolutions=["720p", "1080p"], supportsAudio=True, maxPromptLength=1200, supportsCancel=False, note="北京区域 DashScope API Key；wan2.6-t2v，提交后不支持取消。"),
    "runway": dict(name="Runway", baseUrl="https://api.dev.runwayml.com/v1", models=["gen4.5"], ratios=["9:16", "16:9"], durations=[5, 8, 10], resolutions=["720p"], supportsAudio=False, maxPromptLength=1000, supportsCancel=True, note="Gen-4.5 文生视频，720p，无原生音频。"),
    "luma": dict(name="Luma", baseUrl="https://api.lumalabs.ai/dream-machine/v1", models=["ray-flash-2", "ray-2"], ratios=["9:16", "16:9", "1:1"], durations=[5], resolutions=["720p", "1080p"], supportsAudio=False, maxPromptLength=1200, supportsCancel=False, note="快速档使用 ray-flash-2，其余使用 ray-2；提交后不支持取消。"),
}


def capabilities(provider_id):
    spec = SPECS[provider_id]
    return {**{key: spec[key] for key in ("ratios", "durations", "resolutions", "supportsAudio", "maxPromptLength", "supportsCancel")}, "requiresAudio": provider_id == "wan"}


def validate_input(provider_id, value):
    caps = capabilities(provider_id)
    if caps["requiresAudio"] and not value.generateAudio:
        raise ProviderApiError("UNSUPPORTED_PARAMETER", "通义万相 wan2.6 固定生成音频，请启用音频后提交", 422)
    for field, allowed in (("ratio", "ratios"), ("duration", "durations"), ("resolution", "resolutions")):
        if getattr(value, field) not in caps[allowed]:
            raise ProviderApiError("UNSUPPORTED_PARAMETER", f"当前供应商不支持 {field}={getattr(value, field)}", 422)
    if value.generateAudio and not caps["supportsAudio"]:
        raise ProviderApiError("UNSUPPORTED_PARAMETER", "当前供应商不支持原生音频，请关闭音频", 422)
    if len(value.prompt) > caps["maxPromptLength"]:
        raise ProviderApiError("UNSUPPORTED_PARAMETER", f"描述最多 {caps['maxPromptLength']} 个字符", 422)


class PlatformVideoProvider(VolcengineVideoProvider):
    def __init__(self, provider_id, api_key):
        self.provider_id = provider_id
        self.api_key = api_key
        self._tasks = {}
        self._idempotency_index = {}
        self._lock = threading.RLock()

    def estimate(self, value):
        validate_input(self.provider_id, value)
        estimate = super().estimate(value.model_copy(update={"quality": "standard"}))
        return estimate.model_copy(update={"priceVersion": f"{self.provider_id}-local-quota-v1"})

    def get_capabilities(self):
        return {"provider": self.provider_id, **capabilities(self.provider_id)}

    def _request_json(self, method, path, payload=None):
        if not self.api_key:
            raise ProviderNotConfiguredError("API Key 未配置")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Accept": "application/json"}
        if self.provider_id == "runway":
            headers["X-Runway-Version"] = "2024-11-06"
        if self.provider_id == "wan":
            headers["X-DashScope-Async"] = "enable"
        request = urllib.request.Request(SPECS[self.provider_id]["baseUrl"] + path, data=json.dumps(payload).encode() if payload is not None else None, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raise ProviderApiError("PROVIDER_HTTP_ERROR", f"供应商请求失败（HTTP {exc.code}），请检查密钥、区域、权限和余额", 502, exc.code == 429 or exc.code >= 500) from None
        except (urllib.error.URLError, TimeoutError, ValueError):
            raise ProviderApiError("PROVIDER_UNAVAILABLE", "供应商连接或响应异常，请稍后重试", 503, True) from None

    def restore_task(self, task):
        self._tasks[task.id] = task
        self._idempotency_index[task.idempotencyKey] = task.id

    @synchronized
    def create_task(self, value, idempotency_key):
        validate_input(self.provider_id, value)
        if idempotency_key in self._idempotency_index:
            return self._tasks[self._idempotency_index[idempotency_key]]
        if self.provider_id == "wan":
            sizes = {"720p": {"16:9": "1280*720", "9:16": "720*1280", "1:1": "960*960"}, "1080p": {"16:9": "1920*1080", "9:16": "1080*1920", "1:1": "1440*1440"}}
            response = self._request_json("POST", "/services/aigc/video-generation/video-synthesis", {"model": "wan2.6-t2v", "input": {"prompt": value.prompt}, "parameters": {"size": sizes[value.resolution][value.ratio], "duration": value.duration}})
            external = response.get("output", {}).get("task_id")
        elif self.provider_id == "runway":
            response = self._request_json("POST", "/text_to_video", {"model": "gen4.5", "promptText": value.prompt, "ratio": {"16:9": "1280:720", "9:16": "720:1280"}[value.ratio], "duration": value.duration})
            external = response.get("id")
        else:
            response = self._request_json("POST", "/generations/video", {"model": "ray-flash-2" if value.quality == "fast" else "ray-2", "prompt": value.prompt, "aspect_ratio": value.ratio, "resolution": value.resolution, "duration": f"{value.duration}s"})
            external = response.get("id")
        if not external:
            raise ProviderApiError("INVALID_PROVIDER_RESPONSE", "供应商未返回任务 ID")
        task = VideoTask(id=f"{self.provider_id}-{uuid.uuid4().hex}", provider=self.provider_id, externalTaskId=str(external), idempotencyKey=idempotency_key, status=TaskStatus.QUEUED, progress=4, stage="任务已提交到供应商", createdAt=int(time.time()*1000), input=value)
        self.restore_task(task)
        return task

    @synchronized
    def get_task(self, task_id):
        task = self._tasks.get(task_id)
        if task is None or task.status in (TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return task
        path = f"/generations/{task.externalTaskId}" if self.provider_id == "luma" else f"/tasks/{task.externalTaskId}"
        response = self._request_json("GET", path)
        data = response.get("output", {}) if self.provider_id == "wan" else response
        state = str(data.get("task_status", data.get("status", data.get("state", "pending")))).lower()
        mapped = {"succeeded": TaskStatus.SUCCEEDED, "completed": TaskStatus.SUCCEEDED, "failed": TaskStatus.FAILED, "canceled": TaskStatus.CANCELLED, "cancelled": TaskStatus.CANCELLED, "running": TaskStatus.GENERATING, "dreaming": TaskStatus.GENERATING}.get(state, TaskStatus.QUEUED)
        output = data.get("output") or []
        url = data.get("video_url") or (data.get("assets") or {}).get("video") or (output[0] if output else None)
        updated = task.model_copy(update=dict(status=mapped, progress=100 if mapped in (TaskStatus.SUCCEEDED, TaskStatus.FAILED) else 45, stage="视频已经生成" if mapped == TaskStatus.SUCCEEDED else "正在同步视频任务", resultUrl=url, completedAt=int(time.time()*1000) if mapped == TaskStatus.SUCCEEDED else None, errorMessage="供应商生成失败，请检查内容、权限及余额" if mapped == TaskStatus.FAILED else None))
        self._tasks[task_id] = updated
        return updated

    @synchronized
    def cancel_task(self, task_id):
        task = self._tasks.get(task_id)
        if task is None:
            return None
        if task.status in (TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return task
        if not capabilities(self.provider_id)["supportsCancel"]:
            raise ProviderApiError("CANCEL_NOT_SUPPORTED", "该供应商不支持取消，请等待任务完成；已提交任务可能产生费用", 409)
        self._request_json("DELETE", f"/tasks/{task.externalTaskId}")
        updated = task.model_copy(update=dict(status=TaskStatus.CANCELLED, stage="任务已取消", cancelledAt=int(time.time()*1000)))
        self._tasks[task_id] = updated
        return updated
