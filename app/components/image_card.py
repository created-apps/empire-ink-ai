"""
Reusable gallery image card.
Shows the artwork, prompt text, style badge, source badge (Generated/Transformed),
and Download + Delete action buttons.
"""

from __future__ import annotations

from typing import Optional
from nicegui import ui


def image_card(item: dict, on_delete: Optional[callable] = None) -> None:
    """
    Renders a single gallery card.

    Args:
        item: Gallery item dict (id, prompt, image_url, style_preset, source_type, model_used, created_at).
        on_delete: Async callable(item_id) called after delete confirmation.
    """
    source_type = item.get("source_type", "generate")
    style_preset = item.get("style_preset", "akbari").capitalize()
    model_used = item.get("model_used", "")
    prompt_text = item.get("prompt", "")
    image_url = item.get("image_url", "")
    item_id = item.get("id", "")

    # Truncate long prompts for display
    display_prompt = prompt_text[:80] + "..." if len(prompt_text) > 80 else prompt_text

    with ui.card().classes("ei-gallery-card"):

        # Image
        ui.image(image_url).classes("w-full rounded-t-lg object-cover").style("aspect-ratio: 1/1;")

        with ui.column().classes("p-3 gap-2"):

            # Badges row
            with ui.row().classes("gap-2 flex-wrap"):
                badge_color = "amber" if source_type == "generate" else "teal"
                badge_label = "✦ Generated" if source_type == "generate" else "⟳ Transformed"
                ui.badge(badge_label, color=badge_color).classes("text-xs")
                ui.badge(style_preset, color="deep-orange").classes("text-xs")
                if model_used:
                    ui.badge(model_used, color="grey").classes("text-xs opacity-70")

            # Prompt
            ui.label(display_prompt).classes("text-sm ei-prompt-text").props('title="' + prompt_text.replace('"', "'") + '"')

            # Actions
            with ui.row().classes("gap-2 mt-1"):

                # Download button — opens image in new tab
                ui.button(
                    icon="download",
                    on_click=lambda url=image_url: ui.navigate.to(url, new_tab=True),
                ).props("flat dense").classes("ei-icon-btn").tooltip("Download image")

                # Delete button — shows confirmation dialog
                async def handle_delete(iid=item_id):
                    with ui.dialog() as confirm_dialog, ui.card().classes("p-6 gap-4"):
                        ui.label("Delete this artwork?").classes("font-semibold text-lg")
                        ui.label("This action cannot be undone.").classes("text-sm opacity-70")
                        with ui.row().classes("gap-3 justify-end w-full"):
                            ui.button("Cancel", on_click=confirm_dialog.close).classes("ei-btn-outline")

                            async def confirmed_delete(d=confirm_dialog):
                                d.close()
                                if on_delete:
                                    await on_delete(iid)

                            ui.button("Delete", on_click=confirmed_delete).classes("ei-btn-danger")
                    confirm_dialog.open()

                ui.button(
                    icon="delete_outline",
                    on_click=handle_delete,
                ).props("flat dense").classes("ei-icon-btn text-red-400").tooltip("Delete artwork")
