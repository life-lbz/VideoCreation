from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


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
        )


settings = Settings.from_env()
