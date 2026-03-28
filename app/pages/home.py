"""
Home page — the art studio input forms only.
Route: /

Two tabs:
  Tab 1: Generate Art — text prompt → Mughal miniature
  Tab 2: Transform Photo — upload image → Mughal version

After generation/transform, user is redirected to /gallery to view their artwork.
"""

from __future__ import annotations

import uuid
import logging

from nicegui import ui, app
from app.components.navbar import navbar
from app.components.style_panel import style_panel
from app.components.upload_panel import UploadPanel
from app.ai.prompt_enhancer import enhance_prompt
from app.ai.image_generator import generate_image
from app.ai.image_transformer import transform_image
from app.services.gallery_service import upload_image, save_gallery_item

logger = logging.getLogger(__name__)


def _require_auth() -> bool:
    if not app.storage.user.get("user_id"):
        ui.navigate.to("/login")
        return True
    return False


@ui.page("/")
async def home_page() -> None:
    if _require_auth():
        return

    ui.add_head_html('<link rel="stylesheet" href="/static/mughal.css">')
    ui.add_head_html('<link rel="preconnect" href="https://fonts.googleapis.com">')
    ui.add_head_html(
        '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Crimson+Text:ital@0;1&family=IM+Fell+English:ital@0;1&display=swap" rel="stylesheet">'
    )

    navbar()

    with ui.column().classes("ei-page-container"):

        with ui.column().classes("ei-page-header items-center gap-1"):
            ui.label("The Royal Art Studio").classes("ei-page-title")
            ui.label("Type a thought. Watch Mughal history come alive.").classes("ei-page-subtitle")

        with ui.tabs().classes("ei-tabs w-full") as tabs:
            gen_tab = ui.tab("generate", label="✦  Generate Art")
            trans_tab = ui.tab("transform", label="⟳  Transform Photo")

        with ui.tab_panels(tabs, value=gen_tab).classes("w-full"):
            with ui.tab_panel(gen_tab):
                await _render_generate_tab()
            with ui.tab_panel(trans_tab):
                await _render_transform_tab()


async def _render_generate_tab() -> None:
    with ui.column().classes("w-full max-w-2xl mx-auto gap-4 py-4"):
        with ui.card().classes("ei-controls-card w-full"):
            ui.label("Describe Your Vision").classes("ei-section-label")

            prompt_input = ui.textarea(
                label="Your creative prompt",
                placeholder='e.g. "A cricket match at sunset in a Mughal garden" or "Taj Mahal at dawn"',
            ).classes("w-full ei-textarea").props("rows=4 autogrow")

            style_select = style_panel("akbari")

            with ui.expansion("Enhanced Prompt Preview", icon="auto_awesome").classes(
                "w-full ei-expansion mt-2"
            ):
                enhanced_label = ui.label("Generate an image to see the AI-enhanced prompt.").classes(
                    "text-xs opacity-60 italic"
                )

            status_label = ui.label("").classes("text-amber-400 text-sm min-h-[1rem]")
            error_label = ui.label("").classes("text-red-400 text-sm min-h-[1rem]")

            async def generate():
                error_label.text = ""
                status_label.text = ""
                prompt = prompt_input.value.strip()
                if not prompt:
                    error_label.text = "Please enter a prompt first."
                    return

                user_id = app.storage.user.get("user_id", "")
                gen_btn.props("loading")

                try:
                    status_label.text = "✦ Enhancing your prompt…"
                    enhanced = await enhance_prompt(prompt, style_select.value)
                    enhanced_label.text = enhanced

                    status_label.text = "✦ Generating Mughal art…"
                    image_bytes, model_used = await generate_image(enhanced)

                    status_label.text = "✦ Saving to your gallery…"
                    filename = f"{uuid.uuid4()}.png"
                    image_url = upload_image(image_bytes, user_id, filename)
                    save_gallery_item(
                        user_id=user_id,
                        prompt=prompt,
                        image_url=image_url,
                        enhanced_prompt=enhanced,
                        style_preset=style_select.value,
                        model_used=model_used,
                        source_type="generate",
                    )

                    status_label.text = ""
                    ui.notify("Artwork created! Opening your gallery…", type="positive")
                    ui.navigate.to("/gallery")
                except Exception as e:
                    logger.error(f"Generate failed: {e}")
                    error_label.text = f"Error: {str(e)}"
                    status_label.text = ""
                finally:
                    gen_btn.props(remove="loading")

            gen_btn = ui.button(
                "✦ Generate Mughal Art", on_click=generate
            ).classes("w-full ei-btn-primary mt-2")

            ui.separator().classes("opacity-20 my-2")
            with ui.row().classes("items-center gap-2 text-xs opacity-50"):
                ui.icon("info_outline").classes("text-sm")
                ui.label("Powered by Google Imagen 4 · Results saved to Your Artworks")


async def _render_transform_tab() -> None:
    upload_panel = UploadPanel()

    with ui.column().classes("w-full max-w-2xl mx-auto gap-4 py-4"):
        with ui.card().classes("ei-controls-card w-full"):
            ui.label("Upload & Transform").classes("ei-section-label")
            ui.label(
                "Upload any photo — portrait, landscape, scene — and watch it become Mughal art."
            ).classes("text-sm opacity-60 mb-3")

            upload_panel.render()

            ui.separator().classes("opacity-20 my-3")

            style_select = style_panel("akbari")

            status_label = ui.label("").classes("text-amber-400 text-sm min-h-[1rem]")
            error_label = ui.label("").classes("text-red-400 text-sm min-h-[1rem]")

            async def transform():
                error_label.text = ""
                status_label.text = ""
                if not upload_panel.has_image:
                    error_label.text = "Please upload an image first."
                    return

                user_id = app.storage.user.get("user_id", "")
                transform_btn.props("loading")

                try:
                    status_label.text = "⟳ Applying Mughal style…"
                    transformed_bytes, model_used = await transform_image(
                        upload_panel.image_bytes, style_select.value
                    )

                    status_label.text = "✦ Saving to your gallery…"
                    filename = f"{uuid.uuid4()}.png"
                    image_url = upload_image(transformed_bytes, user_id, filename)
                    prompt_label = f"[Transform] {upload_panel.filename} → {style_select.value} style"
                    save_gallery_item(
                        user_id=user_id,
                        prompt=prompt_label,
                        image_url=image_url,
                        enhanced_prompt=None,
                        style_preset=style_select.value,
                        model_used=model_used,
                        source_type="transform",
                    )

                    status_label.text = ""
                    ui.notify("Transformation complete! Opening your gallery…", type="positive")
                    ui.navigate.to("/gallery")
                except Exception as e:
                    logger.error(f"Transform failed: {e}")
                    error_label.text = f"Error: {str(e)}"
                    status_label.text = ""
                finally:
                    transform_btn.props(remove="loading")

            transform_btn = ui.button(
                "⟳ Apply Mughal Style", on_click=transform
            ).classes("w-full ei-btn-primary mt-2")

            ui.separator().classes("opacity-20 my-2")
            with ui.row().classes("items-center gap-2 text-xs opacity-50"):
                ui.icon("info_outline").classes("text-sm")
                ui.label("Powered by Gemini Flash · Max 10MB · JPEG/PNG/WEBP")
