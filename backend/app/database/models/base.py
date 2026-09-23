from sqlalchemy import Column, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase

# sentence-transformers/all-MiniLM-L6-v2 output size — see app/config.py's embedding_dimensions
EMBEDDING_DIMENSIONS = 384


class Base(DeclarativeBase):
    pass


# Stub for Supabase Auth's auth.users table: Supabase owns and migrates it, we never touch it,
# but SQLAlchemy needs *something* in our metadata to resolve users.id's foreign key against.
# Distinct from our own public.users table (different schema — no name collision in Postgres).
# Excluded from Alembic autogenerate via env.py's include_object filter on schema == "auth".
auth_users = Table(
    "users",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    schema="auth",
)
