"""Documentos, leyes, artículos y jurisprudencia (§13)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_session
from app.models.catalog import Articulo, Documento, Fuente
from app.schemas.api import (
    ArticuloOut,
    BusquedaOut,
    DocumentoDetalleOut,
    DocumentoOut,
    DocumentoPagina,
    FragmentoOut,
    FuenteEstadoOut,
)
from app.services.embeddings import EmbeddingsNotConfigured, embed_query
from app.services.search import hybrid_search

router = APIRouter(prefix="/api", tags=["documentos"])

LEY = "ley"
JURISPRUDENCIA = "jurisprudencia"


@router.get("/fuentes", response_model=list[FuenteEstadoOut])
async def list_fuentes(session: AsyncSession = Depends(get_session)) -> list[FuenteEstadoOut]:
    """Fuentes oficiales indexadas con su conteo de documentos (lectura pública)."""
    rows = (
        await session.execute(
            select(Fuente, func.count(Documento.id))
            .outerjoin(Documento, Documento.fuente_id == Fuente.id)
            .group_by(Fuente.id)
            .order_by(Fuente.codigo)
        )
    ).all()
    return [
        FuenteEstadoOut(
            codigo=fuente.codigo,
            nombre=fuente.nombre,
            url_base=fuente.url_base,
            activo=fuente.activo,
            documentos=total,
        )
        for fuente, total in rows
    ]


async def _paginate(
    session: AsyncSession,
    *,
    tipo: str | None,
    numero: str | None,
    anio: int | None,
    q: str | None,
    limit: int,
    offset: int,
) -> DocumentoPagina:
    conditions = []
    if tipo:
        conditions.append(Documento.tipo == tipo)
    if numero:
        conditions.append(Documento.numero.ilike(f"%{numero}%"))
    if anio:
        conditions.append(func.extract("year", Documento.fecha_publicacion) == anio)
    if q:
        like = f"%{q}%"
        conditions.append(or_(Documento.titulo.ilike(like), Documento.texto.ilike(like)))

    base = select(Documento)
    count = select(func.count(Documento.id))
    if conditions:
        base = base.where(*conditions)
        count = count.where(*conditions)

    total = int((await session.execute(count)).scalar_one())
    rows = (
        await session.execute(
            base.order_by(Documento.fecha_publicacion.desc().nullslast()).limit(limit).offset(offset)
        )
    ).scalars().all()

    return DocumentoPagina(
        total=total,
        limite=limit,
        desplazamiento=offset,
        items=[DocumentoOut.model_validate(row) for row in rows],
    )


@router.get("/documentos", response_model=DocumentoPagina)
async def list_documentos(
    tipo: str | None = Query(default=None, description="ley | jurisprudencia | doctrina"),
    numero: str | None = None,
    anio: int | None = None,
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> DocumentoPagina:
    return await _paginate(
        session, tipo=tipo, numero=numero, anio=anio, q=q, limit=limit, offset=offset
    )


@router.get("/leyes", response_model=DocumentoPagina)
async def list_leyes(
    numero: str | None = None,
    anio: int | None = None,
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> DocumentoPagina:
    return await _paginate(
        session, tipo=LEY, numero=numero, anio=anio, q=q, limit=limit, offset=offset
    )


@router.get("/documentos/{documento_id}", response_model=DocumentoDetalleOut)
async def get_documento(
    documento_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> DocumentoDetalleOut:
    row = (
        await session.execute(
            select(Documento)
            .options(selectinload(Documento.articulos), selectinload(Documento.fuente))
            .where(Documento.id == documento_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    detalle = DocumentoDetalleOut.model_validate(row)
    detalle.articulos = [
        ArticuloOut.model_validate(a) for a in sorted(row.articulos, key=lambda a: a.orden)
    ]
    return detalle


@router.get("/articulos", response_model=list[ArticuloOut])
async def search_articulos(
    q: str | None = None,
    numero: str | None = None,
    documento_id: uuid.UUID | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[ArticuloOut]:
    stmt = select(Articulo)
    if documento_id:
        stmt = stmt.where(Articulo.documento_id == documento_id)
    if numero:
        stmt = stmt.where(Articulo.numero.ilike(f"%{numero}%"))
    if q:
        stmt = stmt.where(
            or_(Articulo.texto.ilike(f"%{q}%"), Articulo.titulo.ilike(f"%{q}%"))
        )
    rows = (await session.execute(stmt.order_by(Articulo.orden).limit(limit))).scalars().all()
    return [ArticuloOut.model_validate(row) for row in rows]


@router.get("/jurisprudencia", response_model=BusquedaOut)
async def search_jurisprudencia(
    q: str = Query(min_length=2),
    anio: int | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> BusquedaOut:
    vector = None
    try:
        vector = await embed_query(q)
    except EmbeddingsNotConfigured:
        vector = None

    fragments = await hybrid_search(
        session, q, vector, tipo=JURISPRUDENCIA, anio=anio, limit=limit
    )
    return BusquedaOut(
        termino=q,
        total=len(fragments),
        modo_vectorial=vector is not None,
        items=[
            FragmentoOut(
                fragmento_id=f.fragmento_id,
                documento_id=f.documento_id,
                titulo=f.documento_titulo,
                tipo=f.documento_tipo,
                numero=f.documento_numero,
                articulo=f.articulo_numero,
                fuente=f.fuente,
                url=f.url_original,
                score=round(f.score, 4),
                texto=f.texto,
            )
            for f in fragments
        ],
    )


@router.get("/jurisprudencia/{documento_id}", response_model=DocumentoDetalleOut)
async def get_jurisprudencia(
    documento_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> DocumentoDetalleOut:
    row = (
        await session.execute(
            select(Documento)
            .options(selectinload(Documento.articulos), selectinload(Documento.fuente))
            .where(Documento.id == documento_id, Documento.tipo == JURISPRUDENCIA)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Sentencia no encontrada.")
    detalle = DocumentoDetalleOut.model_validate(row)
    detalle.articulos = [ArticuloOut.model_validate(a) for a in row.articulos]
    return detalle
