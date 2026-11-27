"""Caché de respuestas en Redis con invalidación por versión del índice (§14)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import redis.asyncio as redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.catalog import Documento
from app.utils.text import normalize_text


class _Cache:
    def __init__(self, url: str) -> None:
        self._url = url
        self._client: redis.Redis | None = None

    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self._url, encoding="utf-8", decode_responses=True)
        return self._client

    async def ping(self) -> bool:
        return bool(await self.client().ping())

    async def get(self, key: str) -> dict[str, Any] | None:
        raw = await self.client().get(key)
        return json.loads(raw) if raw else None

    async def set(self, key: str, value: dict[str, Any], ttl: int | None = None) -> None:
        await self.client().set(key, json.dumps(value), ex=ttl or settings.cache_ttl_seconds)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


cache = _Cache(settings.redis_url)


async def indice_version(session: AsyncSession) -> str:
    """Huella del estado del corpus: cambia cuando se indexan o versionan documentos."""
    row = (
        await session.execute(
            select(func.count(Documento.id), func.max(Documento.updated_at))
        )
    ).one()
    total, ultima = row
    return hashlib.sha1(f"{total}|{ultima}".encode("utf-8")).hexdigest()[:16]


def question_key(pregunta: str, version: str) -> str:
    digest = hashlib.sha256(normalize_text(pregunta).lower().encode("utf-8")).hexdigest()
    return f"lexia:respuesta:{version}:{digest}"
