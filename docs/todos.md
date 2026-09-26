# Document Copilot — implementation checklist

Work top to bottom. Each phase unlocks the next. Check items off as you go.

## Where to start: backend, frontend, or both?

**Start with foundation, then backend-led vertical slices.**

| Order | Why |
| ----- | --- |
| 1. Supabase + sample data | Everything persists here; you need a project and a corpus to test against. |
| 2. Backend schema + migrations | Auth, chat, retrieval, and citations all depend on the data model. |
| 3. Thin vertical slices | Wire auth, then a stubbed chat stream, then real RAG — each slice touches frontend + backend together. |
| 4. Frontend in parallel (lightly) | Scaffold the SPA early, but don't build citation UI or chat polish until the backend can return real grounded answers. |

The critical path is **data model → ingestion → retrieval → LLM → citations**. The frontend is mostly a streaming chat shell with auth and citation display — it shouldn't get far ahead of working APIs.

---

## Phase 0 — Prerequisites & foundation

- [*] Install toolchain: Python 3.12+, `uv`, Node 20+, `npm` (see [README](../README.md))
- [*] Create Supabase project and collect credentials ([supabase-setup](guides/supabase-setup.md))
- [*] Create Groq API key (needed from Phase 6 onward — free tier). No key needed for embeddings; those run locally via HuggingFace `sentence-transformers/all-MiniLM-L6-v2`.
- [*] Set `USER_AGENT` in `data/download.py` and download sample 10-K corpus:
  ```bash
  uv run data/download.py
  ```
- [*] Confirm `data/downloads/manifest.json` lists AAPL, MSFT, NVDA, AMZN, GOOGL filings (2021–2025)

---

## Phase 1 — Backend scaffold & database

Goal: a running FastAPI service with a migrated Supabase schema.

- [*] Init backend deps and project layout ([backend-setup](guides/backend-setup.md))
- [*] `app/config.py` — settings module, fail fast on missing env vars
- [*] `app/main.py` — FastAPI app, CORS, health check (`GET /health`)
- [*] SQLAlchemy models in `app/database/models/` (split one-class-per-file per later request; `__init__.py` re-exports everything):
  - [*] `users` (public.users, FK'd to Supabase Auth's `auth.users.id` — one row per analyst)
  - [*] `source_documents`
  - [*] `document_chunks` (embedding `vector(384)` + generated `tsvector`)
  - [*] `chat_threads`
  - [*] `chat_messages`
  - [*] `message_citations`
- [*] Alembic init + first migration — written and offline-SQL-validated, **not yet applied** (see blocker below):
  - [*] `create extension if not exists vector`
  - [*] `vector(384)` embedding column (dimension for `all-MiniLM-L6-v2`)
  - [*] generated `tsvector` column on chunks
  - [*] HNSW index (vector) + GIN index (full-text)
  - [*] RLS policies (users see only their own chats)
- [*] ~~Blocker: direct-connection host was IPv6-only~~ — resolved by switching `DATABASE_URL` to the Session pooler connection string; live connection + empty target database confirmed
- [*] `uv run alembic upgrade head` against Supabase — applied and verified: all 6 tables + `vector` extension + HNSW/GIN indexes + RLS policies confirmed live in the database
- [*] `app/database/supabase.py` — anon-key (user JWT verification) and service-role clients, `lru_cache`-backed singletons
- [*] Verify: `uv run uvicorn app.main:app --reload` → health check returns 200 (confirmed earlier this phase)

---

## Phase 2 — Auth (full stack)

Goal: analysts can sign in with email; backend rejects unauthenticated requests.

**Backend**

- [*] `app/auth/dependencies.py` — verify `Authorization: Bearer <supabase_jwt>`, expose `get_current_user`
- [*] Reject missing/expired tokens with `401` before any chat or retrieval work

**Frontend**

- [*] Scaffold Vite + React + TypeScript + Tailwind + shadcn ([frontend-setup](guides/frontend-setup.md)) — Base UI primitives, Nova preset
- [*] `src/lib/env.ts` — validate `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- [*] `src/lib/supabase.ts` — browser Supabase client
- [*] `src/lib/http.ts` + `src/lib/api.ts` — fetch wrapper with automatic bearer token
- [*] Sign-in / sign-up pages (email only, no SSO) — `src/pages/sign-in.tsx`, `src/pages/sign-up.tsx`
- [*] Protected routes — redirect unauthenticated users to login (`src/components/protected-route.tsx`, `src/lib/auth.tsx`)
- [*] Public self-serve sign-up intentionally disabled in Supabase (pilot is invite-only, provisioned via the service-role admin API, not the public `/auth/v1/signup` endpoint) — `src/pages/sign-up.tsx` exists for when/if this reopens, but analysts are created server-side for now
- [*] Verify: created a user via the Supabase admin API, signed in, confirmed `Authorization: Bearer <token>` reaches `GET /auth/me` on the real running backend and returns the correct id/email (then deleted the test user)

---

## Phase 3 — Chat shell (vertical slice, stubbed)

Goal: end-to-end chat UI streaming from FastAPI, no real retrieval yet.

**Backend**

- [*] Chat thread CRUD: list threads, create thread, load message history — `app/api/chat.py`, `app/database/chats.py`
- [*] `POST /chat/stream` — accepts AI SDK message format, streams a stubbed assistant reply — `app/chat/streaming.py`, `app/chat/orchestrator.py` (AI SDK v5 UI message stream protocol, verified byte-for-byte against a live request)
- [*] Persist user + assistant messages to `chat_messages` after stream completes — confirmed via reload (`GET /chat/threads/{id}/messages` returns both messages after streaming)
- [*] `403` when user accesses another user's thread — verified by code review + shared code path with the already-verified 404 case (`_get_owned_thread`'s single `if/else`); a live two-user HTTP test was attempted but blocked by Supabase free-tier Admin API rate limiting after repeated test-user creation this session (see cleanup note below)
- [*] **Real bug found + fixed:** `uvicorn app.main:app --reload` hangs/fails on every DB-touching request on Windows, with or without `--reload`. Root cause: uvicorn's CLI creates its asyncio event loop (`asyncio.run`) *before* importing the app module, so a Windows event-loop-policy fix placed inside `app/main.py` (or anywhere the app imports) always runs too late — the loop already exists as `ProactorEventLoop`, which psycopg (v3) can't use, even for sync calls dispatched via `asyncio.to_thread`. Fixed with `app/__main__.py`, which sets `WindowsSelectorEventLoopPolicy` first, then calls `uvicorn.run(...)` programmatically in the same process — no-op on Linux/Mac (Railway prod). **Run command is now `uv run python -m app`**, not `uv run uvicorn app.main:app --reload` (updated in `backend/README.md` and `docs/guides/backend-setup.md`).
- [ ] **Cleanup needed:** several throwaway test users (`test-*@example.com`) created during this session's verification are still in Supabase Auth — `admin.auth.admin.list_users()`/`delete_user()` both fail with "User not allowed" (separate from the rate-limit issue above; looks like the service-role key lacks Auth Admin list/delete scope). Clean up manually via the Supabase Dashboard → Authentication → Users, or fix the key's admin scope first.

**Frontend**

- [*] React Router: login, chat list, chat thread routes — `/login`, `/signup`, `/chats`, `/chats/:threadId` (`src/App.tsx`, `src/pages/chat/*`)
- [*] AI SDK chat primitives pointed at `POST /chat/stream` with Supabase bearer token — `useChat` + `DefaultChatTransport` in `src/pages/chat/thread.tsx`
- [*] Thread sidebar (past conversations) — `src/components/chat/thread-sidebar.tsx`, shadcn `Sidebar`
- [*] Basic message list + input + streaming indicator — `src/components/chat/message-list.tsx` (shadcn `MessageScroller`/`Message`/`Bubble`), `src/components/chat/message-input.tsx` (shadcn `InputGroup`)
- [*] Verify: create thread, send message, see streamed stub response, reload and see history — verified against the live backend via its REST/SSE contract directly (create → stream → reload all confirmed); the React UI itself wasn't click-tested in an actual browser in this session — worth a manual pass in `npm run dev`

---

## Phase 4 — Ingestion pipeline

Goal: SEC filings in the corpus are parsed, chunked, embedded, and stored in Supabase.

- [*] `ingest/` scripts (or CLI entrypoint) for one-off corpus loading — `data/convert_to_markdown.py` (HTML → Markdown, outside the backend) + `backend/app/ingest/load_source_documents.py` (Markdown → Supabase) + `backend/app/ingest/chunk_and_embed.py` (Docling JSON → chunks + embeddings → Supabase)
- [*] HTML → normalized Markdown extraction (preserve page/section metadata) — Docling, via `data/convert_to_markdown.py`; mirrors `data/downloads/<year>/` into `data/markdown/<year>/` plus a repointed `manifest.json`. Also saves each filing's DoclingDocument as JSON to `data/docling/<year>/` from the same conversion pass — needed for chunking (see below)
- [*] Chunking strategy — Docling's `HybridChunker` (hierarchical + token-aware): walks the document tree per item (paragraph/table/list), merges/splits to fit the embedding model's own token budget (256, via `HuggingFaceTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")`). Stores chunk index, page (provenance, mostly `None` — see note below), section, ticker, filing type, year. Two findings from analyzing the Docling documents, documented in `chunk_and_embed.py`'s module docstring:
  - SEC EDGAR 10-K HTML has zero semantic `<h1>-<h6>` tags (headings are styled spans) — verified 0 `TitleItem`/`SectionHeaderItem` across a full filing — so `chunk.meta.headings` is empty for this whole corpus and `section` is `None`. Hierarchical chunking still pays off as item-aware splitting (never mid-table/mid-paragraph) + token-budget merging, just not heading breadcrumbs, on this corpus.
  - Chunking must run against the per-filing DoclingDocument JSON (`data/docling/`), not `source_documents.markdown_content`: re-parsing our own exported Markdown back into a DoclingDocument was tried and measurably lossy (misaligned/near-empty table chunks) versus chunking the original single conversion pass.
  - Also swapped Docling's default table serializer (`TripletTableSerializer`, which flattens every cell as noisy repeated "row_label = value" pairs) for its built-in `MarkdownTableSerializer` — verified cleaner, properly aligned table chunks.
- [*] Write `source_documents` rows with filing metadata from `manifest.json` — `uv run python -m app.ingest.load_source_documents` (idempotent upsert on `accession_number`); verified 25/25 rows live in Supabase (5 tickers × 2021–2025)
- [*] Write `document_chunks` rows with text + metadata — `uv run python -m app.ingest.chunk_and_embed`
- [*] Local HuggingFace embedding generation (`sentence-transformers/all-MiniLM-L6-v2` via `langchain_huggingface.HuggingFaceEmbeddings`, no API key) → store `vector(384)` per chunk — same script, batched per filing
- [*] Generated `tsvector` populated for full-text search — confirmed 0 `NULL` `search_vector` rows across all 21,533 chunks (Postgres `GENERATED ALWAYS` column, populates automatically on insert)
- [*] Idempotent re-run (skip already-ingested documents) — `chunk_and_embed.py` skips any `source_documents` row that already has `document_chunks`; this is also what let the run recover cleanly from two transient Supabase connection drops mid-run (see below) without duplicating or corrupting data
- [ ] Unit tests: chunking logic, metadata extraction
- [*] Run ingestion on full sample corpus (25 filings × 5 companies) — 21,533 chunks written. Hit two transient Supabase connection failures mid-run ("server closed the connection unexpectedly", then "SSL connection has been closed unexpectedly" / "statement timeout") — root-caused to (1) a single DB session held open across the whole run, including the CPU-bound embedding step per filing, and (2) an initial bulk `SELECT *` on `source_documents` pulling ~20MB of unused `markdown_content` text. Fixed by opening a short-lived session per document (only around the actual DB read/write) and selecting only the columns the script needs; re-running picked up cleanly thanks to the idempotent skip
- [*] Verify: chunks exist in Supabase; spot-check a known passage (e.g. Apple revenue mix table) — ran a real `pgvector` cosine-similarity query ("Apple total net sales by product category iPhone Mac iPad") against AAPL 2025 chunks: top result was the iPhone/Mac/iPad net-sales narrative, second was the Wearables/Home/Accessories revenue table, third the by-country net-sales table — all genuinely relevant

---

## Phase 5 — Retrieval

Goal: a user question returns ranked, relevant source passages.

- [ ] `retrieval/queries.py` — pgvector semantic search over `document_chunks`
- [ ] `retrieval/queries.py` — Postgres full-text search over `search_vector`
- [ ] `retrieval/fusion.py` — Reciprocal Rank Fusion in Python
- [ ] `retrieval/retriever.py` — query → fused ranked passages + neighbor chunks
- [ ] Unit tests: fusion ranking, query assembly (mock DB)
- [ ] Integration test (optional, `@pytest.mark.integration`): real query against ingested corpus
- [ ] Verify: test queries from [client-brief](client-brief.md) return relevant chunks (manual or scripted)

---

## Phase 6 — LLM agent & grounding

Goal: grounded answers with enforced citations — the core product contract.

- [ ] `assistant/instructions.md` — product contract (cite everything, refuse to invent, no stock picks)
- [ ] PydanticAI agent with typed deps (`DocumentAgentDeps`) and output (`GroundedAnswer`)
- [ ] Agent tools: `search_filings`, `read_chunk`, `read_surrounding_chunks`
- [ ] `chat/orchestrator.py` — one turn: retrieve → agent → validate → stream → persist
- [ ] `grounding/validator.py` — every citation maps to a retrieved passage; fail closed on violation
- [ ] `chat/streaming.py` — AI SDK-compatible stream (text deltas + citation metadata parts)
- [ ] Persist `message_citations` linked to assistant messages
- [ ] Unit tests: citation validation, grounding enforcement, message conversion
- [ ] Verify against [client-brief example questions](client-brief.md#example-analyst-questions):
  - [ ] Answers cite specific filings and pages
  - [ ] Under-specified questions get "not enough evidence" responses
  - [ ] Question 10 (generative AI margins) refuses to infer beyond filings

---

## Phase 7 — Trust UI (citations & source passages)

Goal: analysts can verify every claim in one click — this is what makes the product usable.

- [ ] Citation chips/links on assistant messages (company, filing type, date, page/section)
- [ ] Source passage panel — show underlying excerpt for selected citation
- [ ] Empty states (no threads, no corpus match)
- [ ] Error states (auth expired, retrieval failure, grounding failure, network/CORS)
- [ ] Loading/streaming status during assistant run
- [ ] Verify: click a citation → see the exact passage from the filing

---

## Phase 8 — Pilot readiness

Goal: 5 senior analysts can use it for a week and report ≥3 hours saved per analyst per week.

- [ ] README "Running locally" section — copy-paste commands for backend + frontend + env vars
- [ ] Seed or document how to ingest/update the corpus
- [ ] Smoke-test all 10 example questions from the client brief
- [ ] Confirm chat history persists across sessions
- [ ] Confirm ~40-user scale assumptions (no hardcoded single-user shortcuts)
- [ ] Basic structured logging on backend (`structlog`) for debugging failed turns
- [ ] Review latency: streaming starts within a few seconds for typical queries

---

## Phase 9 — Deployment (Railway)

- [ ] Railway: backend service (Uvicorn, env vars, `ALLOWED_ORIGINS`)
- [ ] Railway: frontend service (Vite build, `VITE_*` env vars at build time)
- [ ] Supabase: re-enable email confirmation for production if disabled during dev
- [ ] Run `alembic upgrade head` against production Supabase (direct connection)
- [ ] Run ingestion against production database
- [ ] End-to-end test on deployed URLs with a real Driftwood-style email account

---

## Quick reference

| Doc | Purpose |
| --- | ------- |
| [client-brief.md](client-brief.md) | What Driftwood needs and example questions |
| [architecture.md](architecture.md) | System design, data model, streaming contract |
| [guides/supabase-setup.md](guides/supabase-setup.md) | Hosted Postgres + Auth |
| [guides/backend-setup.md](guides/backend-setup.md) | FastAPI + Alembic commands |
| [guides/frontend-setup.md](guides/frontend-setup.md) | Vite + React scaffold commands |