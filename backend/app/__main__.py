"""Dev server entrypoint: `uv run python -m app`.

Not just a convenience wrapper around `uvicorn app.main:app` — it's required
on Windows. uvicorn's CLI creates its asyncio event loop (via `asyncio.run`)
*before* importing the app module, so a Windows event-loop-policy fix placed
inside app/main.py always runs too late to affect the loop uvicorn already
created. This script sets the policy first, then starts uvicorn programmatically
in the same process, so the fix is in effect before the loop exists.

Without this, psycopg (v3) database connections hang or fail outright on
Windows: the default ProactorEventLoop doesn't support the socket operations
libpq needs, both for psycopg's native async mode and, it turns out, even for
synchronous calls dispatched via asyncio.to_thread() from a thread while a
ProactorEventLoop runs on the main thread. No-op on Linux/Mac (Railway prod),
where asyncio already defaults to a selector-based loop.
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn


def main() -> None:
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
