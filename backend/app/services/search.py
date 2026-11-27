"""Búsqueda híbrida BM25 + vectorial sobre PostgreSQL (§11).

La similitud vectorial se calcula con el operador coseno de pgvector y el ranking
textual con `ts_rank_cd` sobre la columna generada `texto_tsv`. Ambos puntajes se
normalizan y combinan con los pesos configurados.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


@dataclass(slots=True)
class RetrievedFragment:
    fragmento_id: uuid.UUID
    documento_id: uuid.UUID
    documento_titulo: str
    documento_tipo: str
    documento_numero: str | None
    documento_estado: str
    fecha_publicacion: date | None
    url_original: str
    fuente: str
    articulo_numero: str | None
    texto: str
    score_bm25: float
    score_vector: float | None
    score: float = 0.0
    metadatos: dict = field(default_factory=dict)

    def citation(self) -> dict:
        return {
            "fragmento_id": str(self.fragmento_id),
            "documento_id": str(self.documento_id),
            "titulo": self.documento_titulo,
            "tipo": self.documento_tipo,
            "numero": self.documento_numero,
            "articulo": self.articulo_numero,
            "fuente": self.fuente,
            "url": self.url_original,
            "fecha_publicacion": self.fecha_publicacion.isoformat()
            if self.fecha_publicacion
            else None,
        }


_SQL = """
WITH params AS (
    SELECT websearch_to_tsquery('spanish', CAST(:termino AS text)) AS tsq,
           CAST(:vector AS halfvec) AS vec
)
SELECT f.id                AS fragmento_id,
       f.texto             AS texto,
       d.id                AS documento_id,
       d.titulo            AS documento_titulo,
       d.tipo              AS documento_tipo,
       d.numero            AS documento_numero,
       d.estado            AS documento_estado,
       d.fecha_publicacion AS fecha_publicacion,
       d.url_original      AS url_original,
       s.nombre            AS fuente,
       a.numero            AS articulo_numero,
       ts_rank_cd(f.texto_tsv, p.tsq) AS score_bm25,
       CASE WHEN p.vec IS NOT NULL AND f.embedding IS NOT NULL
            THEN 1 - (f.embedding <=> p.vec)
            ELSE NULL END AS score_vector
FROM fragmentos f
JOIN documentos d ON d.id = f.documento_id
JOIN fuentes s ON s.id = d.fuente_id
LEFT JOIN articulos a ON a.id = f.articulo_id
CROSS JOIN params p
WHERE ((p.vec IS NOT NULL AND f.embedding IS NOT NULL) OR f.texto_tsv @@ p.tsq)
   AND (CAST(:tipo AS text) IS NULL OR d.tipo = CAST(:tipo AS text))
   AND (CAST(:numero AS text) IS NULL OR d.numero ILIKE CAST(:numero AS text))
   AND (CAST(:anio AS integer) IS NULL
        OR EXTRACT(YEAR FROM d.fecha_publicacion) = CAST(:anio AS integer))
ORDER BY GREATEST(ts_rank_cd(f.texto_tsv, p.tsq), COALESCE(1 - (f.embedding <=> p.vec), 0)) DESC
LIMIT :limite
"""


def _vector_literal(vector: list[float] | None) -> str | None:
    if vector is None:
        return None
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


async def hybrid_search(
    session: AsyncSession,
    termino: str,
    vector: list[float] | None = None,
    *,
    tipo: str | None = None,
    numero: str | None = None,
    anio: int | None = None,
    limit: int | None = None,
) -> list[RetrievedFragment]:
    """Devuelve fragmentos ordenados por puntaje híbrido normalizado."""
    if not termino.strip() and vector is None:
        return []

    rows = (
        await session.execute(
            text(_SQL),
            {
                "termino": termino,
                "vector": _vector_literal(vector),
                "tipo": tipo,
                "numero": f"%{numero}%" if numero else None,
                "anio": anio,
                "limite": limit or settings.rag_top_k,
            },
        )
    ).mappings()

    results: list[RetrievedFragment] = []
    for row in rows:
        results.append(
            RetrievedFragment(
                fragmento_id=row["fragmento_id"],
                documento_id=row["documento_id"],
                documento_titulo=row["documento_titulo"],
                documento_tipo=row["documento_tipo"],
                documento_numero=row["documento_numero"],
                documento_estado=row["documento_estado"],
                fecha_publicacion=row["fecha_publicacion"],
                url_original=row["url_original"],
                fuente=row["fuente"],
                articulo_numero=row["articulo_numero"],
                texto=row["texto"],
                score_bm25=float(row["score_bm25"] or 0.0),
                score_vector=float(row["score_vector"]) if row["score_vector"] is not None else None,
            )
        )

    max_bm25 = max((r.score_bm25 for r in results), default=0.0)
    for item in results:
        bm25 = item.score_bm25 / max_bm25 if max_bm25 > 0 else 0.0
        vector_score = item.score_vector if item.score_vector is not None else 0.0
        item.score = settings.bm25_weight * bm25 + settings.vector_weight * vector_score

    results.sort(key=lambda item: item.score, reverse=True)
    return results
