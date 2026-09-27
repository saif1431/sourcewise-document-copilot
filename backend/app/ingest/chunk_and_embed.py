"""One-off loader: chunk + embed filings into `document_chunks`.

Chunks from each filing's DoclingDocument (data/docling/<year>/*.json, saved by
data/convert_to_markdown.py in the same conversion pass as the Markdown export)
rather than from `source_documents.markdown_content`. Re-parsing our own
exported Markdown back into a DoclingDocument was tried and measurably loses
fidelity — tables come out misaligned or near-empty — because the Markdown
export is already a lossy flattening of the original structure. The Docling
JSON preserves that structure (headings, tables, provenance) losslessly.

Uses Docling's HybridChunker for hierarchical, token-aware chunking: it walks
the document tree (paragraphs, tables, lists) instead of splitting on a fixed
character count, and merges/splits chunks to fit a token budget. The tokenizer
is the embedding model's own HuggingFace tokenizer, so chunks never exceed
what all-MiniLM-L6-v2 (256 tokens) can actually encode.

Note: SEC EDGAR 10-K HTML has no semantic <h1>-<h6> tags — filings style
headings with bold/underlined spans, not real heading elements — so Docling
can't recover a heading hierarchy that was never marked up, and
`chunk.meta.headings` is empty for this whole corpus (verified). The real
benefit of hierarchical chunking here is item-aware splitting (a chunk never
cuts a table or paragraph mid-way) and token-budget merging, not heading
breadcrumbs.

Also swaps Docling's default table serializer (which flattens every cell as
"row_label = value", repeated per column — very noisy on the wide financial
tables in these filings) for Docling's built-in MarkdownTableSerializer, which
renders proper Markdown tables in the chunk text. Verified to read far more
cleanly and keep numbers aligned with their row labels.

Run from backend/, so app.config/app.database can resolve:

    cd backend
    uv run python -m app.ingest.chunk_and_embed
"""

from __future__ import annotations

import json
from pathlib import Path

from docling_core.transforms.chunker.hierarchical_chunker import ChunkingDocSerializer, ChunkingSerializerProvider
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from docling_core.transforms.serializer.base import BaseDocSerializer
from docling_core.transforms.serializer.markdown import MarkdownTableSerializer
from docling_core.types.doc.document import DoclingDocument
from sqlalchemy import select

from app.config import settings
from app.database.models import DocumentChunk, SourceDocument
from app.database.session import session_maker
from app.embeddings import get_embeddings

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCLING_DIR = REPO_ROOT / "data" / "docling"
MARKDOWN_MANIFEST = REPO_ROOT / "data" / "markdown" / "manifest.json"


class MarkdownTableChunkingSerializerProvider(ChunkingSerializerProvider):
    """Docling's default chunking serializer, but with Markdown-table rendering.

    See module docstring — the default TripletTableSerializer is too noisy on
    these filings' wide financial tables.
    """

    def get_serializer(self, doc: DoclingDocument) -> BaseDocSerializer:
        return ChunkingDocSerializer(doc=doc, table_serializer=MarkdownTableSerializer())


def _docling_json_path(local_path: str) -> Path:
    return DOCLING_DIR / Path(local_path.replace("\\", "/")).with_suffix(".json")


def chunk_and_embed_documents() -> int:
    manifest = json.loads(MARKDOWN_MANIFEST.read_text(encoding="utf-8"))
    json_path_by_accession = {
        filing["accession_number"]: _docling_json_path(filing["local_path"]) for filing in manifest["filings"]
    }

    tokenizer = HuggingFaceTokenizer.from_pretrained(settings.embedding_model_name)
    chunker = HybridChunker(tokenizer=tokenizer, serializer_provider=MarkdownTableChunkingSerializerProvider())
    embeddings = get_embeddings()

    # Select only the columns this script needs — SourceDocument.markdown_content
    # is unused here but can be ~1MB per row, and pulling all 25 in one query
    # was observed breaking the connection (SSL closed / statement timeout).
    with session_maker() as session:
        documents = session.execute(
            select(
                SourceDocument.id,
                SourceDocument.ticker,
                SourceDocument.company_name,
                SourceDocument.filing_type,
                SourceDocument.filing_date,
                SourceDocument.fiscal_year,
                SourceDocument.accession_number,
            )
        ).all()

    total_chunks = 0
    for document in documents:
        # A DB session is opened fresh per document rather than held for the whole
        # run: embed_documents() below is CPU-bound and can take a while per filing,
        # and Supabase's pooler was observed dropping a connection left idle that long.
        with session_maker() as session:
            existing = session.execute(
                select(DocumentChunk.id).where(DocumentChunk.document_id == document.id).limit(1)
            ).first()
        if existing is not None:
            print(f"Skipping {document.ticker} {document.fiscal_year} (already chunked)")
            continue

        docling_doc = DoclingDocument.load_from_json(json_path_by_accession[document.accession_number])
        chunks = [c for c in chunker.chunk(docling_doc) if c.text.strip()]
        vectors = embeddings.embed_documents([c.text for c in chunks])

        with session_maker() as session:
            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
                headings = chunk.meta.headings
                page = next((di.prov[0].page_no for di in chunk.meta.doc_items if di.prov), None)
                session.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        chunk_text=chunk.text,
                        page=page,
                        section=" > ".join(headings) if headings else None,
                        token_count=tokenizer.count_tokens(chunk.text),
                        chunk_metadata={
                            "ticker": document.ticker,
                            "company_name": document.company_name,
                            "filing_type": document.filing_type,
                            "filing_date": document.filing_date.isoformat(),
                            "fiscal_year": document.fiscal_year,
                            "accession_number": document.accession_number,
                            "headings": headings,
                        },
                        embedding=vector,
                    )
                )
            session.commit()

        total_chunks += len(chunks)
        print(f"Chunked {document.ticker} {document.fiscal_year}: {len(chunks)} chunks")

    return total_chunks


if __name__ == "__main__":
    count = chunk_and_embed_documents()
    print(f"Wrote {count} document_chunks row(s)")
