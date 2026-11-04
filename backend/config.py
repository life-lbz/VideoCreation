"""配置加载：支持 .env 文件热重载。

- 启动时 `load_dotenv()` 加载一次，作为进程级默认值。
- 运行时通过 `settings` 属性访问时，若 .env 文件 mtime 变化则重新加载。
- 其它配置（host/port/database_path）由启动时一次性锁定，不做热重载。
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import dotenv_values, load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 4173
    video_provider: str = "auto"
    ark_api_key: str | None = None
    ark_model_id: str = "doubao-seedance-2-0-260128"
    ark_fast_model_id: str = "doubao-seedance-2-0-fast-260128"
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ark_watermark: bool = True
    database_path: str = "data/frameflow.db"
    provider_request_timeout_ms: int = 30_000

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "4173")),
            video_provider=os.getenv("VIDEO_PROVIDER", "auto"),
            ark_api_key=os.getenv("ARK_API_KEY") or os.getenv("VOLCENGINE_API_KEY"),
            ark_model_id=os.getenv("ARK_MODEL_ID", "doubao-seedance-2-0-260128"),
            ark_fast_model_id=os.getenv(
                "ARK_FAST_MODEL_ID", "doubao-seedance-2-0-fast-260128"
            ),
            ark_base_url=os.getenv(
                "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
            ).rstrip("/"),
            ark_watermark=os.getenv("ARK_WATERMARK", "true").lower()
            not in {"0", "false", "no"},
            database_path=os.getenv("DATABASE_PATH", "data/frameflow.db"),
            provider_request_timeout_ms=int(
                os.getenv("PROVIDER_REQUEST_TIMEOUT_MS", "30000")
            ),
        )


# 启动时锁死固定字段（host/port/db 等）。这些改了就要重启，热重载它们没意义。
load_dotenv()
_BASE = Settings.from_env()

# 热重载跟踪：只跟踪可能运行时改变的字段（ARK_API_KEY、VIDEO_PROVIDER、timeout、model_id 等）
_DOTENV_PATH = os.path.abspath(".env")
_LAST_DOTENV_MTIME: float = 0.0
_LAST_ARK_API_KEY: str | None = _BASE.ark_api_key
_LAST_VIDEO_PROVIDER: str = _BASE.video_provider
_LAST_TIMEOUT: int = _BASE.provider_request_timeout_ms
_LAST_MODEL_ID: str = _BASE.ark_model_id
_LAST_FAST_MODEL_ID: str = _BASE.ark_fast_model_id


class _LiveSettings:
    """代理对象：每次访问 ark_api_key / video_provider 时检查 .env mtime 并按需刷新。"""

    __slots__ = ()

    @staticmethod
    def _maybe_reload() -> None:
        global _LAST_DOTENV_MTIME, _LAST_ARK_API_KEY, _LAST_VIDEO_PROVIDER, _LAST_TIMEOUT, _LAST_MODEL_ID, _LAST_FAST_MODEL_ID
        try:
            mtime = os.path.getmtime(_DOTENV_PATH)
        except OSError:
            return
        if mtime == _LAST_DOTENV_MTIME:
            return
        try:
            # 先更新 mtime，确保下次不会重复 reload（即使下面抛异常）
            _LAST_DOTENV_MTIME = mtime
            load_dotenv(_DOTENV_PATH, override=True)
            _LAST_ARK_API_KEY = os.getenv("ARK_API_KEY") or os.getenv("VOLCENGINE_API_KEY")
            _LAST_VIDEO_PROVIDER = os.getenv("VIDEO_PROVIDER", "auto")
            _LAST_TIMEOUT = int(os.getenv("PROVIDER_REQUEST_TIMEOUT_MS", "30000"))
            _LAST_MODEL_ID = os.getenv("ARK_MODEL_ID", "doubao-seedance-2-0-260128")
            _LAST_FAST_MODEL_ID = os.getenv("ARK_FAST_MODEL_ID", "doubao-seedance-2-0-fast-260128")
        except Exception:  # noqa: BLE001 — 任何刷新失败都降级
            return

    # 固定字段（启动后不再变）直接代理到 _BASE
    @property
    def host(self): return _BASE.host
    @property
    def port(self): return _BASE.port
    @property
    def ark_base_url(self): return _BASE.ark_base_url
    @property
    def ark_watermark(self): return _BASE.ark_watermark
    @property
    def database_path(self): return _BASE.database_path

    # 热重载字段：每次访问先检查 .env mtime
    @property
    def video_provider(self):
        self._maybe_reload
        return _LAST_VIDEO_PROVIDER
    @property
    def ark_api_key(self):
        self._maybe_reload
        return _LAST_ARK_API_KEY
    @property
    def provider_request_timeout_ms(self):
        self._maybe_reload
        return _LAST_TIMEOUT
    @property
    def ark_model_id(self):
        self._maybe_reload
        return _LAST_MODEL_ID
    @property
    def ark_fast_model_id(self):
        self._maybe_reload
        return _LAST_FAST_MODEL_ID

    # 让外部仍能 isinstance(..., Settings) — 不行，它不是 Settings 实例。但所有使用者都是 .field 访问，没问题。


settings = _LiveSettings()
