"""query -> fused ranked passages + neighbor chunks.

One retrieval call: embed the query, run semantic + full-text search over
`document_chunks`, fuse the two rankings with RRF, then attach each result's
immediate neighbor chunks (same document, adjacent chunk_index) so the caller
has enough surrounding context to ground an answer, not just an isolated
snippet.
"""

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import DocumentChunk
from app.database.session import session_maker
from app.embeddings import get_embeddings
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.queries import full_text_search, semantic_search

# Candidate pool size per strategy, fused down to top_k — wider than top_k so
# RRF has more than one strategy's worth of signal to combine.
SEMANTIC_CANDIDATES = 20
FULL_TEXT_CANDIDATES = 20
DEFAULT_TOP_K = 8


@dataclass
class RetrievedPassage:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_text: str
    ticker: str
    company_name: str
    filing_type: str
    filing_date: date
    fiscal_year: int
    accession_number: str
    # `page`/`section` are null for most chunks in this corpus — SEC EDGAR 10-K
    # HTML has no page pagination or semantic headings (see app/ingest/chunk_and_embed.py).
    page: int | None
    section: str | None
    score: float
    context_before: str | None
    context_after: str | None


def retrieve(query: str, *, top_k: int = DEFAULT_TOP_K) -> list[RetrievedPassage]:
    query_embedding = get_embeddings().embed_query(query)

    with session_maker() as session:
        semantic_hits = semantic_search(session, query_embedding, limit=SEMANTIC_CANDIDATES)
        full_text_hits = full_text_search(session, query, limit=FULL_TEXT_CANDIDATES)

        chunks_by_id = {chunk.id: chunk for chunk in (*semantic_hits, *full_text_hits)}
        fused = reciprocal_rank_fusion(
            [
                [chunk.id for chunk in semantic_hits],
                [chunk.id for chunk in full_text_hits],
            ]
        )

        return [_to_passage(chunks_by_id[chunk_id], score, session) for chunk_id, score in fused[:top_k]]


def _to_passage(chunk: DocumentChunk, score: float, session: Session) -> RetrievedPassage:
    document = chunk.document
    context_before, context_after = _neighbor_texts(session, chunk)
    return RetrievedPassage(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        chunk_text=chunk.chunk_text,
        ticker=document.ticker,
        company_name=document.company_name,
        filing_type=document.filing_type,
        filing_date=document.filing_date,
        fiscal_year=document.fiscal_year,
        accession_number=document.accession_number,
        page=chunk.page,
        section=chunk.section,
        score=score,
        context_before=context_before,
        context_after=context_after,
    )


def _neighbor_texts(session: Session, chunk: DocumentChunk) -> tuple[str | None, str | None]:
    neighbors = session.execute(
        select(DocumentChunk.chunk_index, DocumentChunk.chunk_text).where(
            DocumentChunk.document_id == chunk.document_id,
            DocumentChunk.chunk_index.in_([chunk.chunk_index - 1, chunk.chunk_index + 1]),
        )
    ).all()
    before = next((text for index, text in neighbors if index == chunk.chunk_index - 1), None)
    after = next((text for index, text in neighbors if index == chunk.chunk_index + 1), None)
    return before, after
