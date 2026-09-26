# Backend

FastAPI service for Document Copilot. See [../CLAUDE.md](../CLAUDE.md) and [CLAUDE.md](CLAUDE.md) for conventions; [../docs/guides/backend-setup.md](../docs/guides/backend-setup.md) for full setup.

## Run

```bash
uv run python -m app
```

**Don't run `uv run uvicorn app.main:app --reload` directly on Windows** — any database-touching request will hang or fail. uvicorn's CLI creates its asyncio event loop before importing the app, so a Windows event-loop-policy fix inside the app itself always runs too late; the default Windows loop (Proactor) isn't compatible with how psycopg does socket I/O, even for synchronous calls dispatched to a thread. `app/__main__.py` sets the correct policy first, then starts uvicorn programmatically in the same process. This is a no-op on Linux/Mac (Railway prod), so it's safe everywhere.

Stop with `Ctrl+C` — don't kill the terminal window, or a stray process can keep `.venv` files locked on Windows.

## Check it's alive

- `http://127.0.0.1:8000/health` → `{"status":"ok"}`
- `http://127.0.0.1:8000/docs` → interactive Swagger UI

## Config

All settings load from `backend/.env` via `app/config.py`. Missing/invalid values fail fast on startup. Required: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, `GROQ_API_KEY`, `ALLOWED_ORIGINS`. See [../docs/guides/supabase-setup.md](../docs/guides/supabase-setup.md) for where to find the Supabase values.

## Dependencies

```bash
uv add <package>          # runtime dep
uv add --dev <package>    # dev-only dep
uv sync                   # install from lockfile
```

## Tests

```bash
uv run pytest -m "not integration"
```
