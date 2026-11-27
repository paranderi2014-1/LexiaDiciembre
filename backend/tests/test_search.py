"""Búsqueda híbrida real contra PostgreSQL + pgvector (§11, §17)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete

from app.core.config import settings
from app.models.catalog import Documento, Fragmento, Fuente
from app.services.search import hybrid_search


def _vector(principal: float, secundario: float = 0.0) -> list[float]:
    values = [0.0] * settings.embedding_dimensions
    values[0] = principal
    values[1] = secundario
    return values


@pytest.fixture
async def corpus(db):
    codigo = f"test-{uuid.uuid4().hex[:8]}"
    fuente = Fuente(codigo=codigo, nombre="Fuente de prueba", url_base="https://www.bacn.gov.py")
    db.add(fuente)
    await db.flush()

    documento = Documento(
        fuente_id=fuente.id,
        tipo="ley",
        numero="1376/88",
        titulo="Ley de honorarios de prueba",
        estado="vigente",
        url_original=f"https://www.bacn.gov.py/leyes-paraguayas/{codigo}",
        hash=uuid.uuid4().hex,
        texto="Los honorarios profesionales se regulan por esta ley de prueba.",
    )
    db.add(documento)
    await db.flush()

    cercano = Fragmento(
        documento_id=documento.id,
        orden=0,
        texto="Los honorarios profesionales se regulan por el artículo 32.",
        tokens=12,
        embedding=_vector(1.0),
    )
    lejano = Fragmento(
        documento_id=documento.id,
        orden=1,
        texto="Disposiciones transitorias sobre notificaciones electrónicas.",
        tokens=10,
        embedding=_vector(0.0, 1.0),
    )
    db.add_all([cercano, lejano])
    await db.commit()

    yield documento, cercano, lejano

    await db.execute(delete(Documento).where(Documento.id == documento.id))
    await db.execute(delete(Fuente).where(Fuente.id == fuente.id))
    await db.commit()


async def test_ordena_por_similitud_vectorial(db, corpus):
    documento, cercano, _ = corpus
    results = await hybrid_search(db, "honorarios", _vector(1.0), tipo="ley")
    assert results, "la búsqueda debe devolver fragmentos"
    assert results[0].fragmento_id == cercano.id
    assert results[0].score_vector is not None
    assert results[0].score_vector > 0.9
    assert results[0].score > results[-1].score
    assert 0.0 <= results[0].score <= 1.0
    assert results[0].documento_id == documento.id


async def test_busqueda_textual_sin_vectores(db, corpus):
    _, cercano, _ = corpus
    results = await hybrid_search(db, "honorarios profesionales", None, tipo="ley")
    ids = [item.fragmento_id for item in results]
    assert cercano.id in ids
    assert all(item.score_vector is None for item in results)


async def test_filtro_por_tipo_excluye_otros_documentos(db, corpus):
    results = await hybrid_search(db, "honorarios", _vector(1.0), tipo="jurisprudencia")
    assert results == []
