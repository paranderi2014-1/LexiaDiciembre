"""Base común de los extractores por portal oficial (§8).

Cada portal define sus propios patrones de enlace y metadatos; la descarga,
la extracción de texto y el control de tamaño son compartidos.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

USER_AGENT = "LexIAParaguayBot/1.0 (+https://www.lexiapy.com; indexación jurídica oficial)"

_YEAR = re.compile(r"(19|20)\d{2}")
_NUMBER = re.compile(r"(?:N[°º]|Nro\.?|Núm\.?)\s*([0-9][0-9./-]*)", re.IGNORECASE)
_ARTICLE = re.compile(
    r"^\s*(?:ART[IÍ]CULO|Art\.?)\s*([0-9]+(?:\s?[°º])?)[\s.\-–:]*(.*)$",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ScrapedDocument:
    fuente: str
    url: str
    titulo: str
    texto: str
    tipo: str = "ley"
    numero: str | None = None
    fecha_publicacion: date | None = None
    metadatos: dict = field(default_factory=dict)


@dataclass(slots=True)
class ScrapedArticle:
    numero: str
    titulo: str | None
    texto: str
    orden: int


def is_official(url: str, domains: tuple[str, ...]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


def discover_links(html: str, base_url: str, pattern: str) -> list[str]:
    """Devuelve enlaces únicos del listado que coinciden con el patrón del portal."""
    soup = BeautifulSoup(html, "html.parser")
    regex = re.compile(pattern)
    found: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"])
        if regex.search(href) and href not in found:
            found.append(href)
    return found


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    return re.sub(r"\n{3,}", "\n\n", root.get_text("\n", strip=True))


def pdf_to_text(payload: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(payload))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def title_of(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find("h1") or soup.find("title")
    return heading.get_text(" ", strip=True) if heading else ""


def guess_number(text: str) -> str | None:
    match = _NUMBER.search(text)
    return match.group(1).rstrip("./-") if match else None


def guess_year(text: str) -> date | None:
    match = _YEAR.search(text)
    return date(int(match.group(0)), 1, 1) if match else None


def split_articles(text: str) -> list[ScrapedArticle]:
    """Separa el texto por encabezados de artículo conservando su orden."""
    articles: list[ScrapedArticle] = []
    current: ScrapedArticle | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal current, buffer
        if current is not None:
            current.texto = "\n".join(buffer).strip()
            if current.texto:
                articles.append(current)
        buffer = []

    for line in text.splitlines():
        match = _ARTICLE.match(line)
        if match:
            flush()
            numero = match.group(1).replace(" ", "").replace("°", "").replace("º", "")
            current = ScrapedArticle(
                numero=numero, titulo=match.group(2).strip() or None, texto="", orden=len(articles)
            )
            if match.group(2).strip():
                buffer.append(match.group(2).strip())
        elif current is not None:
            buffer.append(line)
    flush()
    return articles


class BaseScraper:
    """Extractor de un portal: listado + extracción de documentos."""

    codigo: str = ""
    nombre: str = ""
    url_base: str = ""
    dominio: tuple[str, ...] = ()
    listado: str = ""
    patron_enlace: str = ""
    tipo: str = "ley"

    async def listar(self, client: httpx.AsyncClient | None = None) -> list[str]:
        async with (client or httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT})) as http:
            response = await http.get(self.listado, follow_redirects=True)
            response.raise_for_status()
            return discover_links(response.text, self.listado, self.patron_enlace)

    async def extraer(
        self, url: str, client: httpx.AsyncClient | None = None
    ) -> ScrapedDocument:
        if not is_official(url, self.dominio):
            raise ValueError(f"URL fuera de los dominios oficiales de {self.codigo}: {url}")

        async with (client or httpx.AsyncClient(timeout=60.0, headers={"User-Agent": USER_AGENT})) as http:
            response = await http.get(url, follow_redirects=True)
            response.raise_for_status()
            if len(response.content) > settings.max_download_bytes:
                raise ValueError(f"Documento mayor a {settings.max_download_bytes} bytes: {url}")

            content_type = response.headers.get("content-type", "")
            if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                texto = pdf_to_text(response.content)
                titulo = ""
            else:
                texto = html_to_text(response.text)
                titulo = title_of(response.text)

        titulo = titulo or url.rsplit("/", 1)[-1]
        return ScrapedDocument(
            fuente=self.codigo,
            url=url,
            titulo=titulo[:590],
            texto=texto,
            tipo=self.tipo,
            numero=guess_number(titulo) or guess_number(texto[:400]),
            fecha_publicacion=guess_year(titulo),
            metadatos={"portal": self.nombre, "content_type": content_type},
        )
