"""Servicio Firecrawl — motor de investigación, extracción y seguimiento jurídico.

Pasa todas las operaciones por el backend; la clave FIRECRAWL_API_KEY nunca sale
del servidor. Solo se permiten dominios oficiales paraguayos.

Operaciones soportadas (API v2):
- map:    descubrir páginas de un sitio oficial
- search: localizar documentos y publicaciones
- scrape: extraer contenido de una URL
- crawl:  recorrer una sección delimitada
- json:   extraer datos normativos estructurados
- monitor: registrar y consultar tareas de seguimiento de cambios
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

from app.core.config import settings

FIRECRAWL_BASE = "https://api.firecrawl.dev/v2"
LEGAL_ALLOWED_HOSTS = ["bacn.gov.py", "pj.gov.py", "csj.gov.py", "apps.csj.gov.py"]


class FirecrawlNotConfigured(RuntimeError):
    pass


class FirecrawlError(RuntimeError):
    pass


def _api_key() -> str:
    key = getattr(settings, "firecrawl_api_key", None)
    if not key:
        raise FirecrawlNotConfigured("FIRECRAWL_API_KEY no está configurada en el servidor.")
    return key


def _check_url(url: str) -> None:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise FirecrawlError(f"URL no permitida (debe ser HTTPS oficial): {url}")
    host = parsed.hostname.lower()
    if not any(host == h or host.endswith(f".{h}") for h in LEGAL_ALLOWED_HOSTS):
        raise FirecrawlError(f"Dominio no autorizado: {host}. Solo fuentes oficiales paraguayas.")


@dataclass(slots=True)
class FirecrawlResult:
    success: bool
    data: dict | list = field(default_factory=dict)
    error: str | None = None
    credits_used: int = 0
    timestamp: str = ""

    def as_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "credits_used": self.credits_used,
            "timestamp": self.timestamp,
        }


async def _post(path: str, body: dict, *, timeout: float = 45.0) -> FirecrawlResult:
    key = _api_key()
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{FIRECRAWL_BASE}/{path}",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
    now = datetime.now(timezone.utc).isoformat()
    if not response.ok:
        return FirecrawlResult(
            success=False,
            error=f"Firecrawl rechazó la solicitud ({response.status_code}): {response.text[:500]}",
            timestamp=now,
        )
    payload: dict = response.json()
    return FirecrawlResult(
        success=payload.get("success", True),
        data=payload.get("data", payload),
        credits_used=int(payload.get("creditsUsed", 0)),
        timestamp=now,
    )


async def firecrawl_map(url: str, *, limit: int = 50) -> FirecrawlResult:
    """Descubre páginas de un sitio oficial."""
    _check_url(url)
    return await _post("map", {"url": url, "limit": limit, "includeSubdomains": False})


async def firecrawl_search(query: str, *, limit: int = 5) -> FirecrawlResult:
    """Busca documentos en dominios oficiales paraguayos."""
    return await _post(
        "search",
        {
            "query": query,
            "limit": limit,
            "sources": [{"type": "web"}],
            "includeDomains": LEGAL_ALLOWED_HOSTS,
            "scrapeOptions": {"formats": ["markdown"], "onlyMainContent": True},
        },
    )


async def firecrawl_scrape(url: str) -> FirecrawlResult:
    """Extrae contenido markdown de una URL oficial."""
    _check_url(url)
    return await _post("scrape", {"url": url, "formats": ["markdown"], "onlyMainContent": True})


async def firecrawl_crawl(url: str, *, limit: int = 20, max_depth: int = 2) -> FirecrawlResult:
    """Recorre una sección delimitada de un sitio oficial."""
    _check_url(url)
    return await _post(
        "crawl",
        {
            "url": url,
            "limit": limit,
            "scrapeOptions": {"formats": ["markdown"], "onlyMainContent": True},
            "crawlerOptions": {"maxDepth": max_depth, "includes": [f"*{url}/*"]},
        },
    )


async def firecrawl_extract(url: str, schema: dict) -> FirecrawlResult:
    """Extrae datos normativos estructurados (JSON) de una URL oficial."""
    _check_url(url)
    return await _post(
        "extract",
        {"urls": [url], "prompt": "Extrae datos normativos estructurados", "schema": schema},
    )
