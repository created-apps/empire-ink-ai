"""
Gallery page — "Your Artworks"
Route: /gallery

Features:
- Skeleton loading animation while fetching from Supabase
- Filter: All / Generated / Transformed
- Per-card: Download, Re-Transform (style picker dialog), Delete with confirmation
- Empty state with CTA
- "Create New" button to return to studio
"""

from __future__ import annotations

import httpx
from nicegui import ui, app
from app.components.navbar import navbar
from app.components.style_panel import style_panel
from app.services.gallery_service import get_user_gallery, delete_gallery_item
from app.services.generation_service import run_transform_pipeline


def _require_auth() -> bool:
    if not app.storage.user.get("user_id"):
        ui.navigate.to("/login")
        return True
    return False


@ui.page("/gallery")
async def gallery_page() -> None:
    if _require_auth():
        return

    ui.add_head_html('<link rel="stylesheet" href="/static/mughal.css">')
    ui.add_head_html(
        '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Crimson+Text:ital@0;1&family=IM+Fell+English:ital@0;1&display=swap" rel="stylesheet">'
    )

    navbar()

    user_id = app.storage.user.get("user_id", "")
    state = {"filter": "all"}
    filter_btns: list[tuple] = []

    with ui.column().classes("ei-page-container gap-6"):

        # ── Header ─────────────────────────────────────────────────────────────
        with ui.row().classes("w-full items-center justify-between flex-wrap gap-3"):
            with ui.column().classes("gap-0"):
                ui.label("Your Artworks").classes("ei-page-title")
                ui.label("Your Mughal masterpieces, all in one place").classes("ei-page-subtitle")
            ui.button(
                "✦ Create New", on_click=lambda: ui.navigate.to("/")
            ).classes("ei-btn-primary")

        # ── Filter row ─────────────────────────────────────────────────────────
        with ui.row().classes("gap-2 items-center"):
            ui.label("Show:").classes("text-sm opacity-50 mr-1")
            for label, key in [("All", "all"), ("Generated", "generate"), ("Transformed", "transform")]:
                btn = ui.button(
                    label, on_click=lambda k=key: _apply_filter(k)
                ).props("flat").classes(
                    "ei-filter-btn" + (" ei-filter-active" if key == "all" else "")
                )
                filter_btns.append((btn, key))

        # ── Content container ──────────────────────────────────────────────────
        content = ui.column().classes("w-full")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _apply_filter(value: str) -> None:
        state["filter"] = value
        for btn, key in filter_btns:
            if key == value:
                btn.classes(add="ei-filter-active")
            else:
                btn.classes(remove="ei-filter-active")
        ui.timer(0.01, _refresh, once=True)

    async def _refresh() -> None:
        await _render_content(content, user_id, state, _on_delete, _on_retransform)

    async def _on_delete(item_id: str) -> None:
        if delete_gallery_item(item_id, user_id):
            ui.notify("Artwork deleted.", type="warning")
        else:
            ui.notify("Delete failed.", type="negative")
        await _refresh()

    async def _on_retransform(item: dict) -> None:
        await _retransform_dialog(item, user_id, _refresh)

    # ── Initial render ──────────────────────────────────────────────────────────
    await _refresh()


# ── Content renderer ────────────────────────────────────────────────────────────

async def _render_content(
    content: ui.column,
    user_id: str,
    state: dict,
    on_delete,
    on_retransform,
) -> None:
    # Show skeleton loading cards
    content.clear()
    with content:
        with ui.element("div").classes("ei-gallery-grid w-full"):
            for _ in range(6):
                with ui.card().classes("ei-gallery-card overflow-hidden"):
                    ui.element("div").classes("ei-skeleton-img ei-pulse")
                    with ui.column().classes("p-3 gap-2"):
                        ui.element("div").classes("ei-skeleton-line ei-pulse")
                        ui.element("div").classes("ei-skeleton-line short ei-pulse")

    # Fetch from Supabase
    items = get_user_gallery(user_id, limit=100)
    active = state["filter"]
    filtered = items if active == "all" else [i for i in items if i.get("source_type") == active]

    # Render results
    content.clear()
    with content:
        if not filtered:
            _render_empty_state(active)
        else:
            count = len(filtered)
            ui.label(f"{count} artwork{'s' if count != 1 else ''}").classes(
                "text-sm opacity-40 mb-2"
            )
            with ui.element("div").classes("ei-gallery-grid w-full"):
                for item in filtered:
                    _gallery_card(item, on_delete, on_retransform)


def _render_empty_state(active: str) -> None:
    msgs = {
        "all": ("No artworks yet", "Start creating your first Mughal masterpiece."),
        "generate": ("No generated art yet", "Use the Generate tab to create art from a text prompt."),
        "transform": ("No transformed photos yet", "Use the Transform tab to apply Mughal style to a photo."),
    }
    title, sub = msgs.get(active, msgs["all"])
    with ui.column().classes("w-full items-center justify-center gap-3 py-24"):
        ui.label("☽").classes("text-7xl opacity-15")
        ui.label(title).classes("text-xl font-semibold opacity-50")
        ui.label(sub).classes("text-sm opacity-40 text-center")
        ui.button("✦ Create New", on_click=lambda: ui.navigate.to("/")).classes(
            "ei-btn-primary mt-3"
        )


def _gallery_card(item: dict, on_delete, on_retransform) -> None:
    source_type = item.get("source_type", "generate")
    style = item.get("style_preset", "akbari").capitalize()
    prompt = item.get("prompt", "")
    display_prompt = prompt[:65] + "…" if len(prompt) > 65 else prompt
    image_url = item.get("image_url", "")
    item_id = item.get("id", "")

    with ui.card().classes("ei-gallery-card overflow-hidden"):
        # Full-width image
        ui.image(image_url).classes("w-full object-cover").style("aspect-ratio: 1/1;")

        with ui.column().classes("p-3 gap-2"):
            # Badges
            with ui.row().classes("gap-1 flex-wrap"):
                badge_color = "amber" if source_type == "generate" else "teal"
                badge_label = "✦ Generated" if source_type == "generate" else "⟳ Transformed"
                ui.badge(badge_label, color=badge_color).classes("text-xs")
                ui.badge(style, color="deep-orange").classes("text-xs")

            # Prompt snippet
            ui.label(display_prompt).classes("text-xs opacity-55 leading-snug").props(
                f'title="{prompt.replace(chr(34), chr(39))}"'
            )

            # Action row
            with ui.row().classes("gap-0 mt-1 justify-between w-full"):

                # Download
                ui.button(
                    icon="download",
                    on_click=lambda url=image_url: ui.navigate.to(url, new_tab=True),
                ).props("flat dense").classes("ei-icon-btn").tooltip("Download")

                # Re-transform
                async def handle_retransform(i=item):
                    await on_retransform(i)

                ui.button(
                    icon="auto_fix_high",
                    on_click=handle_retransform,
                ).props("flat dense").classes("ei-icon-btn text-amber-400").tooltip(
                    "Re-transform with a new style"
                )

                # Delete with confirmation dialog
                async def handle_delete(iid=item_id):
                    with ui.dialog() as d, ui.card().classes("p-6 gap-4"):
                        ui.label("Delete this artwork?").classes("font-semibold text-lg")
                        ui.label("This cannot be undone.").classes("text-sm opacity-60")

                        async def confirmed():
                            d.close()
                            await on_delete(iid)

                        with ui.row().classes("gap-3 justify-end w-full mt-2"):
                            ui.button("Cancel", on_click=d.close).classes("ei-btn-outline")
                            ui.button("Delete", on_click=confirmed).classes("ei-btn-danger")
                    d.open()

                ui.button(
                    icon="delete_outline",
                    on_click=handle_delete,
                ).props("flat dense").classes("ei-icon-btn text-red-400").tooltip("Delete artwork")


# ── Re-transform dialog ─────────────────────────────────────────────────────────

async def _retransform_dialog(item: dict, user_id: str, on_done) -> None:
    with ui.dialog() as dialog, ui.card().classes("p-6 gap-4").style(
        "min-width: 360px; max-width: 500px;"
    ):
        ui.label("Re-Transform Artwork").classes("ei-section-label")
        ui.label("Apply a new Mughal style to this image. A new version will be saved to your gallery.").classes(
            "text-sm opacity-60"
        )

        # Thumbnail preview
        ui.image(item.get("image_url", "")).classes(
            "w-full rounded-lg object-cover"
        ).style("max-height: 180px;")

        style_sel = style_panel(item.get("style_preset", "akbari"))
        status = ui.label("").classes("text-sm text-amber-400 min-h-[1.25rem]")

        async def do_transform():
            status.text = "Fetching image from storage…"
            transform_btn.props("loading")
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(item["image_url"])
                    img_bytes = resp.content

                status.text = "Applying Mughal style…"
                result = await run_transform_pipeline(
                    image_bytes=img_bytes,
                    style_preset=style_sel.value,
                    user_id=user_id,
                    original_filename=f"retransform-{item.get('id', '')[:8]}",
                    parent_id=item.get("id"),
                )
                if result.success:
                    dialog.close()
                    ui.notify("New version saved to your gallery!", type="positive")
                    await on_done()
                else:
                    status.text = result.error or "Transformation failed."
            except Exception as e:
                status.text = f"Error: {e}"
            finally:
                transform_btn.props(remove="loading")

        with ui.row().classes("gap-3 justify-end w-full mt-2"):
            ui.button("Cancel", on_click=dialog.close).classes("ei-btn-outline")
            transform_btn = ui.button("Apply Style", on_click=do_transform).classes("ei-btn-primary")

    dialog.open()
