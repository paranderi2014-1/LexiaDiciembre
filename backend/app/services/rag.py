"""Motor RAG: recuperación híbrida, respuesta fundamentada, citas y auditoría (§12)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import Identity
from app.models.ai import Consulta, EstadisticaBusqueda, RespuestaIA
from app.services import auditoria, citaciones, prompts
from app.services.cache import cache, indice_version, question_key
from app.services.embeddings import EmbeddingsNotConfigured, embed_query
from app.services.search import RetrievedFragment, hybrid_search


class ChatNotConfigured(RuntimeError):
    """Sin modelo de chat configurado no se generan respuestas."""


@dataclass(slots=True)
class RAGResult:
    contenido: str
    fuentes: list[dict] = field(default_factory=list)
    fundamento_suficiente: bool = False
    modelo: str = ""
    desde_cache: bool = False
    latencia_ms: int = 0
    fragmentos: list[RetrievedFragment] = field(default_factory=list)
    consulta_id: str | None = None


async def _ask_model(
    pregunta: str,
    fragments: list[RetrievedFragment],
    *,
    fuero: str = "General",
    analysis_mode: str = "WEB_SEARCH",
) -> str:
    if not settings.ai_configured:
        raise ChatNotConfigured("OPENAI_API_KEY no está configurada para el modelo de chat.")

    client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    response = await client.chat.completions.create(
        model=settings.chat_model,
        temperature=0,
        messages=[
            {"role": "system", "content": prompts.SYSTEM_PROMPT},
            {"role": "user", "content": prompts.build_user_prompt(pregunta, fragments, fuero=fuero, analysis_mode=analysis_mode)},
        ],
    )
    return response.choices[0].message.content or ""


async def answer(
    session: AsyncSession,
    identity: Identity,
    pregunta: str,
    *,
    canal: str = "web",
    fuero: str = "General",
    analysis_mode: str = "WEB_SEARCH",
) -> RAGResult:
    started = time.perf_counter()
    version = await indice_version(session)
    key = question_key(pregunta, version)

    consulta = Consulta(usuario_id=identity.id, pregunta=pregunta, canal=canal)
    session.add(consulta)
    await session.flush()

    try:
        cached = await cache.get(key)
    except Exception:  # noqa: BLE001 - Redis caído no debe impedir responder
        cached = None

    if cached:
        consulta.desde_cache = True
        respuesta = RespuestaIA(
            consulta_id=consulta.id,
            contenido=cached["contenido"],
            modelo=cached["modelo"],
            fundamento_suficiente=cached["fundamento_suficiente"],
            fuentes=cached["fuentes"],
            latencia_ms=int((time.perf_counter() - started) * 1000),
        )
        session.add(respuesta)
        auditoria.registrar(
            session,
            "chat.cache",
            usuario_id=identity.id,
            entidad="consultas",
            entidad_id=str(consulta.id),
            metadatos={"indice_version": version},
        )
        await session.commit()
        return RAGResult(
            contenido=cached["contenido"],
            fuentes=cached["fuentes"],
            fundamento_suficiente=cached["fundamento_suficiente"],
            modelo=cached["modelo"],
            desde_cache=True,
            latencia_ms=respuesta.latencia_ms or 0,
            consulta_id=str(consulta.id),
        )

    vector: list[float] | None = None
    try:
        vector = await embed_query(pregunta)
    except EmbeddingsNotConfigured:
        vector = None

    fragments = await hybrid_search(session, pregunta, vector)
    session.add(
        EstadisticaBusqueda(consulta_id=consulta.id, termino=pregunta[:400], resultados=len(fragments))
    )

    if not fragments:
        resultado = RAGResult(
            contenido=citaciones.CONTINGENCIA,
            fundamento_suficiente=False,
            modelo="sin-recuperacion",
            latencia_ms=int((time.perf_counter() - started) * 1000),
            consulta_id=str(consulta.id),
        )
    else:
        contenido = await _ask_model(pregunta, fragments, fuero=fuero, analysis_mode=analysis_mode)
        validado = citaciones.validate_citations(contenido, fragments)
        resultado = RAGResult(
            contenido=validado.contenido,
            fuentes=validado.fuentes,
            fundamento_suficiente=validado.fundamento_suficiente,
            modelo=settings.chat_model,
            latencia_ms=int((time.perf_counter() - started) * 1000),
            fragmentos=fragments,
            consulta_id=str(consulta.id),
        )

    respuesta = RespuestaIA(
        consulta_id=consulta.id,
        contenido=resultado.contenido,
        modelo=resultado.modelo,
        fundamento_suficiente=resultado.fundamento_suficiente,
        fuentes=resultado.fuentes,
        latencia_ms=resultado.latencia_ms,
    )
    session.add(respuesta)
    await session.flush()

    auditoria.registrar(
        session,
        "chat.consulta",
        usuario_id=identity.id,
        entidad="consultas",
        entidad_id=str(consulta.id),
        metadatos={
            "fragmentos": len(fragments),
            "fundamento_suficiente": resultado.fundamento_suficiente,
            "indice_version": version,
        },
    )

    if resultado.fundamento_suficiente:
        try:
            await cache.set(
                key,
                {
                    "contenido": resultado.contenido,
                    "fuentes": resultado.fuentes,
                    "fundamento_suficiente": resultado.fundamento_suficiente,
                    "modelo": resultado.modelo,
                },
            )
        except Exception:  # noqa: BLE001 - la caché es una optimización
            pass

    await session.commit()
    return resultado
