"""
Generates Mughal miniature art images from a text prompt.
Primary: Imagen 3 (imagen-3.0-generate-002)
Fallback: Gemini 2.0 Flash image generation (gemini-2.0-flash-preview-image-generation)
"""

import logging
from google import genai
from google.genai import types
from app.config import settings

logger = logging.getLogger(__name__)
_client = genai.Client(api_key=settings.gemini_api_key)

IMAGEN_MODEL = "imagen-4.0-generate-001"
FLASH_IMAGE_MODEL = "gemini-2.5-flash-image"


async def generate_image(prompt: str) -> tuple[bytes, str]:
    """
    Generates an image from a text prompt.
    Tries Imagen 3 first; falls back to Gemini Flash on quota or API errors.

    Args:
        prompt: The fully enhanced Mughal art prompt.

    Returns:
        Tuple of (image_bytes: bytes, model_used: str)
    """
    # ── Primary: Imagen 3 ──────────────────────────────────────────────────────
    try:
        response = await _client.aio.models.generate_images(
            model=IMAGEN_MODEL,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="BLOCK_LOW_AND_ABOVE",
                person_generation="allow_adult",
            ),
        )
        image_bytes = response.generated_images[0].image.image_bytes
        logger.info("Image generated with Imagen 4.")
        return image_bytes, "imagen-4"

    except Exception as e:
        logger.warning(f"Imagen 4 failed ({e}), falling back to Gemini Flash.")

    # ── Fallback: Gemini Flash image generation ────────────────────────────────
    try:
        response = await _client.aio.models.generate_content(
            model=FLASH_IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_bytes = part.inline_data.data  # SDK returns raw bytes, no decode needed
                logger.info("Image generated with Gemini Flash fallback.")
                return image_bytes, "gemini-flash"

        raise ValueError("Gemini Flash returned no image data.")

    except Exception as e:
        logger.error(f"Both image generation models failed: {e}")
        raise RuntimeError(f"Image generation failed: {e}") from e
