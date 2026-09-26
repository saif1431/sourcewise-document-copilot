from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database.url import normalize_database_url

# Sync engine, not async. psycopg (v3)'s native asyncio mode requires a
# selector-based event loop, but `uvicorn app.main:app` creates its event loop
# (via asyncio.run) *before* importing this module, so a Windows event-loop-
# policy fix here would always be too late. Blocking calls are instead wrapped
# in asyncio.to_thread() at call sites — the same pattern already used for the
# Supabase client in app/auth/dependencies.py.
engine = create_engine(normalize_database_url(settings.database_url))
session_maker = sessionmaker(engine, expire_on_commit=False)
