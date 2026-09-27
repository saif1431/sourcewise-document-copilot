from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    """Local sentence-transformers model, shared by ingestion and retrieval.

    Cached because loading the model is expensive — both `app.ingest` scripts
    and `app.retrieval` need the exact same model so query and chunk vectors
    land in the same embedding space.
    """
    return HuggingFaceEmbeddings(model_name=settings.embedding_model_name)
