"""Endpoints de análisis jurídico asistido por IA (Plan Maestro §12.2).

Adaptados de LegalAiService.kt y DespachoViewModel.kt:
- Revisión de contratos con clasificación de riesgos
- Comparación de documentos con diff
- Generación de escritos desde plantillas
- Preparación de audiencias
- Extracción de hechos de expedientes
- Búsqueda de casos análogos
- Triaje de clientes
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import Identity, require_permission
from app.database.session import get_session
from app.schemas.analysis import (
    AnalogousCaseRequest,
    AnalogousCaseResult,
    CaseExtractionRequest,
    CaseExtractionReport,
    ClientLeadTriage,
    ClientLeadTriageRequest,
    ContractReviewReport,
    ContractReviewRequest,
    DocumentComparisonReport,
    DocumentComparisonRequest,
    DraftRequest,
    GeneratedDraftPayload,
    HearingPrepReport,
    HearingPrepRequest,
)
from app.services import analysis_prompts, auditoria
from app.services.search import hybrid_search

router = APIRouter(prefix="/api/analysis", tags=["análisis"])


@dataclass(slots=True)
class _AnalysisContext:
    """Fragmentos RAG recuperados para enriquecer el prompt."""


async def _get_model_response(system_prompt: str, user_prompt: str) -> str:
    """Llama al modelo de chat con prompt del sistema y del usuario."""
    if not settings.ai_configured:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY no está configurada para el análisis jurídico.",
        )
    client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    response = await client.chat.completions.create(
        model=settings.chat_model,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


async def _get_text_response(system_prompt: str, user_prompt: str) -> str:
    """Llama al modelo de chat sin formato JSON (para análisis de texto libre)."""
    if not settings.ai_configured:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY no está configurada para el análisis jurídico.",
        )
    client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    response = await client.chat.completions.create(
        model=settings.chat_model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


@router.post("/contract-review", response_model=ContractReviewReport)
async def review_contract(
    payload: ContractReviewRequest,
    identity: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> ContractReviewReport:
    """Revisa un contrato y devuelve riesgos clasificados."""
    prompt = analysis_prompts.contract_review_prompt(payload.contract_text, payload.fuero)
    raw = await _get_model_response(analysis_prompts.ACADEMIC_SYSTEM_PROMPT, prompt)
    try:
        data = analysis_prompts.parse_json_response(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="El modelo devolvió una respuesta no parseable.")
    auditoria.registrar(
        session,
        "analisis.contrato",
        usuario_id=identity.id,
        entidad="analisis",
        metadatos={"fuero": payload.fuero, "riesgo": data.get("overallRiskLevel", "?")},
    )
    await session.commit()
    return ContractReviewReport(**data)


@router.post("/document-comparison", response_model=DocumentComparisonReport)
async def compare_documents(
    payload: DocumentComparisonRequest,
    identity: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> DocumentComparisonReport:
    """Compara dos versiones de un documento y devuelve el impacto jurídico."""
    prompt = analysis_prompts.document_comparison_prompt(
        payload.version_a_title,
        payload.version_a_text,
        payload.version_b_title,
        payload.version_b_text,
        payload.fuero,
    )
    raw = await _get_model_response(analysis_prompts.ACADEMIC_SYSTEM_PROMPT, prompt)
    try:
        data = analysis_prompts.parse_json_response(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="El modelo devolvió una respuesta no parseable.")
    auditoria.registrar(
        session,
        "analisis.comparacion",
        usuario_id=identity.id,
        entidad="analisis",
        metadatos={"fuero": payload.fuero},
    )
    await session.commit()
    return DocumentComparisonReport(**data)


@router.post("/generate-draft", response_model=GeneratedDraftPayload)
async def generate_draft(
    payload: DraftRequest,
    identity: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> GeneratedDraftPayload:
    """Genera un borrador de escrito judicial desde una plantilla."""
    from app.services import prompts as rag_prompts  # evita import circular

    # Buscar plantilla por key — los skeletons están en el catálogo del frontend,
    # pero el backend recibe template_key y facts_and_instructions. Generamos
    # usando el fuero y las instrucciones del usuario.
    template_skeleton = "I. OBJETO\nII. HECHOS\nIII. DERECHO\nIV. PRUEBAS\nV. PETITORIO"
    template_title = f"Escrito — {payload.template_key}"
    normative_refs = "CPC/CPT/CPP según fuero"

    prompt = analysis_prompts.draft_generation_prompt(
        template_title,
        template_skeleton,
        normative_refs,
        payload.fuero,
        payload.facts_and_instructions,
    )
    raw = await _get_model_response(analysis_prompts.ACADEMIC_SYSTEM_PROMPT, prompt)
    try:
        data = analysis_prompts.parse_json_response(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="El modelo devolvió una respuesta no parseable.")
    auditoria.registrar(
        session,
        "analisis.borrador",
        usuario_id=identity.id,
        entidad="analisis",
        metadatos={"template": payload.template_key, "fuero": payload.fuero},
    )
    await session.commit()
    return GeneratedDraftPayload(**data)


@router.post("/hearing-prep", response_model=HearingPrepReport)
async def prepare_hearing(
    payload: HearingPrepRequest,
    identity: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> HearingPrepReport:
    """Prepara un guion estratégico para audiencia judicial."""
    prompt = analysis_prompts.hearing_prep_prompt(payload.hearing_topic, payload.fuero)
    raw = await _get_model_response(analysis_prompts.ACADEMIC_SYSTEM_PROMPT, prompt)
    try:
        data = analysis_prompts.parse_json_response(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="El modelo devolvió una respuesta no parseable.")
    auditoria.registrar(
        session,
        "analisis.audiencia",
        usuario_id=identity.id,
        entidad="analisis",
        metadatos={"fuero": payload.fuero},
    )
    await session.commit()
    return HearingPrepReport(**data)


@router.post("/case-extraction", response_model=CaseExtractionReport)
async def extract_case_facts(
    payload: CaseExtractionRequest,
    identity: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> CaseExtractionReport:
    """Extrae partes, plazos, montos y riesgos de un documento jurídico."""
    prompt = analysis_prompts.case_extraction_prompt(
        payload.document_title, payload.raw_text, payload.fuero
    )
    raw = await _get_model_response(analysis_prompts.ACADEMIC_SYSTEM_PROMPT, prompt)
    try:
        data = analysis_prompts.parse_json_response(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="El modelo devolvió una respuesta no parseable.")
    auditoria.registrar(
        session,
        "analisis.extraccion",
        usuario_id=identity.id,
        entidad="analisis",
        metadatos={"fuero": payload.fuero, "titulo": payload.document_title},
    )
    await session.commit()
    return CaseExtractionReport(**data)


@router.post("/analogous-cases", response_model=AnalogousCaseResult)
async def find_analogous_cases(
    payload: AnalogousCaseRequest,
    identity: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> AnalogousCaseResult:
    """Busca líneas jurisprudenciales análogas con RAG + análisis IA."""
    # Recuperar fragmentos RAG para enriquecer el contexto
    from app.services.embeddings import EmbeddingsNotConfigured, embed_query

    vector = None
    try:
        vector = await embed_query(payload.case_summary)
    except EmbeddingsNotConfigured:
        vector = None

    fragments = await hybrid_search(
        session, payload.case_summary, vector, tipo="jurisprudencia", limit=4
    )
    context_fragments = "\n".join(
        f"- {f.documento_titulo} ({f.articulo_numero or 'N/A'}): {f.texto[:280]}"
        for f in fragments
    )
    prompt = analysis_prompts.analogous_cases_prompt(
        payload.case_summary, payload.fuero, context_fragments
    )
    raw = await _get_text_response(analysis_prompts.ACADEMIC_SYSTEM_PROMPT, prompt)
    result = raw.strip() or "No se obtuvieron criterios análogos. Verificá directamente en https://www.csj.gov.py/jurisprudencia/."
    auditoria.registrar(
        session,
        "analisis.analogos",
        usuario_id=identity.id,
        entidad="analisis",
        metadatos={"fuero": payload.fuero, "fragmentos": len(fragments)},
    )
    await session.commit()
    return AnalogousCaseResult(analysis=result)


@router.post("/client-lead-triage", response_model=ClientLeadTriage)
async def triage_client_lead(
    payload: ClientLeadTriageRequest,
    identity: Identity = Depends(require_permission("chat.usar")),
    session: AsyncSession = Depends(get_session),
) -> ClientLeadTriage:
    """Clasifica una consulta inicial de cliente y genera orientación preliminar."""
    prompt = analysis_prompts.client_lead_triage_prompt(
        payload.client_name, payload.legal_area, payload.description
    )
    raw = await _get_model_response(analysis_prompts.ACADEMIC_SYSTEM_PROMPT, prompt)
    try:
        data = analysis_prompts.parse_json_response(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="El modelo devolvió una respuesta no parseable.")
    auditoria.registrar(
        session,
        "analisis.triaje",
        usuario_id=identity.id,
        entidad="analisis",
        metadatos={"area": payload.legal_area, "urgencia": data.get("urgency", "?")},
    )
    await session.commit()
    return ClientLeadTriage(**data)
