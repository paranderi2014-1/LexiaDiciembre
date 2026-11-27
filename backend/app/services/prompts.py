"""Prompts jurídicos con reglas estrictas de fundamentación (§12.1)."""

from __future__ import annotations

from app.services.search import RetrievedFragment

SYSTEM_PROMPT = """Sos un asistente jurídico especializado en Derecho paraguayo.
Reglas obligatorias:
1. No inventes leyes, artículos, sentencias, números ni fechas.
2. Distinguí siempre legislación, jurisprudencia y doctrina.
3. Citá número, año, artículo, fuente y enlace original cuando estén disponibles.
4. Usá exclusivamente los fragmentos del CONTEXTO. Cada afirmación debe llevar el
   marcador exacto [[f:<id>]] del fragmento que la respalda.
5. Si el contexto no alcanza para responder, respondé exactamente:
   "No se encontró fundamento jurídico suficiente en las fuentes indexadas para responder esta consulta."
6. No presentes información no verificada como Derecho vigente.
7. Escribí en español del Paraguay, con lenguaje claro y sin asesoramiento definitivo.
"""


def build_context(fragments: list[RetrievedFragment]) -> str:
    if not fragments:
        return "(sin fragmentos recuperados)"
    blocks = []
    for item in fragments:
        header = f"[{item.fragmento_id}] {item.documento_titulo}"
        if item.documento_numero:
            header += f" — N° {item.documento_numero}"
        if item.articulo_numero:
            header += f" — Art. {item.articulo_numero}"
        header += f" ({item.documento_tipo}, fuente: {item.fuente})"
        blocks.append(f"{header}\nURL: {item.url_original}\n{item.texto}")
    return "\n\n---\n\n".join(blocks)


def build_user_prompt(pregunta: str, fragments: list[RetrievedFragment]) -> str:
    return f"CONTEXTO:\n{build_context(fragments)}\n\nCONSULTA:\n{pregunta}"
