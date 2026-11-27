"""Validación de citas jurídicas (Plan Maestro §12.1).

El modelo debe citar únicamente fragmentos recuperados, con el marcador
`[[f:<uuid>]]`. Toda cita que no pertenezca al conjunto recuperado se descarta y,
si no queda ninguna, la respuesta se sustituye por el texto de contingencia.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from urllib.parse import urlparse

from app.services.search import RetrievedFragment

CONTINGENCIA = (
    "No se encontró fundamento jurídico suficiente en las fuentes indexadas "
    "para responder esta consulta."
)

OFFICIAL_DOMAINS = frozenset({"bacn.gov.py", "pj.gov.py", "csj.gov.py", "apps.csj.gov.py"})

_CITATION = re.compile(r"\[\[f:([0-9a-fA-F-]{36})\]\]")


@dataclass(slots=True)
class CitationResult:
    contenido: str
    fuentes: list[dict] = field(default_factory=list)
    fundamento_suficiente: bool = False
    citas_invalidas: list[str] = field(default_factory=list)


def is_official_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in OFFICIAL_DOMAINS)


def validate_citations(content: str, retrieved: list[RetrievedFragment]) -> CitationResult:
    """Conserva solo citas verificables y detecta respuestas sin fundamento."""
    by_id = {str(item.fragmento_id): item for item in retrieved}
    cited: list[uuid.UUID] = []
    invalid: list[str] = []

    for match in _CITATION.finditer(content):
        raw = match.group(1)
        if raw in by_id and is_official_url(by_id[raw].url_original):
            if uuid.UUID(raw) not in cited:
                cited.append(uuid.UUID(raw))
        else:
            invalid.append(raw)

    if not cited:
        return CitationResult(
            contenido=CONTINGENCIA,
            fuentes=[],
            fundamento_suficiente=False,
            citas_invalidas=invalid,
        )

    valid_ids = {str(item) for item in cited}
    clean = _CITATION.sub(
        lambda m: "" if m.group(1) not in valid_ids else f"[[f:{m.group(1)}]]", content
    ).strip()

    fuentes: list[dict] = []
    seen: set[str] = set()
    for fragmento_id in valid_ids:
        item = by_id[fragmento_id]
        if str(item.documento_id) in seen:
            continue
        seen.add(str(item.documento_id))
        fuentes.append(item.citation())

    return CitationResult(
        contenido=clean,
        fuentes=fuentes,
        fundamento_suficiente=True,
        citas_invalidas=invalid,
    )
