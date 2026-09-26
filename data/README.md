# Data

Local data artifacts for development live here.

- `downloads/` holds raw source files fetched from SEC EDGAR, grouped by year.
- `markdown/` holds the same filings converted to Markdown via Docling, mirroring the `downloads/` year folders plus a `manifest.json` pointing at the `.md` files. This is what gets loaded into `source_documents.markdown_content`.
- `docling/` holds each filing's DoclingDocument as JSON (same conversion pass as `markdown/`), mirroring the `downloads/` year folders. This is the chunking input for `backend/app/ingest/chunk_and_embed.py` — chunking needs the structured document (headings, tables, provenance), not the flattened Markdown text.
- Downloaded payloads and converted output are gitignored because the corpus can get large; all of it is regenerable from `downloads/`.
- Fetch a sample corpus with `uv run data/download.py`
- Convert the corpus to Markdown + Docling JSON (from `backend/`, so Docling's dependencies are available): `cd backend && uv run python ../data/convert_to_markdown.py`
