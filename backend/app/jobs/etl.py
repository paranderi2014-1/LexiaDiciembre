"""Pipeline ETL e indexación (§9, §10).

Extract → Transform (limpieza, deduplicación, versiones, artículos) →
Load (documentos, artículos, fragmentos y embeddings). Una nueva versión
actualiza el documento y sus índices sin duplicarlo.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.catalog import (
    Articulo,
    CambioPendiente,
    Documento,
    Fragmento,
    Fuente,
    VersionDocumento,
)
from app.scrapers.base import ScrapedDocument, split_articles
from app.scrapers.portals import get_scraper
from app.services.embeddings import EmbeddingsNotConfigured, embed_texts
from app.utils.text import chunk_text, content_hash, estimate_tokens, normalize_text


@dataclass(slots=True)
class IngestReport:
    fuente: str
    descubiertos: int = 0
    nuevos: int = 0
    actualizados: int = 0
    pendientes_revision: int = 0
    sin_cambios: int = 0
    fragmentos: int = 0
    errores: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "fuente": self.fuente,
            "descubiertos": self.descubiertos,
            "nuevos": self.nuevos,
            "actualizados": self.actualizados,
            "pendientes_revision": self.pendientes_revision,
            "sin_cambios": self.sin_cambios,
            "fragmentos": self.fragmentos,
            "errores": self.errores,
        }


async def ensure_fuente(session: AsyncSession, codigo: str) -> Fuente:
    fuente = (
        await session.execute(select(Fuente).where(Fuente.codigo == codigo))
    ).scalar_one_or_none()
    if fuente is not None:
        return fuente

    scraper = get_scraper(codigo)
    fuente = Fuente(
        codigo=scraper.codigo,
        nombre=scraper.nombre,
        url_base=scraper.url_base,
        tipo="portal",
    )
    session.add(fuente)
    await session.flush()
    return fuente


async def _index_documento(session: AsyncSession, documento: Documento) -> int:
    await session.execute(delete(Fragmento).where(Fragmento.documento_id == documento.id))
    await session.execute(delete(Articulo).where(Articulo.documento_id == documento.id))
    await session.flush()

    articulos = split_articles(documento.texto)
    unidades: list[tuple[uuid.UUID | None, str]] = []

    if articulos:
        for article in articulos:
            row = Articulo(
                documento_id=documento.id,
                numero=article.numero,
                titulo=article.titulo,
                texto=article.texto,
                orden=article.orden,
            )
            session.add(row)
            await session.flush()
            for chunk in chunk_text(
                article.texto, settings.chunk_tokens, settings.chunk_overlap_tokens
            ):
                unidades.append((row.id, chunk))
    else:
        for chunk in chunk_text(
            documento.texto, settings.chunk_tokens, settings.chunk_overlap_tokens
        ):
            unidades.append((None, chunk))

    if not unidades:
        return 0

    vectors: list[list[float] | None]
    try:
        vectors = list(await embed_texts([texto for _, texto in unidades]))
    except EmbeddingsNotConfigured:
        vectors = [None] * len(unidades)

    for orden, ((articulo_id, texto), vector) in enumerate(zip(unidades, vectors, strict=True)):
        session.add(
            Fragmento(
                documento_id=documento.id,
                articulo_id=articulo_id,
                orden=orden,
                texto=texto,
                tokens=estimate_tokens(texto),
                embedding=vector,
            )
        )
    return len(unidades)


async def upsert_documento(
    session: AsyncSession, doc: ScrapedDocument
) -> tuple[Documento, str, int]:
    """Crea o versiona el documento. Devuelve (documento, estado, fragmentos)."""
    fuente = await ensure_fuente(session, doc.fuente)
    texto = normalize_text(doc.texto)
    huella = content_hash(texto)

    existente = (
        await session.execute(
            select(Documento).where(
                Documento.fuente_id == fuente.id, Documento.url_original == doc.url
            )
        )
    ).scalar_one_or_none()

    if existente is None:
        documento = Documento(
            fuente_id=fuente.id,
            tipo=doc.tipo,
            numero=doc.numero,
            titulo=doc.titulo,
            fecha_publicacion=doc.fecha_publicacion,
            estado="vigente",
            url_original=doc.url,
            hash=huella,
            texto=texto,
            metadatos=doc.metadatos,
        )
        session.add(documento)
        await session.flush()
        fragmentos = await _index_documento(session, documento)
        return documento, "nuevo", fragmentos

    if existente.hash == huella:
        return existente, "sin_cambios", 0

    # Control de actualizaciones (§18): el cambio se registra como pendiente
    # de revisión humana. No se actualiza el documento vigente automáticamente.
    pendiente = CambioPendiente(
        documento_id=existente.id,
        fuente_codigo=doc.fuente,
        url=doc.url,
        titulo=doc.titulo or existente.titulo,
        hash_anterior=existente.hash,
        hash_nuevo=huella,
        texto_nuevo=texto,
        texto_anterior=existente.texto,
        estado="pendiente",
        metadatos=doc.metadatos,
    )
    session.add(pendiente)
    await session.flush()
    return existente, "pendiente_revision", 0


async def run_source(session: AsyncSession, codigo: str, limite: int | None = None) -> IngestReport:
    scraper = get_scraper(codigo)
    report = IngestReport(fuente=codigo)

    try:
        urls = await scraper.listar()
    except Exception as exc:  # noqa: BLE001 - se reporta la fuente no disponible
        report.errores.append(f"listado: {type(exc).__name__}: {exc}")
        return report

    if limite:
        urls = urls[:limite]
    report.descubiertos = len(urls)

    for url in urls:
        try:
            doc = await scraper.extraer(url)
            _, estado, fragmentos = await upsert_documento(session, doc)
            report.fragmentos += fragmentos
            if estado == "nuevo":
                report.nuevos += 1
            elif estado == "pendiente_revision":
                report.pendientes_revision += 1
            else:
                report.sin_cambios += 1
            await session.commit()
        except Exception as exc:  # noqa: BLE001 - un documento fallido no detiene el lote
            await session.rollback()
            report.errores.append(f"{url}: {type(exc).__name__}: {exc}")

    return report
