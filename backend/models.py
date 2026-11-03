from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TaskStatus(StrEnum):
    QUEUED = "queued"
    GENERATING = "generating"
    POST_PROCESSING = "post_processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationInput(BaseModel):
    prompt: str = Field(min_length=4, max_length=1200)
    ratio: Literal["9:16", "16:9", "1:1"] = "9:16"
    duration: Literal[5, 8, 10, 15] = 5
    quality: Literal["fast", "standard", "pro"] = "fast"
    resolution: Literal["480p", "720p", "1080p"] = "720p"
    generateAudio: bool = False
    quantity: Literal[1] = 1

    @field_validator("prompt")
    @classmethod
    def normalize_prompt(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 4:
            raise ValueError("请输入 4 到 1200 个字符的创作描述")
        return value


class CostEstimate(BaseModel):
    credits: int
    currency: str = "credits"
    estimatedSeconds: int
    priceVersion: str


class VideoTask(BaseModel):
    id: str
    provider: str = "volcengine"
    externalTaskId: str = Field(exclude=True)
    idempotencyKey: str = Field(exclude=True)
    status: TaskStatus
    progress: int = Field(ge=0, le=100)
    stage: str
    createdAt: int
    completedAt: int | None = None
    cancelledAt: int | None = None
    resultUrl: str | None = None
    errorCode: str | None = None
    errorMessage: str | None = None
    actionUrl: str | None = None
    input: GenerationInput


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool = False


class ErrorResponse(BaseModel):
    error: ErrorDetail
