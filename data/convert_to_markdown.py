"""Convert downloaded SEC filings (HTML) to Markdown with Docling.

Mirrors data/downloads/<year>/*.htm into data/markdown/<year>/*.md, and
writes a manifest.json alongside it (same shape as data/downloads/manifest.json,
with local_path/primary_document pointed at the converted .md files) so the
Markdown corpus is self-describing for later ingestion.

Also mirrors data/downloads/<year>/*.htm into data/docling/<year>/*.json —
each filing's DoclingDocument (headings, tables, provenance), saved from the
same conversion pass. backend/app/ingest/chunk_and_embed.py chunks from this
structured document rather than the flattened Markdown: re-parsing our own
exported Markdown back into a DoclingDocument loses table/heading fidelity
(verified empirically — see docs/todos.md Phase 4 notes).

Docling ships as a backend dev/ingest dependency (see backend/pyproject.toml),
so run this from the backend venv:

    cd backend
    uv run python ../data/convert_to_markdown.py
"""

from __future__ import annotations

import json
from pathlib import Path

from docling.datamodel.base_models import ConversionStatus
from docling.document_converter import DocumentConverter

DATA_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = DATA_DIR / "downloads"
MARKDOWN_DIR = DATA_DIR / "markdown"
DOCLING_DIR = DATA_DIR / "docling"


def convert_filings() -> None:
    html_paths = sorted(DOWNLOADS_DIR.glob("*/*.htm*"))
    if not html_paths:
        print(f"No HTML files found under {DOWNLOADS_DIR}")
        return

    manifest = json.loads((DOWNLOADS_DIR / "manifest.json").read_text(encoding="utf-8"))
    filings_by_local_path = {
        Path(filing["local_path"]).as_posix(): filing for filing in manifest["filings"]
    }

    converter = DocumentConverter()
    converted = 0

    for result in converter.convert_all(html_paths, raises_on_error=False):
        source_path = Path(result.input.file)
        relative_path = source_path.relative_to(DOWNLOADS_DIR)

        if result.status not in (ConversionStatus.SUCCESS, ConversionStatus.PARTIAL_SUCCESS):
            print(f"Skipping {relative_path}: conversion status {result.status.value}")
            continue

        out_path = MARKDOWN_DIR / relative_path.with_suffix(".md")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result.document.export_to_markdown(), encoding="utf-8")

        docling_json_path = DOCLING_DIR / relative_path.with_suffix(".json")
        docling_json_path.parent.mkdir(parents=True, exist_ok=True)
        result.document.save_as_json(docling_json_path)

        filing = filings_by_local_path.get(relative_path.as_posix())
        if filing is not None:
            filing["primary_document"] = out_path.with_suffix(".md").name
            filing["local_path"] = str(relative_path.with_suffix(".md"))

        converted += 1
        print(f"Converted {relative_path} -> {out_path.relative_to(DATA_DIR)}")

    manifest_path = MARKDOWN_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Converted {converted}/{len(html_paths)} filing(s) to {MARKDOWN_DIR}")
    print(f"Docling documents: {DOCLING_DIR}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    convert_filings()
