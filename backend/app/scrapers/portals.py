"""Extractores independientes por portal oficial (Plan Maestro §8).

Los patrones se ajustan a la estructura pública de cada portal; si un portal
cambia, solo se actualiza su clase.
"""

from __future__ import annotations

from app.scrapers.base import BaseScraper


class BacnScraper(BaseScraper):
    codigo = "bacn"
    nombre = "BACN — Leyes Paraguayas"
    url_base = "https://www.bacn.gov.py/"
    dominio = ("bacn.gov.py",)
    listado = "https://www.bacn.gov.py/leyes-paraguayas"
    patron_enlace = r"bacn\.gov\.py/leyes-paraguayas/\d+"
    tipo = "ley"


class CsjLegislacionScraper(BaseScraper):
    codigo = "csj_legislacion"
    nombre = "CSJ — Legislación"
    url_base = "https://www.csj.gov.py/"
    dominio = ("csj.gov.py",)
    listado = "https://www.csj.gov.py/legislacion/"
    patron_enlace = r"csj\.gov\.py/legislacion/.+"
    tipo = "ley"


class CsjJurisprudenciaScraper(BaseScraper):
    codigo = "csj_jurisprudencia"
    nombre = "CSJ — Jurisprudencia"
    url_base = "https://www.csj.gov.py/"
    dominio = ("csj.gov.py", "apps.csj.gov.py")
    listado = "https://www.csj.gov.py/jurisprudencia/"
    patron_enlace = r"(csj\.gov\.py|apps\.csj\.gov\.py)/jurisprudencia/.+"
    tipo = "jurisprudencia"


class PoderJudicialScraper(BaseScraper):
    codigo = "pj"
    nombre = "Poder Judicial"
    url_base = "https://www.pj.gov.py/"
    dominio = ("pj.gov.py",)
    listado = "https://www.pj.gov.py/"
    patron_enlace = r"pj\.gov\.py/.+"
    tipo = "doctrina"


SCRAPERS: dict[str, BaseScraper] = {
    scraper.codigo: scraper
    for scraper in (BacnScraper(), CsjLegislacionScraper(), CsjJurisprudenciaScraper(), PoderJudicialScraper())
}


def get_scraper(codigo: str) -> BaseScraper:
    if codigo not in SCRAPERS:
        raise KeyError(f"Fuente desconocida: {codigo}")
    return SCRAPERS[codigo]
