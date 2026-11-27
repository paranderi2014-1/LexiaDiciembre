"""Registro de auditoría (§14)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import Auditoria


def registrar(
    session: AsyncSession,
    accion: str,
    *,
    usuario_id: uuid.UUID | None = None,
    entidad: str | None = None,
    entidad_id: str | None = None,
    metadatos: dict[str, Any] | None = None,
) -> Auditoria:
    """Agrega la entrada a la sesión; el commit lo decide el caso de uso."""
    entry = Auditoria(
        usuario_id=usuario_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        metadatos=metadatos or {},
    )
    session.add(entry)
    return entry
