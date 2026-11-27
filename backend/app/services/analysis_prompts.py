"""Prompts para análisis jurídico estructurado — adaptados de LegalAiService.kt.

Cada función construye el prompt específico para el tipo de análisis solicitado,
con las reglas jurídicas paraguayas y el schema JSON esperado.
"""

from __future__ import annotations

import json

ACADEMIC_SYSTEM_PROMPT = """Eres LexIAPY Chat, un copiloto jurídico especializado exclusivamente en el derecho positivo, jurisprudencia y práctica forense de la República del Paraguay.
Reglas obligatorias de rigor jurídico:
1. Responde siempre en castellano claro, técnico, sobrio y estructurado.
2. Prioriza como fuentes oficiales de verificación: BACN (bacn.gov.py/leyes-paraguayas), Poder Judicial (pj.gov.py), Corte Suprema de Justicia (csj.gov.py).
3. Cuando recibas fragmentos del contexto, cítalos explícitamente indicando el cuerpo legal, el número de artículo y su estado de vigencia cuando conste.
4. Nunca inventes números de leyes, artículos, expedientes ni acuerdos y sentencias. Si un dato normativo requiere verificación adicional, decláralo con honestidad profesional.
5. Todo análisis o borrador requiere revisión y aprobación de un abogado matriculado antes de su presentación o firma. No garantices resultados procesales.
"""


def contract_review_prompt(contract_text: str, fuero: str) -> str:
    return f"""Realiza una revisión contractual exhaustiva bajo el Código Civil Paraguayo (Ley N° 1183/85), Ley de Defensa del Consumidor N° 1334/98 y normativa aplicable al fuero {fuero}.
Clasifica cada cláusula riesgosa con severidad CRITICO, ALTO, MEDIO o BAJO, señala omisiones y propón redacción alternativa.

=== TEXTO DEL CONTRATO ===
{contract_text[:18000]}

Debés responder ÚNICAMENTEN con un objeto JSON válido con esta estructura:
{{
  "executiveSummary": "Resumen ejecutivo del contrato y balance de riesgos",
  "overallRiskLevel": "CRITICO | ALTO | MEDIO | BAJO",
  "missingClauses": ["Cláusulas omitidas recomendadas bajo derecho paraguayo"],
  "riskyClauses": [
    {{
      "clauseName": "Nombre de la cláusula",
      "severity": "CRITICO | ALTO | MEDIO | BAJO",
      "legalFinding": "Hallazgo jurídico",
      "paraguayReference": "Referencia normativa paraguaya",
      "suggestedRedline": "Redacción alternativa sugerida"
    }}
  ],
  "recommendations": ["Recomendaciones accionables"]
}}"""


def document_comparison_prompt(
    title_a: str, text_a: str, title_b: str, text_b: str, fuero: str
) -> str:
    return f"""Compara dos versiones de un documento jurídico bajo el derecho paraguayo ({fuero}).
Versión A: {title_a}
{ text_a[:10000]}

Versión B: {title_b}
{ text_b[:10000]}

Debés responder ÚNICAMENTEN con un objeto JSON válido:
{{
  "summary": "Síntesis de las diferencias",
  "legalImpact": "Impacto jurídico de los cambios",
  "addedPoints": ["Puntos añadidos en B que no estaban en A"],
  "removedPoints": ["Puntos eliminados en B que estaban en A"],
  "modifiedPoints": ["Puntos modificados entre versiones"],
  "actionChecklist": ["Acciones recomendadas"]
}}"""


def draft_generation_prompt(
    template_title: str,
    template_skeleton: str,
    normative_refs: str,
    fuero: str,
    facts_and_instructions: str,
) -> str:
    return f"""Redacta un borrador jurídico completo en castellano jurídico paraguayo siguiendo esta plantilla oficial:
Plantilla: {template_title} | Fuero: {fuero}
Referencias base: {normative_refs}
Estructura base:
{template_skeleton}

Instrucciones y hechos específicos del usuario:
{ facts_and_instructions[:8000]}

Incluye espacios entre corchetes [DATO A VERIFICAR] para datos no provistos y una lista de verificación para aprobación humana.

Debés responder ÚNICAMENTEN con un objeto JSON válido:
{{
  "title": "Título del borrador",
  "content": "Texto completo del escrito o documento listo para revisión profesional",
  "sourcesSummary": "Normativa paraguaya citada",
  "humanReviewChecklist": ["Lista de verificación para aprobación humana"]
}}"""


def hearing_prep_prompt(hearing_topic: str, fuero: str) -> str:
    return f"""Prepara un guion estratégico completo para audiencia judicial/conciliatoria en Paraguay ({fuero}).
Objetivo de la audiencia / situación:
{ hearing_topic[:6000]}

Debés responder ÚNICAMENTEN con un objeto JSON válido:
{{
  "strategySummary": "Resumen de la estrategia",
  "keyArguments": ["Argumentos clave a presentar"],
  "strategicQuestions": ["Preguntas estratégicas"],
  "anticipatedObjections": ["Objeciones anticipadas de la contraparte"],
  "evidenceChecklist": ["Checklist de evidencia a llevar"]
}}"""


def case_extraction_prompt(document_title: str, raw_text: str, fuero: str) -> str:
    return f"""Extrae entidades jurídicas estructuradas de este documento paraguayo ({fuero}) titulado "{document_title}":
partes intervinientes, fechas y plazos procesales/contractuales, montos y obligaciones, resumen de hechos, fuero sugerido y riesgos detectados.

=== DOCUMENTO ===
{ raw_text[:18000]}

Debés responder ÚNICAMENTEN con un objeto JSON válido:
{{
  "parties": ["Partes intervinientes"],
  "keyDatesAndDeadlines": ["Fechas y plazos"],
  "monetaryAmountsAndObligations": ["Montos y obligaciones"],
  "factsSummary": "Resumen de hechos",
  "suggestedFuero": "Fuero sugerido",
  "proceduralRisks": ["Riesgos procesales detectados"]
}}"""


def analogous_cases_prompt(case_summary: str, fuero: str, context_fragments: str) -> str:
    return f"""Identifica líneas jurisprudenciales análogas de la Corte Suprema de Justicia del Paraguay y precedentes normativos relevantes para el fuero {fuero}.
Caso de análisis:
{ case_summary[:4000]}

{("Contexto del índice controlado:" + chr(10) + context_fragments) if context_fragments else ""}

Contrasta siempre la fuente oficial en https://www.csj.gov.py/jurisprudencia/ y evita inventar números de Acuerdos y Sentencias si no constan en la búsqueda."""


def client_lead_triage_prompt(client_name: str, legal_area: str, description: str) -> str:
    return f"""Realiza un triaje preliminar de admisión de cliente en Paraguay para el área "{legal_area}".
Consultante: {client_name}
Relato inicial: {description[:5000]}
Regla ética: clasifica urgencia (URGENTE, NORMAL, CONSULTIVA), elabora resumen estructurado para el abogado, lista preguntas de entrevista inicial y redacta una orientación informativa preliminar SIN emitir dictamen definitivo ni prometer resultados judiciales.

Debés responder ÚNICAMENTEN con un objeto JSON válido:
{{
  "urgency": "URGENTE | NORMAL | CONSULTIVA",
  "lawyerSummary": "Resumen estructurado para el abogado",
  "followUpQuestions": ["Preguntas de entrevista inicial"],
  "informativeGuidance": "Orientación informativa preliminar"
}}"""


def parse_json_response(raw: str) -> dict:
    """Extrae el objeto JSON de una respuesta del modelo."""
    text = raw.strip()
    # Remover markdown code fences si existen
    if text.startswith("```"):
        lines = text.split("\n")
        start = 1
        end = len(lines) - 1
        for i, line in enumerate(lines):
            if line.strip().startswith("```") and i > 0:
                end = i
                break
        text = "\n".join(lines[start:end])
    return json.loads(text)
