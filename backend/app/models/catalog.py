"""Fuentes oficiales, documentos, artículos y fragmentos indexados (Plan Maestro §5, §9)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import (
    Boolean,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database.session import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class Fuente(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "fuentes"

    codigo: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    url_base: Mapped[str] = mapped_column(String(400), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False, default="portal")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    documentos: Mapped[list["Documento"]] = relationship(back_populates="fuente")


class Documento(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "documentos"
    __table_args__ = (
        UniqueConstraint("fuente_id", "url_original", name="documento_fuente_url_unico"),
        Index("documentos_tipo_estado_idx", "tipo", "estado"),
        Index("documentos_fecha_publicacion_idx", "fecha_publicacion"),
        Index("documentos_numero_idx", "numero"),
    )

    fuente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fuentes.id", ondelete="RESTRICT"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)  # ley | jurisprudencia | doctrina
    numero: Mapped[str | None] = mapped_column(String(80))
    titulo: Mapped[str] = mapped_column(String(600), nullable=False)
    fecha_publicacion: Mapped[date | None] = mapped_column(Date)
    fecha_vigencia: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(40), nullable=False, default="vigente")
    url_original: Mapped[str] = mapped_column(String(1000), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    texto: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metadatos: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    fuente: Mapped[Fuente] = relationship(back_populates="documentos", lazy="joined")
    articulos: Mapped[list["Articulo"]] = relationship(
        back_populates="documento", cascade="all, delete-orphan"
    )
    fragmentos: Mapped[list["Fragmento"]] = relationship(
        back_populates="documento", cascade="all, delete-orphan"
    )


class VersionDocumento(UUIDPrimaryKey, Base):
    __tablename__ = "versiones_documento"

    documento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
    )
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metadatos: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    detectada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Archivo(UUIDPrimaryKey, Base):
    __tablename__ = "archivos"

    documento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(400), nullable=False)
    mime: Mapped[str | None] = mapped_column(String(120))
    bytes: Mapped[int | None] = mapped_column(Integer)
    ruta: Mapped[str | None] = mapped_column(String(1000))
    hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Articulo(UUIDPrimaryKey, Base):
    __tablename__ = "articulos"
    __table_args__ = (UniqueConstraint("documento_id", "numero", name="articulo_unico"),)

    documento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
    )
    numero: Mapped[str] = mapped_column(String(60), nullable=False)
    titulo: Mapped[str | None] = mapped_column(String(400))
    texto: Mapped[str] = mapped_column(Text, nullable=False, default="")
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    documento: Mapped[Documento] = relationship(back_populates="articulos")


class Fragmento(UUIDPrimaryKey, Base):
    __tablename__ = "fragmentos"
    __table_args__ = (
        Index("fragmentos_texto_tsv_idx", "texto_tsv", postgresql_using="gin"),
        # HNSW admite hasta 2000 dimensiones con `vector` y 4000 con `halfvec`;
        # text-embedding-3-large usa 3072, por eso la columna es halfvec.
        Index(
            "fragmentos_embedding_idx",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "halfvec_cosine_ops"},
        ),
        Index("fragmentos_documento_idx", "documento_id", "orden"),
    )

    documento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
    )
    articulo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("articulos.id", ondelete="SET NULL")
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding: Mapped[list[float] | None] = mapped_column(
        HALFVEC(settings.embedding_dimensions)
    )
    # Columna generada: la búsqueda textual siempre ve el texto vigente.
    texto_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('spanish', texto)", persisted=True)
    )

    documento: Mapped[Documento] = relationship(back_populates="fragmentos")


class Etiqueta(UUIDPrimaryKey, Base):
    __tablename__ = "etiquetas"

    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)


class DocumentoEtiqueta(Base):
    __tablename__ = "documento_etiqueta"

    documento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), primary_key=True
    )
    etiqueta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("etiquetas.id", ondelete="CASCADE"), primary_key=True
    )


class ReferenciaNormativa(UUIDPrimaryKey, Base):
    __tablename__ = "referencias_normativas"

    documento_origen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
    )
    documento_destino_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="SET NULL")
    )
    articulo_origen_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("articulos.id", ondelete="SET NULL")
    )
    tipo: Mapped[str] = mapped_column(String(60), nullable=False, default="cita")


class JurisprudenciaRelacionada(UUIDPrimaryKey, Base):
    __tablename__ = "jurisprudencia_relacionada"

    documento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
    )
    documento_relacionado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
    )
    motivo: Mapped[str | None] = mapped_column(String(255))


class Precedente(UUIDPrimaryKey, Base):
    __tablename__ = "precedentes"

    documento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
    )
    tema: Mapped[str] = mapped_column(String(200), nullable=False)
    resumen: Mapped[str] = mapped_column(Text, nullable=False, default="")
