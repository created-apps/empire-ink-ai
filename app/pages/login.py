"""
Login and Register NiceGUI pages.
Routes: /login, /register
"""

from nicegui import ui, app
from app.services.auth_service import sign_in, sign_up


def _auth_guard_redirect() -> bool:
    """If user is already logged in, redirect to home. Returns True if redirected."""
    if app.storage.user.get("user_id"):
        ui.navigate.to("/")
        return True
    return False


@ui.page("/login")
def login_page() -> None:
    if _auth_guard_redirect():
        return

    ui.add_head_html('<link rel="stylesheet" href="/static/mughal.css">')

    with ui.column().classes("ei-auth-page"):
        # Decorative header
        with ui.column().classes("ei-auth-header items-center gap-2"):
            ui.label("☽").classes("text-5xl")
            ui.label("Empire & Ink").classes("ei-logo-text text-3xl font-bold")
            ui.label("AI Mughal Art Studio").classes("text-sm tracking-widest opacity-70")

        with ui.card().classes("ei-auth-card"):
            ui.label("Sign In").classes("text-xl font-semibold mb-4 ei-heading")

            email_input = ui.input(
                label="Email address",
                placeholder="you@example.com",
            ).classes("w-full ei-input").props("type=email autocomplete=email")

            password_input = ui.input(
                label="Password",
                password=True,
                password_toggle_button=True,
            ).classes("w-full ei-input").props("autocomplete=current-password")

            error_label = ui.label("").classes("text-red-400 text-sm min-h-[1.2rem]")

            async def handle_login():
                error_label.text = ""
                email = email_input.value.strip()
                password = password_input.value

                if not email or not password:
                    error_label.text = "Please enter your email and password."
                    return

                login_btn.props("loading")
                result = sign_in(email, password)
                login_btn.props(remove="loading")

                if result.success:
                    app.storage.user["user_id"] = result.user_id
                    app.storage.user["email"] = result.email
                    app.storage.user["access_token"] = result.access_token
                    ui.navigate.to("/")
                else:
                    error_label.text = result.error or "Sign in failed."

            login_btn = ui.button("Sign In", on_click=handle_login).classes("w-full ei-btn-primary mt-2")

            # Allow pressing Enter to submit
            password_input.on("keydown.enter", handle_login)
            email_input.on("keydown.enter", handle_login)

            ui.separator().classes("my-4 opacity-30")

            with ui.row().classes("items-center gap-1 justify-center text-sm opacity-70"):
                ui.label("Don't have an account?")
                ui.link("Create one", "/register").classes("ei-link")


@ui.page("/register")
def register_page() -> None:
    if _auth_guard_redirect():
        return

    ui.add_head_html('<link rel="stylesheet" href="/static/mughal.css">')

    with ui.column().classes("ei-auth-page"):
        with ui.column().classes("ei-auth-header items-center gap-2"):
            ui.label("☽").classes("text-5xl")
            ui.label("Empire & Ink").classes("ei-logo-text text-3xl font-bold")
            ui.label("Join the Art Studio").classes("text-sm tracking-widest opacity-70")

        with ui.card().classes("ei-auth-card"):
            ui.label("Create Account").classes("text-xl font-semibold mb-4 ei-heading")

            email_input = ui.input(
                label="Email address",
                placeholder="you@example.com",
            ).classes("w-full ei-input").props("type=email autocomplete=email")

            password_input = ui.input(
                label="Password",
                password=True,
                password_toggle_button=True,
                placeholder="Minimum 6 characters",
            ).classes("w-full ei-input").props("autocomplete=new-password")

            confirm_input = ui.input(
                label="Confirm password",
                password=True,
                password_toggle_button=True,
            ).classes("w-full ei-input").props("autocomplete=new-password")

            error_label = ui.label("").classes("text-red-400 text-sm min-h-[1.2rem]")

            async def handle_register():
                error_label.text = ""
                email = email_input.value.strip()
                password = password_input.value
                confirm = confirm_input.value

                if not email or not password:
                    error_label.text = "Please fill in all fields."
                    return
                if len(password) < 6:
                    error_label.text = "Password must be at least 6 characters."
                    return
                if password != confirm:
                    error_label.text = "Passwords do not match."
                    return

                register_btn.props("loading")
                result = sign_up(email, password)
                register_btn.props(remove="loading")

                if result.success:
                    if result.access_token:
                        app.storage.user["user_id"] = result.user_id
                        app.storage.user["email"] = result.email
                        app.storage.user["access_token"] = result.access_token
                        ui.navigate.to("/")
                    else:
                        # Supabase email confirmation required
                        ui.notify(
                            "Account created! Check your email to confirm before logging in.",
                            type="positive",
                            timeout=8000,
                        )
                        ui.navigate.to("/login")
                else:
                    error_label.text = result.error or "Registration failed."

            register_btn = ui.button("Create Account", on_click=handle_register).classes(
                "w-full ei-btn-primary mt-2"
            )

            confirm_input.on("keydown.enter", handle_register)

            ui.separator().classes("my-4 opacity-30")

            with ui.row().classes("items-center gap-1 justify-center text-sm opacity-70"):
                ui.label("Already have an account?")
                ui.link("Sign in", "/login").classes("ei-link")
