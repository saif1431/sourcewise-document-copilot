from functools import lru_cache

from supabase import Client, create_client

from app.config import settings


@lru_cache
def get_supabase_client() -> Client:
    """Anon-key client. Safe for verifying a user's own JWT via Supabase Auth.

    Chat/document data itself is read and written through SQLAlchemy against
    DATABASE_URL, not through this client — see app/database/models.py and
    docs/architecture.md's Supabase and FastAPI Communication section.
    """
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache
def get_supabase_admin_client() -> Client:
    """Service-role client. Privileged Supabase Auth/Admin API calls only — never expose to the browser."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
