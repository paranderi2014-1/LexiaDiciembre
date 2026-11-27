"""Embeddings con OpenAI (§10). Control explícito de modelo y dimensiones."""

from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import settings

BATCH_SIZE = 64


class EmbeddingsNotConfigured(RuntimeError):
    """Sin OPENAI_API_KEY no se generan vectores."""


class EmbeddingDimensionMismatch(RuntimeError):
    """El modelo devolvió una dimensión distinta a la configurada."""


def _client() -> AsyncOpenAI:
    if not settings.ai_configured:
        raise EmbeddingsNotConfigured("OPENAI_API_KEY no está configurada.")
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def _check(vector: list[float]) -> list[float]:
    if len(vector) != settings.embedding_dimensions:
        raise EmbeddingDimensionMismatch(
            f"{settings.embedding_model} devolvió {len(vector)} dimensiones; "
            f"la columna usa {settings.embedding_dimensions}."
        )
    return vector


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Vectoriza en lotes, conservando el orden de entrada."""
    if not texts:
        return []

    client = _client()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
            dimensions=settings.embedding_dimensions,
        )
        vectors.extend(_check(item.embedding) for item in response.data)
    return vectors


async def embed_query(text: str) -> list[float]:
    return (await embed_texts([text]))[0]
