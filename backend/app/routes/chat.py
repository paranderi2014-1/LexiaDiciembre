"""Consulta jurídica con RAG e historial (§13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Identity, get_current_identity, require_permission
from app.database.session import get_session
from app.models.ai import Consulta, RespuestaIA
from app.schemas.api import ChatRequest, ChatResponse, ConsultaOut
from app.services import rag

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    identity: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    try:
        result = await rag.answer(session, identity, payload.pregunta, canal=payload.canal)
    except rag.ChatNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(
        consulta_id=result.consulta_id or "",
        respuesta=result.contenido,
        fuentes=result.fuentes,
        fundamento_suficiente=result.fundamento_suficiente,
        modelo=result.modelo,
        desde_cache=result.desde_cache,
        latencia_ms=result.latencia_ms,
    )


@router.get("/consultas", response_model=list[ConsultaOut])
async def list_consultas(
    identity: Identity = Depends(get_current_identity),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[ConsultaOut]:
    rows = (
        await session.execute(
            select(Consulta, RespuestaIA)
            .outerjoin(RespuestaIA, RespuestaIA.consulta_id == Consulta.id)
            .where(Consulta.usuario_id == identity.id)
            .order_by(Consulta.creada_en.desc())
            .limit(limit)
        )
    ).all()

    return [
        ConsultaOut(
            id=consulta.id,
            pregunta=consulta.pregunta,
            canal=consulta.canal,
            desde_cache=consulta.desde_cache,
            creada_en=consulta.creada_en,
            respuesta=respuesta.contenido if respuesta else None,
            fundamento_suficiente=respuesta.fundamento_suficiente if respuesta else None,
        )
        for consulta, respuesta in rows
    ]
