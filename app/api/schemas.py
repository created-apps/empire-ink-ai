from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


# ── Auth Request Models ────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str


# ── Request Models ─────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500, description="Raw user prompt/idea")
    style_preset: Literal["akbari", "jahangiri", "shahjahani"] = Field(
        default="akbari", description="Mughal art school style preset"
    )


# ── Response Models ────────────────────────────────────────────────────────────

class GenerateResponse(BaseModel):
    success: bool
    image_url: str | None = None
    enhanced_prompt: str | None = None
    model_used: str | None = None
    gallery_id: str | None = None
    error: str | None = None


class TransformResponse(BaseModel):
    success: bool
    image_url: str | None = None
    model_used: str | None = None
    gallery_id: str | None = None
    error: str | None = None


class GalleryItem(BaseModel):
    id: str
    user_id: str
    prompt: str
    enhanced_prompt: str | None = None
    image_url: str
    style_preset: str
    model_used: str | None = None
    source_type: Literal["generate", "transform"] = "generate"
    created_at: datetime


class GalleryResponse(BaseModel):
    items: list[GalleryItem]
    total: int


class DeleteResponse(BaseModel):
    success: bool
    message: str
