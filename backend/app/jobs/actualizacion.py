"""Actualización automática del Derecho paraguayo (§19)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.etl import run_source
from app.models.ai import Auditoria, Configuracion
from app.models.catalog import Fuente

REPORT_KEY = "ultima_actualizacion"


async def actualizar_todo(session: AsyncSession, limite_por_fuente: int | None = None) -> dict:
    """Recorre las fuentes activas y deja un informe de ejecución."""
    codigos = (
        await session.execute(select(Fuente.codigo).where(Fuente.activo.is_(True)))
    ).scalars().all()

    informes = []
    for codigo in codigos:
        report = await run_source(session, codigo, limite=limite_por_fuente)
        informes.append(report.as_dict())

    resumen = {
        "ejecutado_en": datetime.now(timezone.utc).isoformat(),
        "fuentes": informes,
        "errores": sum(len(item["errores"]) for item in informes),
    }

    existente = await session.get(Configuracion, REPORT_KEY)
    if existente is None:
        session.add(Configuracion(clave=REPORT_KEY, valor=resumen))
    else:
        existente.valor = resumen

    session.add(
        Auditoria(
            accion="actualizacion.automatica",
            entidad="fuentes",
            metadatos=resumen,
        )
    )
    await session.commit()
    return resumen
