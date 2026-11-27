"""Esquemas de análisis jurídico asistido por IA (Plan Maestro §12.2).

Adaptados de los data classes de LegalAiService.kt: revisión de contratos,
comparación de documentos, generación de escritos, preparación de audiencias,
extracción de hechos, casos análogos y triaje de clientes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Revisión de contratos --------------------------------------------------
class ContractRiskClause(BaseModel):
    clause_name: str = Field(alias="clauseName")
    severity: str  # CRITICO | ALTO | MEDIO | BAJO
    legal_finding: str = Field(alias="legalFinding")
    paraguay_reference: str = Field(alias="paraguayReference")
    suggested_redline: str = Field(alias="suggestedRedline")


class ContractReviewRequest(BaseModel):
    contract_text: str = Field(min_length=10, max_length=20000, alias="contractText")
    fuero: str = "Civil y Comercial"


class ContractReviewReport(BaseModel):
    executive_summary: str = Field(alias="executiveSummary")
    overall_risk_level: str = Field(alias="overallRiskLevel")
    missing_clauses: list[str] = Field(default_factory=list, alias="missingClauses")
    risky_clauses: list[ContractRiskClause] = Field(default_factory=list, alias="riskyClauses")
    recommendations: list[str] = Field(default_factory=list)


# --- Comparación de documentos ---------------------------------------------
class DocumentComparisonRequest(BaseModel):
    version_a_title: str = Field(default="Versión A", alias="versionATitle")
    version_a_text: str = Field(min_length=10, max_length=20000, alias="versionAText")
    version_b_title: str = Field(default="Versión B", alias="versionBTitle")
    version_b_text: str = Field(min_length=10, max_length=20000, alias="versionBText")
    fuero: str = "Civil y Comercial"


class DocumentComparisonReport(BaseModel):
    summary: str
    legal_impact: str = Field(alias="legalImpact")
    added_points: list[str] = Field(default_factory=list, alias="addedPoints")
    removed_points: list[str] = Field(default_factory=list, alias="removedPoints")
    modified_points: list[str] = Field(default_factory=list, alias="modifiedPoints")
    action_checklist: list[str] = Field(default_factory=list, alias="actionChecklist")


# --- Generación de escritos -------------------------------------------------
class DraftRequest(BaseModel):
    template_key: str = Field(alias="templateKey")
    facts_and_instructions: str = Field(min_length=5, max_length=10000, alias="factsAndInstructions")
    fuero: str = "Civil y Comercial"


class GeneratedDraftPayload(BaseModel):
    title: str
    content: str
    sources_summary: str = Field(default="", alias="sourcesSummary")
    human_review_checklist: list[str] = Field(default_factory=list, alias="humanReviewChecklist")


# --- Preparación de audiencias ---------------------------------------------
class HearingPrepRequest(BaseModel):
    hearing_topic: str = Field(min_length=5, max_length=8000, alias="hearingTopic")
    fuero: str = "Civil y Comercial"


class HearingPrepReport(BaseModel):
    strategy_summary: str = Field(alias="strategySummary")
    key_arguments: list[str] = Field(default_factory=list, alias="keyArguments")
    strategic_questions: list[str] = Field(default_factory=list, alias="strategicQuestions")
    anticipated_objections: list[str] = Field(default_factory=list, alias="anticipatedObjections")
    evidence_checklist: list[str] = Field(default_factory=list, alias="evidenceChecklist")


# --- Extracción de hechos --------------------------------------------------
class CaseExtractionRequest(BaseModel):
    document_title: str = Field(default="Documento del caso", alias="documentTitle")
    raw_text: str = Field(min_length=10, max_length=20000, alias="rawText")
    fuero: str = "Civil y Comercial"


class CaseExtractionReport(BaseModel):
    parties: list[str] = Field(default_factory=list)
    key_dates_and_deadlines: list[str] = Field(default_factory=list, alias="keyDatesAndDeadlines")
    monetary_amounts_and_obligations: list[str] = Field(
        default_factory=list, alias="monetaryAmountsAndObligations"
    )
    facts_summary: str = Field(default="", alias="factsSummary")
    suggested_fuero: str = Field(default="", alias="suggestedFuero")
    procedural_risks: list[str] = Field(default_factory=list, alias="proceduralRisks")


# --- Casos análogos --------------------------------------------------------
class AnalogousCaseRequest(BaseModel):
    case_summary: str = Field(min_length=5, max_length=6000, alias="caseSummary")
    fuero: str = "Civil y Comercial"


class AnalogousCaseResult(BaseModel):
    analysis: str


# --- Triaje de clientes ----------------------------------------------------
class ClientLeadTriageRequest(BaseModel):
    client_name: str = Field(min_length=2, max_length=300, alias="clientName")
    legal_area: str = Field(default="Civil y Comercial", alias="legalArea")
    description: str = Field(min_length=5, max_length=6000)


class ClientLeadTriage(BaseModel):
    urgency: str  # URGENTE | NORMAL | CONSULTIVA
    lawyer_summary: str = Field(alias="lawyerSummary")
    follow_up_questions: list[str] = Field(default_factory=list, alias="followUpQuestions")
    informative_guidance: str = Field(alias="informativeGuidance")


# --- Respuesta genérica de análisis ----------------------------------------
class AnalysisResponse(BaseModel):
    ok: bool = True
    modelo: str = ""
    result: dict | str
