"""Usuarios, roles y permisos (Plan Maestro §5, §7).

Firebase Authentication es el proveedor de identidad: `firebase_uid` es el único
vínculo con la cuenta. Aquí nunca se guardan contraseñas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class Usuario(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "usuarios"

    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    nombre: Mapped[str | None] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list["UsuarioRol"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan", lazy="selectin"
    )


class Rol(UUIDPrimaryKey, Base):
    __tablename__ = "roles"

    nombre: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))

    permisos: Mapped[list["RolPermiso"]] = relationship(
        back_populates="rol", cascade="all, delete-orphan", lazy="selectin"
    )


class Permiso(UUIDPrimaryKey, Base):
    __tablename__ = "permisos"

    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))


class RolPermiso(Base):
    __tablename__ = "rol_permiso"

    rol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permiso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True
    )

    rol: Mapped[Rol] = relationship(back_populates="permisos")
    permiso: Mapped[Permiso] = relationship(lazy="joined")


class UsuarioRol(Base):
    __tablename__ = "usuario_rol"
    __table_args__ = (UniqueConstraint("usuario_id", "rol_id", name="usuario_rol_unico"),)

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    rol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )

    usuario: Mapped[Usuario] = relationship(back_populates="roles")
    rol: Mapped[Rol] = relationship(lazy="joined")
