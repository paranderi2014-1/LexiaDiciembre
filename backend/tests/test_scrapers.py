from app.scrapers.base import discover_links, html_to_text, is_official, split_articles

LISTADO = """
<html><body>
  <a href="/leyes-paraguayas/1234-ley-de-ejemplo">Ley de ejemplo</a>
  <a href="https://www.bacn.gov.py/leyes-paraguayas/9876-otra">Otra ley</a>
  <a href="/leyes-paraguayas/1234-ley-de-ejemplo">Duplicado</a>
  <a href="/contacto">Contacto</a>
</body></html>
"""

TEXTO = """
ARTÍCULO 1°.- Objeto.
La presente ley regula la materia.

ARTÍCULO 2°.- Ámbito de aplicación.
Se aplica en todo el territorio nacional.
"""


def test_descubre_enlaces_del_portal_sin_duplicados():
    links = discover_links(LISTADO, "https://www.bacn.gov.py/leyes-paraguayas", r"bacn\.gov\.py/leyes-paraguayas/\d+")
    assert links == [
        "https://www.bacn.gov.py/leyes-paraguayas/1234-ley-de-ejemplo",
        "https://www.bacn.gov.py/leyes-paraguayas/9876-otra",
    ]


def test_separa_articulos_con_numero_y_texto():
    articulos = split_articles(TEXTO)
    assert [a.numero for a in articulos] == ["1", "2"]
    assert articulos[0].titulo == "Objeto."
    assert "regula la materia" in articulos[0].texto


def test_extrae_texto_sin_scripts():
    html = "<html><body><script>x()</script><main><p>Texto legal</p></main></body></html>"
    assert html_to_text(html) == "Texto legal"


def test_solo_dominios_oficiales_https():
    assert is_official("https://www.pj.gov.py/x", ("pj.gov.py",))
    assert not is_official("http://www.pj.gov.py/x", ("pj.gov.py",))
    assert not is_official("https://pj.gov.py.falso.com/x", ("pj.gov.py",))
