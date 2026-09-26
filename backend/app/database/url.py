def normalize_database_url(url: str) -> str:
    """postgresql:// -> postgresql+psycopg://

    We install psycopg (v3), not psycopg2, so the dialect+driver must be
    explicit or SQLAlchemy looks for psycopg2. Shared by the async runtime
    engine and Alembic so they can't drift apart on driver naming.
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url
