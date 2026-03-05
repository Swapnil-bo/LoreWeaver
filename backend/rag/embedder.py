import asyncio

from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _embed_sync(text: str) -> list[float]:
    """Synchronous inner — never call directly in async context."""
    return get_embedder().encode(text, normalize_embeddings=True).tolist()


async def embed(text: str) -> list[float]:
    """
    Async embed — always use this in FastAPI/WebSocket routes.
    Offloads CPU-bound matrix multiply to thread pool.
    Event loop stays free during the 100-200ms computation.
    """
    return await asyncio.to_thread(_embed_sync, text)
