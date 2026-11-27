"""Tests de los endpoints de análisis jurídico."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.main import app


@pytest.fixture
def mock_settings():
    from app.core.config import settings

    original_key = settings.openai_api_key
    original_url = settings.openai_base_url
    settings.openai_api_key = "test-key"
    settings.openai_base_url = "https://test.openai.com/v1"
    yield settings
    settings.openai_api_key = original_key
    settings.openai_base_url = original_url


async def test_contract_review_returns_report(client, cleanup_user, mock_settings):
    fake_json = json.dumps({
        "executiveSummary": "Contrato estándar",
        "overallRiskLevel": "MEDIO",
        "missingClauses": ["Cláusula de jurisdicción"],
        "riskyClauses": [
            {
                "clauseName": "Penalidad excesiva",
                "severity": "ALTO",
                "legalFinding": "Penalización desproporcionada",
                "paraguayReference": "Art. 421 CC",
                "suggestedRedline": "Reducir al 10% del valor",
            }
        ],
        "recommendations": ["Negociar reducción de penalidad"],
    })

    with patch("app.routes.analysis._get_model_response", new_callable=AsyncMock, return_value=fake_json):
        resp = await client.post("/api/analysis/contract-review", json={
            "contractText": "Contrato de locación de servicios con penalidad excesiva.",
            "fuero": "Civil y Comercial",
        }, headers={"Authorization": "Bearer ******"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["overallRiskLevel"] == "MEDIO"
    assert len(data["riskyClauses"]) == 1
    assert data["riskyClauses"][0]["severity"] == "ALTO"


async def test_case_extraction_returns_report(client, cleanup_user, mock_settings):
    fake_json = json.dumps({
        "parties": ["Actor: Juan Pérez", "Demandado: María Gómez"],
        "keyDatesAndDeadlines": ["Notificación: 01/03/2025"],
        "monetaryAmountsAndObligations": ["Gs. 50.000.000"],
        "factsSummary": "Demanda por incumplimiento contractual",
        "suggestedFuero": "Civil y Comercial",
        "proceduralRisks": ["Posible prescripción"],
    })

    with patch("app.routes.analysis._get_model_response", new_callable=AsyncMock, return_value=fake_json):
        resp = await client.post("/api/analysis/case-extraction", json={
            "documentTitle": "Demanda civil",
            "rawText": "Juan Pérez demanda a María Gómez por incumplimiento...",
            "fuero": "Civil y Comercial",
        }, headers={"Authorization": "Bearer ******"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["parties"]) == 2
    assert data["suggestedFuero"] == "Civil y Comercial"


async def test_client_lead_triage_returns_urgency(client, cleanup_user, mock_settings):
    fake_json = json.dumps({
        "urgency": "NORMAL",
        "lawyerSummary": "Consulta sobre desalojo",
        "followUpQuestions": ["¿Tiene contrato escrito?"],
        "informativeGuidance": "Orientación preliminar sobre desalojo",
    })

    with patch("app.routes.analysis._get_model_response", new_callable=AsyncMock, return_value=fake_json):
        resp = await client.post("/api/analysis/client-lead-triage", json={
            "clientName": "Carlos Test",
            "legalArea": "Civil y Comercial",
            "description": "Consulta por desalojo de inmueble",
        }, headers={"Authorization": "Bearer ******"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["urgency"] == "NORMAL"
    assert len(data["followUpQuestions"]) > 0


async def test_contract_review_without_key_returns_503(client, cleanup_user):
    from app.core.config import settings

    original = settings.openai_api_key
    settings.openai_api_key = None
    try:
        resp = await client.post("/api/analysis/contract-review", json={
            "contractText": "Contrato de locación de servicios.",
            "fuero": "Civil y Comercial",
        }, headers={"Authorization": "Bearer ******"})
        assert resp.status_code == 503
    finally:
        settings.openai_api_key = original
