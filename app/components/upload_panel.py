"""
Drag-and-drop image upload panel with live preview.
Used on the Transform tab of the home page.
"""

from __future__ import annotations

import base64
from nicegui import ui, events


class UploadPanel:
    """
    Manages image upload state and renders the upload UI.

    Usage:
        panel = UploadPanel()
        panel.render()
        # Access panel.image_bytes for the uploaded bytes
        # Access panel.filename for the original filename
    """

    def __init__(self):
        self.image_bytes: bytes | None = None
        self.filename: str = "upload"
        self._preview_img: ui.image | None = None
        self._status_label: ui.label | None = None

    def render(self) -> None:
        """Renders the upload zone and preview area."""
        with ui.column().classes("w-full gap-3"):
            ui.label("Upload Your Photo").classes("ei-section-label")

            # Upload zone
            ui.upload(
                label="Drop image here or click to browse",
                auto_upload=True,
                max_file_size=10_000_000,
                on_upload=self._handle_upload,
                on_rejected=self._handle_rejected,
            ).classes("w-full ei-upload-zone").props(
                'accept="image/jpeg,image/png,image/webp,image/gif" flat bordered'
            )

            # Status message
            self._status_label = ui.label("").classes("text-sm text-center opacity-70")

            # Preview area (hidden until image uploaded)
            with ui.column().classes("w-full items-center gap-2") as preview_col:
                self._preview_img = ui.image("").classes(
                    "w-full max-w-sm rounded-lg border-2 border-amber-700/30 shadow-lg"
                ).style("display: none; aspect-ratio: 1/1; object-fit: cover;")

                self._clear_btn = ui.button(
                    "✕ Clear", on_click=self.clear
                ).classes("ei-btn-outline text-sm").style("display: none;")

    def _handle_upload(self, e: events.UploadEventArguments) -> None:
        self.image_bytes = e.content.read()
        self.filename = e.name or "upload"

        # Show preview as base64 data URI
        mime = "image/jpeg"
        if self.filename.lower().endswith(".png"):
            mime = "image/png"
        elif self.filename.lower().endswith(".webp"):
            mime = "image/webp"

        b64 = base64.b64encode(self.image_bytes).decode("utf-8")
        data_uri = f"data:{mime};base64,{b64}"

        if self._preview_img:
            self._preview_img.source = data_uri
            self._preview_img.style("display: block;")
        if self._clear_btn:
            self._clear_btn.style("display: flex;")
        if self._status_label:
            size_kb = len(self.image_bytes) / 1024
            self._status_label.text = f"✓ {self.filename} ({size_kb:.0f} KB) — ready to transform"
            self._status_label.classes(add="text-green-400", remove="text-red-400")

    def _handle_rejected(self, e) -> None:
        ui.notify("File rejected — use JPEG, PNG, or WEBP under 10MB.", type="negative")
        if self._status_label:
            self._status_label.text = "Upload failed. Please try a different image."

    def clear(self) -> None:
        self.image_bytes = None
        self.filename = "upload"
        if self._preview_img:
            self._preview_img.source = ""
            self._preview_img.style("display: none;")
        if self._clear_btn:
            self._clear_btn.style("display: none;")
        if self._status_label:
            self._status_label.text = ""

    @property
    def has_image(self) -> bool:
        return self.image_bytes is not None and len(self.image_bytes) > 0
