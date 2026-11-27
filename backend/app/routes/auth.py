"""Sesión y perfil autenticados (§7.2, §13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import Identity, get_current_identity
from app.schemas.api import ProfileOut, SessionOut
from app.services import auditoria
from app.database.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api", tags=["autenticación"])


def _profile(identity: Identity) -> ProfileOut:
    return ProfileOut(
        id=identity.id,
        email=identity.usuario.email,
        nombre=identity.usuario.nombre,
        activo=identity.usuario.activo,
        roles=identity.roles,
        permisos=sorted(identity.permisos),
    )


@router.post("/auth/session", response_model=SessionOut)
async def create_session(
    identity: Identity = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session),
) -> SessionOut:
    """Verifica el ID token, vincula el UID con su perfil y registra el acceso."""
    auditoria.registrar(
        session,
        "auth.sesion",
        usuario_id=identity.id,
        entidad="usuarios",
        entidad_id=str(identity.id),
        metadatos={"roles": identity.roles},
    )
    await session.commit()
    return SessionOut(perfil=_profile(identity))


@router.get("/profile", response_model=ProfileOut)
async def read_profile(identity: Identity = Depends(get_current_identity)) -> ProfileOut:
    return _profile(identity)
