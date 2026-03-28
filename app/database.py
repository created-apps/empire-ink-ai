from supabase import create_client, Client
from app.config import settings


def get_anon_client() -> Client:
    """Anon client — for auth operations (sign in, sign up, sign out)."""
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_service_client() -> Client:
    """Service role client — for server-side DB and Storage operations (bypasses RLS)."""
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_user_client(access_token: str) -> Client:
    """Client authenticated as the logged-in user — respects RLS policies."""
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client
