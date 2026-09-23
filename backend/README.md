# Backend

FastAPI service for Document Copilot. See [../CLAUDE.md](../CLAUDE.md) and [CLAUDE.md](CLAUDE.md) for conventions; [../docs/guides/backend-setup.md](../docs/guides/backend-setup.md) for full setup.

## Run

```bash
uv run uvicorn app.main:app --reload
```

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
