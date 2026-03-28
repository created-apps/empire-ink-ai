"""
FastAPI routes for the Empire & Ink API.

Endpoints:
  POST /api/auth/login        — Sign in, returns JWT
  POST /api/auth/register     — Sign up, returns JWT (or needs_confirmation flag)
  POST /api/auth/logout       — Invalidate session
  POST /api/generate          — Text prompt → Mughal miniature image
  POST /api/transform         — Uploaded photo → Mughal miniature image
  GET  /api/gallery           — Fetch current user's gallery
  DELETE /api/gallery/{id}    — Delete a gallery item
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

from app.api.schemas import (
    LoginRequest, RegisterRequest,
    GenerateRequest, GenerateResponse,
    TransformResponse, GalleryResponse, GalleryItem, DeleteResponse,
)
from app.services.generation_service import run_generate_pipeline, run_transform_pipeline
from app.services.gallery_service import get_user_gallery, delete_gallery_item
from app.services.auth_service import sign_in, sign_up, sign_out
from app.database import get_anon_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Empire & Ink API"])
bearer_scheme = HTTPBearer()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ── Auth dependency ────────────────────────────────────────────────────────────

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Validates the Bearer token via Supabase and returns the user dict."""
    token = credentials.credentials
    try:
        client = get_anon_client()
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        return {"user_id": str(user_response.user.id), "token": token}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth validation error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed.")


# ── POST /api/auth/login ──────────────────────────────────────────────────────

@router.post("/auth/login")
async def login(body: LoginRequest):
    """Signs in a user and returns JWT access token."""
    result = sign_in(body.email, body.password)
    if not result.success:
        raise HTTPException(status_code=401, detail=result.error or "Invalid credentials.")
    return {
        "access_token": result.access_token,
        "user_id": result.user_id,
        "email": result.email,
    }


# ── POST /api/auth/register ────────────────────────────────────────────────────

@router.post("/auth/register")
async def register(body: RegisterRequest):
    """Registers a new user. Returns JWT if auto-confirmed, else needs_confirmation flag."""
    result = sign_up(body.email, body.password)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Registration failed.")
    return {
        "access_token": result.access_token,
        "user_id": result.user_id,
        "email": result.email,
        "needs_confirmation": result.access_token is None,
    }


# ── POST /api/auth/logout ──────────────────────────────────────────────────────

@router.post("/auth/logout")
async def logout_route(user: dict = Depends(get_current_user)):
    """Invalidates the user's current session."""
    sign_out(user["token"])
    return {"success": True}


# ── POST /api/generate ─────────────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
async def generate_art(
    request: GenerateRequest,
    user: dict = Depends(get_current_user),
) -> GenerateResponse:
    """
    Accepts a text prompt and style preset, returns a URL to a generated Mughal miniature image.
    Uses Imagen 3 with Gemini Flash fallback.
    """
    result = await run_generate_pipeline(
        raw_prompt=request.prompt,
        style_preset=request.style_preset,
        user_id=user["user_id"],
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Image generation failed.")

    return GenerateResponse(
        success=True,
        image_url=result.image_url,
        enhanced_prompt=result.enhanced_prompt,
        model_used=result.model_used,
        gallery_id=result.gallery_item.get("id") if result.gallery_item else None,
    )


# ── POST /api/transform ────────────────────────────────────────────────────────

@router.post("/transform", response_model=TransformResponse)
async def transform_photo(
    file: UploadFile = File(..., description="Image file to transform (JPEG/PNG/WEBP, max 10MB)"),
    style_preset: str = Form(default="akbari", description="Mughal style preset"),
    user: dict = Depends(get_current_user),
) -> TransformResponse:
    """
    Accepts an uploaded photo and a style preset.
    Returns a URL to the Mughal-styled version of the image.
    """
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: JPEG, PNG, WEBP, GIF.",
        )

    # Validate preset
    valid_presets = {"akbari", "jahangiri", "shahjahani"}
    if style_preset.lower() not in valid_presets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid style preset '{style_preset}'. Choose from: {', '.join(valid_presets)}.",
        )

    # Read and validate file size
    image_bytes = await file.read()
    if len(image_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = await run_transform_pipeline(
        image_bytes=image_bytes,
        style_preset=style_preset.lower(),
        user_id=user["user_id"],
        original_filename=file.filename or "upload",
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Image transformation failed.")

    return TransformResponse(
        success=True,
        image_url=result.image_url,
        model_used=result.model_used,
        gallery_id=result.gallery_item.get("id") if result.gallery_item else None,
    )


# ── GET /api/gallery ───────────────────────────────────────────────────────────

@router.get("/gallery", response_model=GalleryResponse)
def get_gallery(user: dict = Depends(get_current_user)) -> GalleryResponse:
    """Returns all gallery items for the authenticated user, newest first."""
    items = get_user_gallery(user_id=user["user_id"])
    return GalleryResponse(
        items=[GalleryItem(**item) for item in items],
        total=len(items),
    )


# ── DELETE /api/gallery/{id} ───────────────────────────────────────────────────

@router.delete("/gallery/{item_id}", response_model=DeleteResponse)
def delete_item(item_id: str, user: dict = Depends(get_current_user)) -> DeleteResponse:
    """Deletes a gallery item (DB record + Storage file). Validates ownership."""
    deleted = delete_gallery_item(item_id=item_id, user_id=user["user_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found or access denied.")
    return DeleteResponse(success=True, message="Item deleted successfully.")
