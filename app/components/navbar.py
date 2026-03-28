"""
Top navigation bar — shared across all protected pages.
Shows logo, nav links, and logout button.
"""

from nicegui import ui, app


def navbar() -> None:
    """Renders the Mughal-themed top navigation bar."""
    with ui.header().classes("ei-navbar items-center justify-between px-6 py-3"):

        # Logo + brand
        with ui.row().classes("items-center gap-3 cursor-pointer").on("click", lambda: ui.navigate.to("/")):
            ui.label("☽").classes("text-3xl")
            with ui.column().classes("gap-0"):
                ui.label("Empire & Ink").classes("ei-logo-text text-xl font-bold leading-none")
                ui.label("AI Mughal Art Studio").classes("text-xs opacity-70 tracking-widest")

        # Nav links
        with ui.row().classes("items-center gap-6 hidden sm:flex"):
            ui.link("Generate", "/").classes("ei-nav-link")
            ui.link("Gallery", "/gallery").classes("ei-nav-link")

        # Logout
        async def logout():
            from app.services.auth_service import sign_out
            token = app.storage.user.get("access_token", "")
            if token:
                sign_out(token)
            app.storage.user.clear()
            ui.navigate.to("/login")

        ui.button("Sign Out", on_click=logout).classes("ei-btn-outline text-sm")
