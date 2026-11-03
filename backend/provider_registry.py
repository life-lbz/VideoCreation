from __future__ import annotations

from backend.config import Settings, settings
from backend.providers.base import VideoProvider
from backend.providers.mock import MockVideoProvider
from backend.providers.volcengine import VolcengineConfig, VolcengineVideoProvider


def create_provider(config: Settings = settings) -> VideoProvider:
    selected = config.video_provider
    if selected == "auto":
        selected = "volcengine" if config.ark_api_key else "mock"

    if selected == "mock":
        return MockVideoProvider()
    if selected == "volcengine":
        return VolcengineVideoProvider(
            VolcengineConfig(
                api_key=config.ark_api_key,
                model_id=config.ark_model_id,
                fast_model_id=config.ark_fast_model_id,
                base_url=config.ark_base_url,
                watermark=config.ark_watermark,
            )
        )
    raise ValueError(f"Unsupported VIDEO_PROVIDER: {selected}")
