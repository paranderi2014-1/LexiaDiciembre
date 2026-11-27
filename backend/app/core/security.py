"""Verificación de identidad Firebase y autorización por permisos (Plan Maestro §7).

Reglas aplicadas:
- El UID sale del token verificado; nunca del cuerpo de la petición.
- Sin credenciales de Firebase la API responde 503: no se degrada a identidad anónima.
- Los roles y permisos viven en PostgreSQL y se aplican en el backend.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_session
from app.models.users import Rol, Usuario, UsuarioRol

DEFAULT_ROLE = "usuario"


class AuthNotConfigured(RuntimeError):
    """Falta la configuración de Firebase Admin SDK."""


class InvalidToken(RuntimeError):
    """El ID token no es válido, expiró o fue revocado."""


def _ensure_firebase_app() -> None:
    import firebase_admin
    from firebase_admin import credentials

    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    if not settings.auth_configured:
        raise AuthNotConfigured(
            "FIREBASE_PROJECT_ID y FIREBASE_CREDENTIALS son obligatorios para autenticar."
        )

    raw = settings.firebase_credentials or ""
    if os.path.isfile(raw):
        cred = credentials.Certificate(raw)
    else:
        cred = credentials.Certificate(json.loads(raw))

    firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})


def verify_firebase_token(token: str) -> dict:
    """Verifica el ID token con Firebase Admin SDK y devuelve sus claims."""
    from firebase_admin import auth as firebase_auth

    _ensure_firebase_app()
    try:
        return firebase_auth.verify_id_token(token, check_revoked=True)
    except Exception as exc:  # noqa: BLE001 - se normaliza a un error de autenticación
        raise InvalidToken(str(exc)) from exc


@dataclass(slots=True)
class Identity:
    usuario: Usuario
    roles: list[str] = field(default_factory=list)
    permisos: set[str] = field(default_factory=set)

    @property
    def id(self) -> uuid.UUID:
        return self.usuario.id

    def has_permission(self, nombre: str) -> bool:
        return nombre in self.permisos


def _bearer_token(request: Request) -> str:
    header = request.headers.get("authorization") or ""
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el encabezado Authorization: Bearer <Firebase_ID_Token>.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()


async def _load_identity(session: AsyncSession, claims: dict) -> Identity:
    uid = claims.get("uid") or claims.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="El token no contiene un UID.")

    usuario = (
        await session.execute(select(Usuario).where(Usuario.firebase_uid == uid))
    ).scalar_one_or_none()

    if usuario is None:
        usuario = Usuario(
            firebase_uid=uid,
            email=claims.get("email"),
            nombre=claims.get("name"),
            last_login_at=datetime.now(timezone.utc),
        )
        session.add(usuario)
        await session.flush()
        rol = (await session.execute(select(Rol).where(Rol.nombre == DEFAULT_ROLE))).scalar_one_or_none()
        if rol is not None:
            session.add(UsuarioRol(usuario_id=usuario.id, rol_id=rol.id))
            await session.flush()
        await session.refresh(usuario)
    else:
        usuario.last_login_at = datetime.now(timezone.utc)
        if claims.get("email") and usuario.email != claims.get("email"):
            usuario.email = claims.get("email")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="La cuenta está deshabilitada.")

    roles = [ur.rol.nombre for ur in usuario.roles if ur.rol is not None]
    permisos = {rp.permiso.nombre for ur in usuario.roles for rp in (ur.rol.permisos if ur.rol else [])}
    return Identity(usuario=usuario, roles=roles, permisos=permisos)


async def get_current_identity(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Identity:
    token = _bearer_token(request)
    try:
        claims = verify_firebase_token(token)
    except AuthNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Autenticación no configurada: {exc}",
        ) from exc
    except InvalidToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"ID token inválido: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    identity = await _load_identity(session, claims)
    await session.commit()
    return identity


def require_permission(nombre: str):
    """Dependencia que exige un permiso concreto además de la identidad válida."""

    async def _guard(identity: Identity = Depends(get_current_identity)) -> Identity:
        if not identity.has_permission(nombre):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido: {nombre}.",
            )
        return identity

    return _guard
