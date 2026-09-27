"""Real query against the ingested corpus. Requires live Supabase credentials
(same DB the ingestion pipeline in app/ingest/ wrote to) and downloads the
embedding model on first run — run explicitly with `-m integration`.
"""

import pytest

from app.retrieval.retriever import retrieve

pytestmark = pytest.mark.integration


def test_retrieve_finds_apple_iphone_revenue_passage() -> None:
    passages = retrieve("Apple iPhone net sales by product category", top_k=5)

    assert len(passages) == 5
    assert any(p.ticker == "AAPL" for p in passages)
    assert any("iPhone" in p.chunk_text for p in passages)


def test_retrieve_attaches_neighbor_context() -> None:
    passages = retrieve("Amazon AWS operating income", top_k=5)

    # At least one hit should have a neighbor on either side — passages this
    # deep into a filing are virtually never the very first/last chunk.
    assert any(p.context_before is not None for p in passages)
    assert any(p.context_after is not None for p in passages)


def test_retrieve_respects_top_k() -> None:
    passages = retrieve("Microsoft Azure cloud infrastructure", top_k=3)
    assert len(passages) == 3
