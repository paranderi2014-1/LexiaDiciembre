"""Administración de usuarios, roles y auditoría (§13)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Identity, require_permission
from app.database.session import get_session
from app.models.ai import Auditoria
from app.models.users import Rol, Usuario, UsuarioRol
from app.schemas.api import UsuarioAdminOut, UsuarioAdminPatch
from app.services import auditoria

router = APIRouter(prefix="/api/admin", tags=["administración"])


def _to_out(usuario: Usuario) -> UsuarioAdminOut:
    return UsuarioAdminOut(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        activo=usuario.activo,
        roles=[ur.rol.nombre for ur in usuario.roles if ur.rol],
        last_login_at=usuario.last_login_at,
    )


@router.get("/users", response_model=list[UsuarioAdminOut])
async def list_users(
    _: Identity = Depends(require_permission("admin.usuarios")),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[UsuarioAdminOut]:
    rows = (await session.execute(select(Usuario).order_by(Usuario.created_at.desc()).limit(limit)))
    return [_to_out(usuario) for usuario in rows.scalars().all()]


@router.patch("/users/{usuario_id}", response_model=UsuarioAdminOut)
async def update_user(
    usuario_id: uuid.UUID,
    payload: UsuarioAdminPatch,
    identity: Identity = Depends(require_permission("admin.usuarios")),
    session: AsyncSession = Depends(get_session),
) -> UsuarioAdminOut:
    usuario = (
        await session.execute(select(Usuario).where(Usuario.id == usuario_id))
    ).scalar_one_or_none()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if payload.activo is not None:
        usuario.activo = payload.activo

    if payload.roles is not None:
        roles = (
            await session.execute(select(Rol).where(Rol.nombre.in_(payload.roles)))
        ).scalars().all()
        faltantes = set(payload.roles) - {rol.nombre for rol in roles}
        if faltantes:
            raise HTTPException(status_code=400, detail=f"Roles inexistentes: {sorted(faltantes)}")
        usuario.roles.clear()
        await session.flush()
        for rol in roles:
            session.add(UsuarioRol(usuario_id=usuario.id, rol_id=rol.id))

    auditoria.registrar(
        session,
        "admin.usuario_actualizado",
        usuario_id=identity.id,
        entidad="usuarios",
        entidad_id=str(usuario.id),
        metadatos={"activo": payload.activo, "roles": payload.roles},
    )
    await session.commit()
    await session.refresh(usuario)
    return _to_out(usuario)


@router.get("/auditoria")
async def list_auditoria(
    _: Identity = Depends(require_permission("admin.auditoria")),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    rows = (
        await session.execute(select(Auditoria).order_by(Auditoria.creada_en.desc()).limit(limit))
    ).scalars().all()
    return [
        {
            "id": str(row.id),
            "accion": row.accion,
            "usuario_id": str(row.usuario_id) if row.usuario_id else None,
            "entidad": row.entidad,
            "entidad_id": row.entidad_id,
            "metadatos": row.metadatos,
            "creada_en": row.creada_en.isoformat(),
        }
        for row in rows
    ]
