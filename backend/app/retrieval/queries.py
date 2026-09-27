"""The two bounded retrieval queries: pgvector semantic search and Postgres
full-text search over `document_chunks`.

Statement-building is split from execution so the query shape itself
(operators, ordering, eager-loading) is unit-testable without a database —
see tests/retrieval/test_queries.py.
"""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.database.models import DocumentChunk


def build_semantic_search_stmt(query_embedding: list[float], *, limit: int) -> Select:
    """Nearest chunks by cosine distance between `embedding` and the query vector."""
    return (
        select(DocumentChunk)
        .options(joinedload(DocumentChunk.document))
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )


def build_full_text_search_stmt(query_text: str, *, limit: int) -> Select:
    """Chunks whose `search_vector` matches the query, ranked by `ts_rank`.

    `websearch_to_tsquery` accepts plain analyst phrasing (quotes, `-exclude`)
    instead of requiring Postgres tsquery syntax.
    """
    tsquery = func.websearch_to_tsquery("english", query_text)
    return (
        select(DocumentChunk)
        .options(joinedload(DocumentChunk.document))
        .where(DocumentChunk.search_vector.op("@@")(tsquery))
        .order_by(func.ts_rank(DocumentChunk.search_vector, tsquery).desc())
        .limit(limit)
    )


def semantic_search(session: Session, query_embedding: list[float], *, limit: int) -> list[DocumentChunk]:
    return list(session.execute(build_semantic_search_stmt(query_embedding, limit=limit)).scalars())


def full_text_search(session: Session, query_text: str, *, limit: int) -> list[DocumentChunk]:
    return list(session.execute(build_full_text_search_stmt(query_text, limit=limit)).scalars())
