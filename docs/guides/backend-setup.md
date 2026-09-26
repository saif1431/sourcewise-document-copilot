# Backend setup

This project uses a separate Python + FastAPI backend because the server is responsible for AI and document-processing work, not just basic web CRUD. Python gives us the strongest ecosystem for ingestion, chunking, embeddings, retrieval, evaluation, and LLM workflows. Keeping this logic behind a dedicated API also keeps the frontend focused on the user experience while the backend owns data access, orchestration, and grounding.

## Init (from empty `backend/`)

```bash
cd backend
uv sync
uv add fastapi uvicorn pydantic pydantic-settings httpx structlog groq supabase pydantic-ai sqlalchemy alembic "psycopg[binary]" pgvector langchain-huggingface sentence-transformers
uv add --dev pytest ruff
```

## Database migrations

Alembic owns database schema changes for this project. SQLAlchemy models describe the app tables, and Alembic migrations apply those changes to Supabase Postgres.

Initialize Alembic once from `backend/`:

```bash
uv run alembic init alembic
```

Configure `alembic/env.py` to import the app's SQLAlchemy metadata and read the direct database URL from `app.config.settings`. Use the direct/session Supabase database connection, not the transaction pooler URL, for migrations.

Create a migration after changing SQLAlchemy models:

```bash
uv run alembic revision --autogenerate -m "add document tables"
```

Always review the generated migration. Add explicit operations for Supabase/Postgres features that autogenerate cannot reliably infer:

- `create extension if not exists vector`
- `vector(384)` columns (dimension for `all-MiniLM-L6-v2`)
- generated `tsvector` columns
- HNSW and GIN indexes
- RLS enablement and policies

Apply migrations:

```bash
uv run alembic upgrade head
```

## Run

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app
```

## Imports (`from app...`)

`backend/app` is installed as an editable package by `uv sync`, so `from app...` imports work from uvicorn, direct Python execution, tests, and Jupyter kernels that use the backend venv.

The `[build-system]` and `[tool.hatch.build.targets.wheel]` sections in `backend/pyproject.toml` tell uv how to install the local `app/` package. Without that package install, imports depend on the current working directory or a manually configured `PYTHONPATH`, which is fragile in notebooks and IDE run buttons.

Preferred API server command:

```bash
cd backend
uv run python -m app
```

**Not** `uv run uvicorn app.main:app --reload` directly — on Windows, any database-touching request hangs or fails, because uvicorn's CLI creates its asyncio event loop before importing the app, so a Windows event-loop-policy fix placed inside the app always runs too late. `app/__main__.py` sets the policy first, then starts uvicorn programmatically in the same process; this is a no-op on Linux/Mac (Railway prod).

For Jupyter, install and select the backend kernel:

```bash
cd backend
uv run python -m ipykernel install --user --name document-copilot-backend --display-name "Document Copilot Backend"
```

Then notebooks can import backend modules:

```python
from app.config import settings
```

## Sample SEC data

From the repo root (stdlib-only script, no backend env needed):

```bash
uv run data/download.py
```
