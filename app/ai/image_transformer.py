"""
Transforms an uploaded photo into a Mughal miniature painting style.
Uses Gemini 2.0 Flash multimodal (image + text → image).
"""

import logging
from google import genai
from google.genai import types
from app.config import settings
from app.ai.prompt_enhancer import STYLE_DESCRIPTORS, NEGATIVE_PROMPT

logger = logging.getLogger(__name__)
_client = genai.Client(api_key=settings.gemini_api_key)

TRANSFORM_MODEL = "gemini-2.5-flash-image"

TRANSFORM_INSTRUCTION = (
    "Transform this photograph into a Mughal miniature painting. "
    "Preserve the core subject, composition, and key figures from the original image. "
    "Apply the following art style: {style_desc}. "
    "The result must look like an authentic historical Mughal painting. "
    "Negative style elements to avoid: {negative}."
)


async def transform_image(image_bytes: bytes, style_preset: str = "akbari") -> tuple[bytes, str]:
    """
    Transforms an uploaded image into a Mughal miniature painting using Gemini Flash.

    Args:
        image_bytes: Raw bytes of the uploaded image (JPEG/PNG).
        style_preset: One of 'akbari', 'jahangiri', 'shahjahani'.

    Returns:
        Tuple of (transformed_image_bytes: bytes, model_used: str)
    """
    preset = style_preset.lower() if style_preset.lower() in STYLE_DESCRIPTORS else "akbari"
    style_desc = STYLE_DESCRIPTORS[preset]

    instruction = TRANSFORM_INSTRUCTION.format(
        style_desc=style_desc,
        negative=NEGATIVE_PROMPT,
    )

    # Detect MIME type (default to JPEG)
    mime_type = "image/jpeg"
    if image_bytes[:4] == b"\x89PNG":
        mime_type = "image/png"
    elif image_bytes[:6] in (b"GIF87a", b"GIF89a"):
        mime_type = "image/gif"
    elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        mime_type = "image/webp"

    try:
        response = await _client.aio.models.generate_content(
            model=TRANSFORM_MODEL,
            contents=[
                types.Part(
                    inline_data=types.Blob(mime_type=mime_type, data=image_bytes)
                ),
                types.Part(text=instruction),
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                result_bytes = part.inline_data.data  # SDK returns raw bytes, no decode needed
                logger.info(f"Image transformed with Gemini Flash ({preset} style).")
                return result_bytes, "gemini-flash"

        raise ValueError("Gemini Flash returned no image data in transform response.")

    except Exception as e:
        logger.error(f"Image transformation failed: {e}")
        raise RuntimeError(f"Image transformation failed: {e}") from e
