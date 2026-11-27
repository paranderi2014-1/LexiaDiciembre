"""Otorga el rol `admin` a un usuario ya autenticado al menos una vez (§7, §13).

    python -m scripts.promote_admin --email persona@dominio.com
    python -m scripts.promote_admin --uid <firebase_uid>
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.users import Rol, Usuario, UsuarioRol


async def _promote(email: str | None, uid: str | None) -> str:
    async with SessionLocal() as session:
        filtro = Usuario.email == email if email else Usuario.firebase_uid == uid
        usuario = (await session.execute(select(Usuario).where(filtro))).scalar_one_or_none()
        if usuario is None:
            return "Usuario no encontrado: debe iniciar sesión una vez antes de promoverlo."

        rol = (await session.execute(select(Rol).where(Rol.nombre == "admin"))).scalar_one_or_none()
        if rol is None:
            return "El rol 'admin' no existe: aplique primero las migraciones."

        existente = (
            await session.execute(
                select(UsuarioRol).where(
                    UsuarioRol.usuario_id == usuario.id, UsuarioRol.rol_id == rol.id
                )
            )
        ).scalar_one_or_none()
        if existente is not None:
            return f"{usuario.email or usuario.firebase_uid} ya es admin."

        session.add(UsuarioRol(usuario_id=usuario.id, rol_id=rol.id))
        await session.commit()
        return f"Rol admin otorgado a {usuario.email or usuario.firebase_uid}."


def main() -> None:
    parser = argparse.ArgumentParser(description="Promover un usuario a administrador")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--email")
    grupo.add_argument("--uid")
    args = parser.parse_args()

    print(asyncio.run(_promote(args.email, args.uid)))


if __name__ == "__main__":
    main()
