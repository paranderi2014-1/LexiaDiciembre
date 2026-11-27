import uuid

from app.services.citaciones import CONTINGENCIA, is_official_url, validate_citations
from app.services.search import RetrievedFragment


def _fragment(url: str = "https://www.bacn.gov.py/leyes-paraguayas/1") -> RetrievedFragment:
    return RetrievedFragment(
        fragmento_id=uuid.uuid4(),
        documento_id=uuid.uuid4(),
        documento_titulo="Ley 1376/88",
        documento_tipo="ley",
        documento_numero="1376/88",
        documento_estado="vigente",
        fecha_publicacion=None,
        url_original=url,
        fuente="BACN",
        articulo_numero="32",
        texto="Los honorarios se regulan conforme al artículo 32.",
        score_bm25=0.4,
        score_vector=0.8,
    )


def test_conserva_citas_verificables():
    fragment = _fragment()
    resultado = validate_citations(f"Según el artículo 32 [[f:{fragment.fragmento_id}]].", [fragment])
    assert resultado.fundamento_suficiente is True
    assert resultado.contenido == f"Según el artículo 32 [[f:{fragment.fragmento_id}]]."
    assert resultado.fuentes[0]["url"] == fragment.url_original


def test_descarta_citas_inventadas():
    fragment = _fragment()
    inventado = uuid.uuid4()
    resultado = validate_citations(f"Ver [[f:{inventado}]] y [[f:{fragment.fragmento_id}]]", [fragment])
    assert resultado.citas_invalidas == [str(inventado)]
    assert f"[[f:{inventado}]]" not in resultado.contenido
    assert resultado.fundamento_suficiente is True


def test_sin_citas_devuelve_contingencia():
    fragment = _fragment()
    resultado = validate_citations("Respuesta sin respaldo documental.", [fragment])
    assert resultado.contenido == CONTINGENCIA
    assert resultado.fundamento_suficiente is False
    assert resultado.fuentes == []


def test_rechaza_fuentes_no_oficiales():
    fragment = _fragment(url="https://ejemplo.com/ley")
    resultado = validate_citations(f"Ver [[f:{fragment.fragmento_id}]]", [fragment])
    assert resultado.fundamento_suficiente is False
    assert resultado.contenido == CONTINGENCIA


def test_dominios_oficiales():
    assert is_official_url("https://www.bacn.gov.py/leyes-paraguayas/1")
    assert is_official_url("https://apps.csj.gov.py/jurisprudencia/1")
    assert not is_official_url("http://www.csj.gov.py/jurisprudencia/1")
    assert not is_official_url("https://csj.gov.py.ejemplo.com/x")
