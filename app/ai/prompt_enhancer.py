"""
Uses Gemini 2.0 Flash (text) to transform a user's raw prompt into a rich
Mughal miniature art prompt with era-specific style descriptors.
"""

from google import genai
from google.genai import types
from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

STYLE_DESCRIPTORS: dict[str, str] = {
    "akbari": (
        "Akbari school Mughal miniature painting style (1556-1605), "
        "bold outlines, Persian and Indian fusion, rich jewel tones of crimson and cobalt, "
        "flat perspective, busy multi-figure compositions, gold leaf accents, "
        "intricate architectural details, deep green foliage, ornate floral borders"
    ),
    "jahangiri": (
        "Jahangiri school Mughal miniature painting style (1605-1627), "
        "naturalistic fine detail, delicate botanical accuracy, soft pastel palette, "
        "warm gold leaf borders, European portrait influence, fine brushwork, "
        "single-figure or intimate compositions, realistic animal and bird detail, "
        "ivory and rose tones, translucent washes"
    ),
    "shahjahani": (
        "Shahjahani school Mughal miniature painting style (1628-1658), "
        "white marble aesthetic, refined symmetrical compositions, "
        "opulent floral border patterns, muted jewel tones with ivory dominance, "
        "elegant calligraphic borders, architectural grandeur, "
        "cool blue and white palette with gold filigree, restrained sophistication"
    ),
}

NEGATIVE_PROMPT = (
    "photorealistic, modern photography, 3D render, CGI, anime, cartoon, "
    "western art style, abstract, blurry, low quality, watermark, signature"
)

SYSTEM_INSTRUCTION = """You are an expert prompt engineer specialising in Mughal miniature art.
Your task is to take a user's simple idea and rewrite it as a detailed, evocative image generation prompt.

Rules:
- Keep the core subject/idea from the user's prompt
- Add rich visual detail: lighting, composition, colour palette, textures, setting
- Do NOT add the style keywords yet — those will be appended separately
- Output ONLY the enhanced prompt text, nothing else, no explanation, no preamble
- Maximum 120 words
- Write in present tense, descriptive style"""


async def enhance_prompt(raw_prompt: str, style_preset: str = "akbari") -> str:
    """
    Enhances a raw user prompt using Gemini Flash and appends Mughal style descriptors.

    Args:
        raw_prompt: The user's plain-text idea.
        style_preset: One of 'akbari', 'jahangiri', 'shahjahani'.

    Returns:
        A fully enriched prompt string ready for image generation.
    """
    preset = style_preset.lower() if style_preset.lower() in STYLE_DESCRIPTORS else "akbari"
    style_desc = STYLE_DESCRIPTORS[preset]

    response = await _client.aio.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
            max_output_tokens=200,
        ),
        contents=f"User idea: {raw_prompt}",
    )

    enhanced_core = response.text.strip()
    full_prompt = f"{enhanced_core}, {style_desc}, negative: {NEGATIVE_PROMPT}"
    return full_prompt
