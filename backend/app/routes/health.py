"""Estado de la API y sus dependencias (§13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_session
from app.schemas.api import HealthOut
from app.services.cache import cache

router = APIRouter(prefix="/api", tags=["salud"])


@router.get("/health", response_model=HealthOut)
async def health(session: AsyncSession = Depends(get_session)) -> HealthOut:
    dependencias: dict[str, str] = {}

    try:
        await session.execute(text("SELECT 1"))
        dependencias["postgres"] = "ok"
    except Exception as exc:  # noqa: BLE001 - el estado se informa, no se oculta
        dependencias["postgres"] = f"error: {type(exc).__name__}"

    try:
        dependencias["redis"] = "ok" if await cache.ping() else "error"
    except Exception as exc:  # noqa: BLE001
        dependencias["redis"] = f"error: {type(exc).__name__}"

    dependencias["firebase"] = "ok" if settings.auth_configured else "no_configurado"
    dependencias["openai"] = "ok" if settings.ai_configured else "no_configurado"

    degradado = any(not valor.startswith("ok") for valor in dependencias.values())
    return HealthOut(
        status="degradado" if degradado else "ok",
        version="1.0.0",
        dependencias=dependencias,
        configuracion={
            "autenticacion": settings.auth_configured,
            "ia": settings.ai_configured,
        },
    )
