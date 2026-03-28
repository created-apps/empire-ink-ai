"""
Handles all Supabase Auth operations: sign up, sign in, sign out, session refresh.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from supabase import Client
from app.database import get_anon_client

logger = logging.getLogger(__name__)


@dataclass
class AuthResult:
    success: bool
    user_id: str | None = None
    email: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    error: str | None = None


def sign_up(email: str, password: str) -> AuthResult:
    """Registers a new user with Supabase Auth."""
    client: Client = get_anon_client()
    try:
        response = client.auth.sign_up({"email": email, "password": password})
        if response.user:
            return AuthResult(
                success=True,
                user_id=str(response.user.id),
                email=response.user.email,
                access_token=response.session.access_token if response.session else None,
                refresh_token=response.session.refresh_token if response.session else None,
            )
        return AuthResult(success=False, error="Sign up failed — no user returned.")
    except Exception as e:
        logger.error(f"sign_up error: {e}")
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "already been registered" in error_msg.lower():
            return AuthResult(success=False, error="This email is already registered. Please log in.")
        return AuthResult(success=False, error=f"Sign up failed: {error_msg}")


def sign_in(email: str, password: str) -> AuthResult:
    """Signs in an existing user and returns their session tokens."""
    client: Client = get_anon_client()
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        if response.user and response.session:
            return AuthResult(
                success=True,
                user_id=str(response.user.id),
                email=response.user.email,
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
            )
        return AuthResult(success=False, error="Invalid email or password.")
    except Exception as e:
        logger.error(f"sign_in error: {e}")
        return AuthResult(success=False, error="Invalid email or password.")


def sign_out(access_token: str) -> bool:
    """Signs out the user by invalidating their session."""
    client: Client = get_anon_client()
    try:
        client.auth.set_session(access_token, "")
        client.auth.sign_out()
        return True
    except Exception as e:
        logger.warning(f"sign_out error (non-critical): {e}")
        return False
