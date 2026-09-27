from sqlalchemy.dialects import postgresql

from app.retrieval.queries import build_full_text_search_stmt, build_semantic_search_stmt


def _compile(stmt):
    # Postgres dialect specifically: this app only ever targets Postgres, and
    # generic SQL compilation doesn't know pgvector's `<=>` operator context.
    return stmt.compile(dialect=postgresql.dialect())


def _sql(stmt) -> str:
    return str(_compile(stmt))


def _params(stmt) -> dict:
    # REGCONFIG (websearch_to_tsquery's language arg) has no literal
    # renderer in SQLAlchemy, so bound values are checked here instead of
    # via literal_binds in the compiled SQL text.
    return _compile(stmt).params


def test_semantic_search_orders_by_cosine_distance() -> None:
    stmt = build_semantic_search_stmt([0.1, 0.2, 0.3], limit=5)
    assert "document_chunks.embedding <=>" in _sql(stmt)
    assert "ORDER BY" in _sql(stmt)


def test_semantic_search_limit_is_bound() -> None:
    assert 5 in _params(build_semantic_search_stmt([0.1, 0.2, 0.3], limit=5)).values()


def test_semantic_search_eager_loads_document() -> None:
    assert "JOIN source_documents" in _sql(build_semantic_search_stmt([0.1, 0.2, 0.3], limit=5))


def test_full_text_search_matches_search_vector() -> None:
    stmt = build_full_text_search_stmt("apple iphone revenue", limit=10)
    assert "document_chunks.search_vector @@ websearch_to_tsquery" in _sql(stmt)


def test_full_text_search_query_text_is_bound() -> None:
    params = _params(build_full_text_search_stmt("apple iphone revenue", limit=10))
    assert "apple iphone revenue" in params.values()
    assert "english" in params.values()


def test_full_text_search_orders_by_ts_rank_descending() -> None:
    sql = _sql(build_full_text_search_stmt("apple iphone revenue", limit=10))
    assert "ORDER BY ts_rank" in sql
    assert "DESC" in sql


def test_full_text_search_eager_loads_document() -> None:
    assert "JOIN source_documents" in _sql(build_full_text_search_stmt("apple iphone revenue", limit=10))
