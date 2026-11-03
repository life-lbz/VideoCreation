from __future__ import annotations

import os
import threading
from functools import wraps
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, SecretStr, Field, ConfigDict
from urllib.parse import urlsplit
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import settings
from backend.models import ErrorDetail, ErrorResponse, GenerationInput
from backend.provider_registry import create_provider
from backend.providers.volcengine import ProviderApiError, ProviderNotConfiguredError
from backend.store import AppStore, InsufficientCreditsError
from backend.video_settings import VideoSettings, ProviderRouter
from backend.providers.platforms import SPECS, PlatformVideoProvider

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"


def select_frontend_dir() -> Path:
    configured = os.environ.get("FRAMEFLOW_FRONTEND_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    build_dir = PUBLIC_DIR.parent / "frontend" / "apps" / "web-antd" / "dist"
    return build_dir if (build_dir / "index.html").is_file() else PUBLIC_DIR


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        normalized = path.replace("\\", "/")
        parts = normalized.split("/")
        if parts[0] == "api" or ".." in parts:
            raise StarletteHTTPException(status_code=404)
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
            # Only client-side routes receive the shell; missing assets stay 404.
            route_path = normalized.rstrip("/")
            if (
                Path(route_path).suffix
                or parts[0] == "static"
                or (parts[0] == "assets" and route_path != "assets")
            ):
                raise
            return await super().get_response("index.html", scope)


video_settings = VideoSettings()
provider = ProviderRouter(create_provider(), video_settings)
store = AppStore(settings.database_path)
for persisted_task in store.list_active_tasks():
    provider.restore_task(persisted_task)

app = FastAPI(
    title="FrameFlow Video Agent API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Serialize configuration changes with the estimate/reserve/submit transaction.
provider_transaction_lock = threading.RLock()


def provider_transaction(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with provider_transaction_lock:
            return function(*args, **kwargs)
    return wrapped


def error_payload(code: str, message: str, retryable: bool = False) -> dict[str, object]:
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, retryable=retryable)
    ).model_dump()


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data: blob: https:; media-src 'self' https: blob:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    prompt_error = any(tuple(error.get("loc", ())) == ("body", "prompt") for error in exc.errors())
    message = "请输入 4 到 1200 个字符的创作描述" if prompt_error else "请求参数不符合要求"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload("INVALID_REQUEST", message),
    )


@app.exception_handler(ProviderNotConfiguredError)
async def provider_config_error_handler(_request: Request, exc: ProviderNotConfiguredError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_payload(exc.code, "视频供应商尚未配置", retryable=False),
    )


@app.exception_handler(ProviderApiError)
async def provider_api_error_handler(_request: Request, exc: ProviderApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, str(exc), retryable=exc.retryable),
    )


@app.exception_handler(InsufficientCreditsError)
async def insufficient_credits_handler(_request: Request, exc: InsufficientCreditsError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content=error_payload("INSUFFICIENT_CREDITS", str(exc), retryable=False),
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        content = exc.detail
    else:
        code = "TASK_NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        content = error_payload(code, str(exc.detail))
    return JSONResponse(status_code=exc.status_code, content=content)


@app.get("/api/health")
def health() -> dict[str, str]:
    provider_name = str(provider.get_capabilities().get("provider", settings.video_provider))
    return {"status": "ok", "provider": provider_name, "runtime": "python"}


@app.get("/api/capabilities")
def capabilities() -> dict[str, object]:
    return provider.get_capabilities()


@app.post("/api/intent/parse")
def parse_intent(generation_input: GenerationInput) -> dict[str, object]:
    return {
        "intent": {
            **generation_input.model_dump(),
            "enhancedPrompt": (
                f"{generation_input.prompt}。画面主体清晰，动作自然，"
                "镜头运动稳定，光影具有层次感。"
            ),
            "inferredFields": ["camera", "lighting"],
        }
    }


@app.post("/api/generations/estimate")
def estimate(generation_input: GenerationInput):
    return provider.estimate(generation_input)


@app.post("/api/generations", status_code=status.HTTP_202_ACCEPTED)
@provider_transaction
def create_generation(
    generation_input: GenerationInput,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, object]:
    if not idempotency_key or len(idempotency_key) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_payload("INVALID_IDEMPOTENCY_KEY", "缺少有效的幂等键"),
        )
    estimate_result = provider.estimate(generation_input)
    existing = store.get_task_by_idempotency(idempotency_key)
    if existing is not None:
        return {"task": existing.model_dump(), "estimate": estimate_result.model_dump()}
    store.reserve(idempotency_key, estimate_result.credits)
    try:
        task = provider.create_task(generation_input, idempotency_key)
        store.save_task(task)
    except Exception:
        store.release(idempotency_key)
        raise
    return {"task": task.model_dump(), "estimate": estimate_result.model_dump()}


@app.get("/api/generations/{task_id}")
def get_generation(task_id: str) -> dict[str, object]:
    task = provider.get_task(task_id)
    if task is None:
        task = store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="没有找到该创作任务")
    store.sync_task(task)
    return {"task": task.model_dump()}


@app.post("/api/generations/{task_id}/cancel")
def cancel_generation(task_id: str) -> dict[str, object]:
    task = provider.cancel_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="没有找到该创作任务")
    store.sync_task(task)
    return {"task": task.model_dump()}


class PlanChangeRequest(BaseModel):
    planId: str


@app.get("/api/account/usage")
def account_usage() -> dict[str, object]:
    return store.get_usage()


@app.get("/api/billing")
def billing() -> dict[str, object]:
    return store.get_billing()


@app.post("/api/billing/plan")
def change_plan(request: PlanChangeRequest) -> dict[str, object]:
    try:
        return store.change_plan(request.planId)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_payload("INVALID_PLAN", str(exc)),
        ) from exc


@app.get("/api/works")
def works() -> dict[str, object]:
    return {"works": store.list_works()}


@app.delete("/api/works/{task_id}")
def delete_work(task_id: str) -> dict[str, bool]:
    if not store.delete_work(task_id):
        raise HTTPException(status_code=404, detail="没有找到该作品")
    return {"deleted": True}


class ProviderKeyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    apiKey: SecretStr = Field(min_length=1, max_length=4096)


def settings_write_guard(request: Request):
    hostname = urlsplit(str(request.url)).hostname
    if hostname not in {"localhost", "127.0.0.1", "::1", "testserver"} or (request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}):
        raise HTTPException(403, "配置仅允许本机访问")
    origin = request.headers.get("origin")
    if origin and origin != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "配置请求必须来自同一来源")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "禁止跨站配置请求")
    if request.method == "PUT" and request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise HTTPException(415, "请使用 JSON 请求")


def require_provider(identity):
    if identity not in SPECS:
        raise HTTPException(404, "未知视频供应商")


@app.get("/api/video-providers")
def video_providers():
    fallback = provider.active_id() if isinstance(provider, ProviderRouter) else "mock"
    return video_settings.listing(fallback)


@app.put("/api/video-providers/{identity}")
@provider_transaction
def save_video_provider(identity: str, body: ProviderKeyRequest, request: Request):
    settings_write_guard(request)
    require_provider(identity)
    key = body.apiKey.get_secret_value().strip()
    if not key or any(ord(char) < 33 or ord(char) > 126 for char in key):
        raise HTTPException(422, "API Key 必须为非空可打印 ASCII 字符")
    if any(task.provider == identity for task in store.list_active_tasks()):
        raise HTTPException(409, "该供应商仍有进行中的任务，请完成后再更换密钥")
    video_settings.set_key(identity, key)
    if isinstance(provider, ProviderRouter):
        provider.instances.pop(identity, None)
    return video_providers()


@app.post("/api/video-providers/{identity}/activate")
@provider_transaction
def activate_video_provider(identity: str, request: Request):
    settings_write_guard(request)
    require_provider(identity)
    if not video_settings.key(identity):
        raise HTTPException(409, "请先保存 API Key")
    with video_settings.lock:
        video_settings.data["activeProvider"] = identity
        video_settings.save()
    return video_providers()


@app.delete("/api/video-providers/{identity}")
@provider_transaction
def remove_video_provider(identity: str, request: Request):
    settings_write_guard(request)
    require_provider(identity)
    if video_settings.data.get("activeProvider") == identity or any(task.provider == identity for task in store.list_active_tasks()):
        raise HTTPException(409, "请先切换供应商并等待该供应商任务完成，再删除密钥")
    with video_settings.lock:
        video_settings.data["keys"].pop(identity, None)
        video_settings.save()
    if isinstance(provider, ProviderRouter):
        provider.instances.pop(identity, None)
    return video_providers()


@app.post("/api/video-providers/{identity}/test")
def test_video_provider(identity: str, request: Request):
    settings_write_guard(request)
    require_provider(identity)
    key = video_settings.key(identity)
    if not key:
        return {"ok": False, "message": "请先保存 API Key"}
    try:
        if identity == "volcengine":
            from backend.providers.volcengine import VolcengineConfig, VolcengineVideoProvider
            adapter = VolcengineVideoProvider(VolcengineConfig(key, settings.ark_model_id, settings.ark_fast_model_id, SPECS[identity]["baseUrl"]))
            adapter._request_json("GET", "/models")
        else:
            adapter = PlatformVideoProvider(identity, key)
            adapter._request_json("GET", {"wan": "/models", "runway": "/organization", "luma": "/generations?limit=1"}[identity])
        return {"ok": True, "message": "只读连接验证成功；生成权限与余额请以供应商控制台为准"}
    except (ProviderApiError, ProviderNotConfiguredError):
        return {"ok": False, "message": "连接验证失败，请检查密钥、区域、权限与网络"}


app.mount("/", SPAStaticFiles(directory=select_frontend_dir()), name="frontend")
