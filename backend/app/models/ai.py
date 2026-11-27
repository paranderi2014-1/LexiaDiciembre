"""Consultas, respuestas, auditoría y caché (Plan Maestro §12, §14)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.base import UUIDPrimaryKey


class Consulta(UUIDPrimaryKey, Base):
    __tablename__ = "consultas"

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    pregunta: Mapped[str] = mapped_column(Text, nullable=False)
    canal: Mapped[str] = mapped_column(String(30), nullable=False, default="web")
    desde_cache: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RespuestaIA(UUIDPrimaryKey, Base):
    __tablename__ = "respuestas_ia"

    consulta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultas.id", ondelete="CASCADE"), nullable=False
    )
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)
    fundamento_suficiente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fuentes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    latencia_ms: Mapped[int | None] = mapped_column(Integer)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Auditoria(UUIDPrimaryKey, Base):
    __tablename__ = "auditoria"

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    accion: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entidad: Mapped[str | None] = mapped_column(String(80))
    entidad_id: Mapped[str | None] = mapped_column(String(80))
    metadatos: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class CacheRespuesta(UUIDPrimaryKey, Base):
    __tablename__ = "cache_respuestas"

    hash_pregunta: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    respuesta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("respuestas_ia.id", ondelete="CASCADE"), nullable=False
    )
    indice_version: Mapped[str] = mapped_column(String(64), nullable=False)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expira_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Configuracion(Base):
    __tablename__ = "configuraciones"

    clave: Mapped[str] = mapped_column(String(120), primary_key=True)
    valor: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class EstadisticaBusqueda(UUIDPrimaryKey, Base):
    __tablename__ = "estadisticas_busqueda"

    consulta_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultas.id", ondelete="SET NULL")
    )
    termino: Mapped[str] = mapped_column(String(400), nullable=False)
    resultados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
