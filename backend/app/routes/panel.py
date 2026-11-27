"""Panel técnico — monitoreo de Firecrawl, ETL, embeddings y revisiones.

Endpoints de administración para consultar el estado del motor de investigación
jurídica, documentos pendientes de revisión, errores y consumo.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import Identity, require_permission
from app.database.session import get_session
from app.models.catalog import (
    CambioPendiente,
    Documento,
    Fragmento,
    Fuente,
    VersionDocumento,
)
from app.models.ai import Auditoria

router = APIRouter(prefix="/api/panel", tags=["panel técnico"])


@router.get("/resumen")
async def panel_resumen(
    _: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Resumen general del motor de investigación."""
    total_documentos = (await session.execute(select(func.count(Documento.id)))).scalar_one()
    total_fragmentos = (await session.execute(select(func.count(Fragmento.id)))).scalar_one()
    fragmentos_con_embedding = (
        await session.execute(select(func.count(Fragmento.id)).where(Fragmento.embedding.isnot(None)))
    ).scalar_one()
    total_versiones = (await session.execute(select(func.count(VersionDocumento.id)))).scalar_one()
    total_fuentes = (await session.execute(select(func.count(Fuente.id)))).scalar_one()

    return {
        "firecrawl_configurado": bool(getattr(settings, "firecrawl_api_key", None)),
        "ia_configurado": settings.ai_configured,
        "auth_configurado": settings.auth_configured,
        "fuentes": total_fuentes,
        "documentos": total_documentos,
        "fragmentos": total_fragmentos,
        "fragmentos_con_embedding": fragmentos_con_embedding,
        "fragmentos_sin_embedding": total_fragmentos - fragmentos_con_embedding,
        "versiones_historicas": total_versiones,
        "pendientes_revision": (
            await session.execute(
                select(func.count(CambioPendiente.id)).where(CambioPendiente.estado == "pendiente")
            )
        ).scalar_one(),
    }


@router.get("/fuentes-detalle")
async def panel_fuentes(
    _: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Detalle de cada fuente con conteos de documentos y fragmentos."""
    rows = (
        await session.execute(
            select(
                Fuente.codigo,
                Fuente.nombre,
                Fuente.url_base,
                Fuente.activo,
                func.count(Documento.id).label("documentos"),
            )
            .outerjoin(Documento, Documento.fuente_id == Fuente.id)
            .group_by(Fuente.id)
            .order_by(Fuente.codigo)
        )
    ).all()

    return [
        {
            "codigo": row.codigo,
            "nombre": row.nombre,
            "url_base": row.url_base,
            "activo": row.activo,
            "documentos": row.documentos,
        }
        for row in rows
    ]


@router.get("/embeddings")
async def panel_embeddings(
    _: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Estado de indexación de embeddings."""
    total = (await session.execute(select(func.count(Fragmento.id)))).scalar_one()
    con_embedding = (
        await session.execute(select(func.count(Fragmento.id)).where(Fragmento.embedding.isnot(None)))
    ).scalar_one()

    porcentaje = round((con_embedding / total * 100), 2) if total > 0 else 0.0

    return {
        "total_fragmentos": total,
        "con_embedding": con_embedding,
        "sin_embedding": total - con_embedding,
        "porcentaje_indexado": porcentaje,
        "modelo": settings.embedding_model,
        "dimensiones": settings.embedding_dimensions,
    }


@router.get("/versiones")
async def panel_versiones(
    _: Identity = Depends(require_permission("chat.usar")),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Historial de versiones documentales (trazabilidad)."""
    rows = (
        await session.execute(
            select(VersionDocumento, Documento.titulo)
            .join(Documento, Documento.id == VersionDocumento.documento_id)
            .order_by(VersionDocumento.detectada_en.desc())
            .limit(limit)
        )
    ).all()

    return [
        {
            "id": str(version.id),
            "documento_id": str(version.documento_id),
            "documento_titulo": titulo,
            "hash": version.hash[:12],
            "detectada_en": version.detectada_en.isoformat(),
            "metadatos": version.metadatos,
        }
        for version, titulo in rows
    ]


@router.get("/documentos-por-tipo")
async def panel_por_tipo(
    _: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Distribución de documentos por tipo."""
    rows = (
        await session.execute(
            select(Documento.tipo, func.count(Documento.id))
            .group_by(Documento.tipo)
            .order_by(func.count(Documento.id).desc())
        )
    ).all()
    return [{"tipo": tipo, "cantidad": cantidad} for tipo, cantidad in rows]


# --- Cambios pendientes de revisión humana (§18) ----------------------------

@router.get("/cambios-pendientes")
async def panel_cambios_pendientes(
    _: Identity = Depends(require_permission("chat.usar")),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Lista los cambios detectados pendientes de revisión."""
    rows = (
        await session.execute(
            select(CambioPendiente)
            .where(CambioPendiente.estado == "pendiente")
            .order_by(CambioPendiente.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": str(c.id),
            "documento_id": str(c.documento_id) if c.documento_id else None,
            "fuente_codigo": c.fuente_codigo,
            "url": c.url,
            "titulo": c.titulo,
            "hash_anterior": c.hash_anterior[:12] if c.hash_anterior else None,
            "hash_nuevo": c.hash_nuevo[:12],
            "tipo_cambio": c.tipo_cambio,
            "estado": c.estado,
            "acto_sustento": c.acto_sustento,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "metadatos": c.metadatos,
        }
        for c in rows
    ]


@router.post("/cambios-pendientes/{cambio_id}/aprobar")
async def aprobar_cambio(
    cambio_id: uuid.UUID,
    identity: Identity = Depends(require_permission("admin.usuarios")),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Aprueba un cambio pendiente: actualiza el documento vigente y reindexa."""
    from app.jobs.etl import _index_documento
    from app.scrapers.portals import get_scraper
    from app.models.catalog import Articulo, Fragmento as Frag
    from sqlalchemy import delete

    cambio = (
        await session.execute(select(CambioPendiente).where(CambioPendiente.id == cambio_id))
    ).scalar_one_or_none()
    if cambio is None:
        raise HTTPException(status_code=404, detail="Cambio no encontrado.")
    if cambio.estado != "pendiente":
        raise HTTPException(status_code=400, detail=f"El cambio ya fue {cambio.estado}.")

    documento = None
    if cambio.documento_id:
        documento = await session.get(Documento, cambio.documento_id)

    if documento is None:
        # Documento nuevo: crearlo
        fuente = await session.execute(
            select(Fuente).where(Fuente.codigo == cambio.fuente_codigo)
        )
        fuente = fuente.scalar_one_or_none()
        if fuente is None:
            raise HTTPException(status_code=400, detail="Fuente no encontrada.")
        documento = Documento(
            fuente_id=fuente.id,
            tipo="ley",
            titulo=cambio.titulo,
            url_original=cambio.url,
            hash=cambio.hash_nuevo,
            texto=cambio.texto_nuevo,
            estado="vigente",
            metadatos=cambio.metadatos,
        )
        session.add(documento)
        await session.flush()
    else:
        # Guardar versión anterior
        session.add(
            VersionDocumento(
                documento_id=documento.id,
                hash=documento.hash,
                texto=documento.texto,
                metadatos=documento.metadatos,
            )
        )
        documento.hash = cambio.hash_nuevo
        documento.texto = cambio.texto_nuevo
        documento.titulo = cambio.titulo or documento.titulo
        documento.metadatos = cambio.metadatos
        await session.flush()

    # Reindexar
    await session.execute(delete(Frag).where(Frag.documento_id == documento.id))
    await session.execute(delete(Articulo).where(Articulo.documento_id == documento.id))
    await session.flush()
    fragmentos = await _index_documento(session, documento)

    cambio.estado = "aprobado"
    cambio.revisado_por = identity.id
    from datetime import datetime, timezone
    cambio.revisado_en = datetime.now(timezone.utc)

    session.add(
        Auditoria(
            accion="cambio.aprobado",
            usuario_id=identity.id,
            entidad="cambios_pendientes",
            entidad_id=str(cambio.id),
            metadatos={"documento_id": str(documento.id), "fragmentos": fragmentos},
        )
    )
    await session.commit()
    return {"estado": "aprobado", "documento_id": str(documento.id), "fragmentos": fragmentos}


@router.post("/cambios-pendientes/{cambio_id}/rechazar")
async def rechazar_cambio(
    cambio_id: uuid.UUID,
    motivo: str = Body(..., embed=True),
    identity: Identity = Depends(require_permission("admin.usuarios")),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Rechaza un cambio pendiente con un motivo."""
    cambio = (
        await session.execute(select(CambioPendiente).where(CambioPendiente.id == cambio_id))
    ).scalar_one_or_none()
    if cambio is None:
        raise HTTPException(status_code=404, detail="Cambio no encontrado.")
    if cambio.estado != "pendiente":
        raise HTTPException(status_code=400, detail=f"El cambio ya fue {cambio.estado}.")

    cambio.estado = "rechazado"
    cambio.revisado_por = identity.id
    cambio.motivo_revision = motivo
    from datetime import datetime, timezone
    cambio.revisado_en = datetime.now(timezone.utc)

    session.add(
        Auditoria(
            accion="cambio.rechazado",
            usuario_id=identity.id,
            entidad="cambios_pendientes",
            entidad_id=str(cambio.id),
            metadatos={"motivo": motivo},
        )
    )
    await session.commit()
    return {"estado": "rechazado", "motivo": motivo}
