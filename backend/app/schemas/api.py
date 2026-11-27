"""Esquemas Pydantic de entrada y salida."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Identidad (§7) ---------------------------------------------------------
class ProfileOut(ORMModel):
    id: uuid.UUID
    email: str | None = None
    nombre: str | None = None
    activo: bool
    roles: list[str] = []
    permisos: list[str] = []


class SessionOut(BaseModel):
    perfil: ProfileOut
    autenticado: bool = True


# --- Catálogo (§13) ---------------------------------------------------------
class FuenteOut(ORMModel):
    codigo: str
    nombre: str
    url_base: str


class DocumentoOut(ORMModel):
    id: uuid.UUID
    tipo: str
    numero: str | None = None
    titulo: str
    fecha_publicacion: date | None = None
    fecha_vigencia: date | None = None
    estado: str
    url_original: str
    fuente: FuenteOut | None = None


class ArticuloOut(ORMModel):
    id: uuid.UUID
    documento_id: uuid.UUID
    numero: str
    titulo: str | None = None
    texto: str


class DocumentoDetalleOut(DocumentoOut):
    texto: str
    articulos: list[ArticuloOut] = []


class DocumentoPagina(BaseModel):
    total: int
    limite: int
    desplazamiento: int
    items: list[DocumentoOut]


class FragmentoOut(BaseModel):
    fragmento_id: uuid.UUID
    documento_id: uuid.UUID
    titulo: str
    tipo: str
    numero: str | None = None
    articulo: str | None = None
    fuente: str
    url: str
    score: float
    texto: str


class BusquedaOut(BaseModel):
    termino: str
    total: int
    modo_vectorial: bool
    items: list[FragmentoOut]


# --- Chat (§13) -------------------------------------------------------------
class ChatRequest(BaseModel):
    pregunta: str = Field(min_length=3, max_length=4000)
    canal: Literal["web", "android", "api"] = "web"


class FuenteCitada(BaseModel):
    fragmento_id: str
    documento_id: str
    titulo: str
    tipo: str
    numero: str | None = None
    articulo: str | None = None
    fuente: str
    url: str
    fecha_publicacion: str | None = None


class ChatResponse(BaseModel):
    consulta_id: str
    respuesta: str
    fuentes: list[FuenteCitada] = []
    fundamento_suficiente: bool
    modelo: str
    desde_cache: bool
    latencia_ms: int


class ConsultaOut(BaseModel):
    id: uuid.UUID
    pregunta: str
    canal: str
    desde_cache: bool
    creada_en: datetime
    respuesta: str | None = None
    fundamento_suficiente: bool | None = None


# --- Administración (§13) ---------------------------------------------------
class UsuarioAdminOut(BaseModel):
    id: uuid.UUID
    email: str | None = None
    nombre: str | None = None
    activo: bool
    roles: list[str] = []
    last_login_at: datetime | None = None


class UsuarioAdminPatch(BaseModel):
    activo: bool | None = None
    roles: list[str] | None = None


# --- Salud (§13) ------------------------------------------------------------
class HealthOut(BaseModel):
    status: Literal["ok", "degradado"]
    version: str
    dependencias: dict[str, str]
    configuracion: dict[str, bool]
