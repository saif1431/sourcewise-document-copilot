"""One-off loader: write `source_documents` rows from the converted Markdown corpus.

Reads data/markdown/manifest.json (produced by data/convert_to_markdown.py) and
upserts one row per filing, keyed on the unique accession_number so re-running
is safe. Chunking/embedding into `document_chunks` is a separate, later step.

Run from backend/, so app.config/app.database can resolve:

    cd backend
    uv run python -m app.ingest.load_source_documents
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from app.database.models import SourceDocument
from app.database.session import session_maker

REPO_ROOT = Path(__file__).resolve().parents[3]
MARKDOWN_DIR = REPO_ROOT / "data" / "markdown"

# Not derivable from the SEC manifest (which only carries tickers/CIKs) — the
# sample corpus is fixed to these 5 companies, so a small static map is enough.
COMPANY_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc.",
}


def load_source_documents() -> int:
    manifest = json.loads((MARKDOWN_DIR / "manifest.json").read_text(encoding="utf-8"))

    loaded = 0
    with session_maker() as session:
        for filing in manifest["filings"]:
            local_path = Path(filing["local_path"].replace("\\", "/"))
            markdown_content = (MARKDOWN_DIR / local_path).read_text(encoding="utf-8")
            # report_date is the fiscal period end; filing_date is when it was filed.
            # Fiscal year is grouped by report_date, matching the data/downloads/<year> layout.
            fiscal_year = int((filing["report_date"] or filing["filing_date"])[:4])

            values = {
                "ticker": filing["ticker"],
                "company_name": COMPANY_NAMES[filing["ticker"]],
                "filing_type": filing["form"],
                "filing_date": date.fromisoformat(filing["filing_date"]),
                "fiscal_year": fiscal_year,
                "source_url": filing["source_url"],
                "markdown_content": markdown_content,
            }

            stmt = (
                insert(SourceDocument)
                .values(accession_number=filing["accession_number"], **values)
                .on_conflict_do_update(index_elements=[SourceDocument.accession_number], set_=values)
            )
            session.execute(stmt)
            loaded += 1

        session.commit()

    return loaded


if __name__ == "__main__":
    count = load_source_documents()
    print(f"Loaded {count} source document(s) from {MARKDOWN_DIR}")
