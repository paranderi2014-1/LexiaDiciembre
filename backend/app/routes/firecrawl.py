"""Endpoints de Firecrawl — motor de investigación documental (Plan Maestro §8).

Todas las operaciones pasan por el backend; la clave nunca se expone.
Requieren permiso `chat.usar` o `admin.firecrawl`.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import Identity, require_permission
from app.services import firecrawl
from app.services.firecrawl import FirecrawlNotConfigured

router = APIRouter(prefix="/api/firecrawl", tags=["firecrawl"])


class MapRequest(BaseModel):
    url: str = Field(..., description="URL del sitio oficial a mapear")
    limit: int = Field(default=50, ge=1, le=500)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


class ScrapeRequest(BaseModel):
    url: str = Field(..., description="URL oficial a extraer")


class CrawlRequest(BaseModel):
    url: str = Field(..., description="URL raíz de la sección a recorrer")
    limit: int = Field(default=20, ge=1, le=100)
    max_depth: int = Field(default=2, ge=1, le=5)


class ExtractRequest(BaseModel):
    url: str = Field(..., description="URL oficial a extraer")
    schema: dict = Field(..., description="Esquema JSON de extracción")


def _handle_configured(exc: FirecrawlNotConfigured) -> None:
    raise HTTPException(status_code=503, detail=str(exc))


@router.get("/status")
async def firecrawl_status(
    _: Identity = Depends(require_permission("chat.usar")),
) -> dict:
    """Verifica si Firecrawl está configurado."""
    key = getattr(__import__("app.core.config", fromlist=["settings"]).settings, "firecrawl_api_key", None)
    return {"configured": bool(key)}


@router.post("/map")
async def map_site(
    payload: MapRequest,
    _: Identity = Depends(require_permission("chat.usar")),
) -> dict:
    try:
        result = await firecrawl.firecrawl_map(payload.url, limit=payload.limit)
    except FirecrawlNotConfigured as exc:
        _handle_configured(exc)
        return {}  # unreachable
    except firecrawl.FirecrawlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.as_dict()


@router.post("/search")
async def search_docs(
    payload: SearchRequest,
    _: Identity = Depends(require_permission("chat.usar")),
) -> dict:
    try:
        result = await firecrawl.firecrawl_search(payload.query, limit=payload.limit)
    except FirecrawlNotConfigured as exc:
        _handle_configured(exc)
        return {}
    return result.as_dict()


@router.post("/scrape")
async def scrape_url(
    payload: ScrapeRequest,
    _: Identity = Depends(require_permission("chat.usar")),
) -> dict:
    try:
        result = await firecrawl.firecrawl_scrape(payload.url)
    except FirecrawlNotConfigured as exc:
        _handle_configured(exc)
        return {}
    except firecrawl.FirecrawlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.as_dict()


@router.post("/crawl")
async def crawl_site(
    payload: CrawlRequest,
    _: Identity = Depends(require_permission("admin.firecrawl")),
) -> dict:
    try:
        result = await firecrawl.firecrawl_crawl(payload.url, limit=payload.limit, max_depth=payload.max_depth)
    except FirecrawlNotConfigured as exc:
        _handle_configured(exc)
        return {}
    except firecrawl.FirecrawlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.as_dict()


@router.post("/extract")
async def extract_json(
    payload: ExtractRequest,
    _: Identity = Depends(require_permission("admin.firecrawl")),
) -> dict:
    try:
        result = await firecrawl.firecrawl_extract(payload.url, payload.schema)
    except FirecrawlNotConfigured as exc:
        _handle_configured(exc)
        return {}
    except firecrawl.FirecrawlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.as_dict()
