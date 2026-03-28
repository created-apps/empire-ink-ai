"""
Orchestrates the full AI pipeline for both generation and transformation flows.

Generate pipeline:
  raw prompt → enhance (Gemini Flash text) → generate image (Imagen 3 / Flash)
  → upload to Storage → save to DB

Transform pipeline:
  uploaded image bytes → transform (Gemini Flash multimodal)
  → upload to Storage → save to DB
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from app.ai.prompt_enhancer import enhance_prompt
from app.ai.image_generator import generate_image
from app.ai.image_transformer import transform_image
from app.services.gallery_service import upload_image, save_gallery_item

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    success: bool
    image_url: str | None = None
    enhanced_prompt: str | None = None
    model_used: str | None = None
    gallery_item: dict | None = None
    error: str | None = None


async def run_generate_pipeline(
    raw_prompt: str,
    style_preset: str,
    user_id: str,
) -> GenerationResult:
    """
    Full text-to-image pipeline.

    Args:
        raw_prompt: User's plain text idea.
        style_preset: 'akbari', 'jahangiri', or 'shahjahani'.
        user_id: Authenticated user's UUID.

    Returns:
        GenerationResult with image_url and gallery metadata.
    """
    try:
        # Step 1: Enhance prompt
        logger.info(f"Enhancing prompt for user {user_id}: '{raw_prompt[:60]}...'")
        enhanced = await enhance_prompt(raw_prompt, style_preset)

        # Step 2: Generate image
        logger.info("Generating image...")
        image_bytes, model_used = await generate_image(enhanced)

        # Step 3: Upload to Supabase Storage
        filename = f"{uuid.uuid4()}.png"
        image_url = upload_image(image_bytes, user_id, filename)

        # Step 4: Save to DB
        gallery_item = save_gallery_item(
            user_id=user_id,
            prompt=raw_prompt,
            image_url=image_url,
            enhanced_prompt=enhanced,
            style_preset=style_preset,
            model_used=model_used,
            source_type="generate",
        )

        logger.info(f"Generation complete: {image_url}")
        return GenerationResult(
            success=True,
            image_url=image_url,
            enhanced_prompt=enhanced,
            model_used=model_used,
            gallery_item=gallery_item,
        )

    except Exception as e:
        logger.error(f"Generation pipeline failed: {e}")
        return GenerationResult(success=False, error=str(e))


async def run_transform_pipeline(
    image_bytes: bytes,
    style_preset: str,
    user_id: str,
    original_filename: str = "upload",
    parent_id: str | None = None,
) -> GenerationResult:
    """
    Full image-to-Mughal-image pipeline.

    Args:
        image_bytes: Raw bytes of the user's uploaded photo.
        style_preset: 'akbari', 'jahangiri', or 'shahjahani'.
        user_id: Authenticated user's UUID.
        original_filename: Original uploaded filename (for context/logging).

    Returns:
        GenerationResult with image_url and gallery metadata.
    """
    try:
        # Step 1: Transform image
        logger.info(f"Transforming image '{original_filename}' for user {user_id} ({style_preset} style).")
        transformed_bytes, model_used = await transform_image(image_bytes, style_preset)

        # Step 2: Upload to Supabase Storage
        filename = f"{uuid.uuid4()}.png"
        image_url = upload_image(transformed_bytes, user_id, filename)

        # Step 3: Save to DB
        prompt_label = f"[Transform] {original_filename} → {style_preset} style"
        gallery_item = save_gallery_item(
            user_id=user_id,
            prompt=prompt_label,
            image_url=image_url,
            enhanced_prompt=None,
            style_preset=style_preset,
            model_used=model_used,
            source_type="transform",
            parent_id=parent_id,
        )

        logger.info(f"Transform complete: {image_url}")
        return GenerationResult(
            success=True,
            image_url=image_url,
            model_used=model_used,
            gallery_item=gallery_item,
        )

    except Exception as e:
        logger.error(f"Transform pipeline failed: {e}")
        return GenerationResult(success=False, error=str(e))
