"""Esquema inicial de la API central.

Revision ID: 0001_esquema_inicial
Revises:
Create Date: 2026-11-27

Crea las extensiones requeridas (§5) y el esquema declarado en `app/models`,
más los datos mínimos de operación: roles, permisos y fuentes oficiales (§8).
"""

from __future__ import annotations

from alembic import op

revision = "0001_esquema_inicial"
down_revision = None
branch_labels = None
depends_on = None

PERMISOS = [
    ("chat.usar", "Formular consultas jurídicas al motor RAG."),
    ("documentos.leer", "Consultar documentos, leyes y artículos."),
    ("documentos.escribir", "Cargar y versionar documentos jurídicos."),
    ("admin.usuarios", "Administrar usuarios y roles."),
    ("admin.fuentes", "Administrar fuentes y actualizaciones."),
    ("admin.auditoria", "Consultar el registro de auditoría."),
]

ROLES = [
    ("admin", "Acceso completo a la plataforma."),
    ("editor", "Carga y mantiene la base jurídica."),
    ("usuario", "Consulta la base jurídica y usa el chat."),
]

ROL_PERMISOS = {
    "admin": [nombre for nombre, _ in PERMISOS],
    "editor": ["chat.usar", "documentos.leer", "documentos.escribir"],
    "usuario": ["chat.usar", "documentos.leer"],
}

FUENTES = [
    ("bacn", "BACN — Leyes Paraguayas", "https://www.bacn.gov.py/leyes-paraguayas", "portal"),
    ("csj_legislacion", "CSJ — Legislación", "https://www.csj.gov.py/legislacion/", "portal"),
    ("csj_jurisprudencia", "CSJ — Jurisprudencia", "https://www.csj.gov.py/jurisprudencia/", "portal"),
    ("pj", "Poder Judicial", "https://www.pj.gov.py/", "portal"),
]


def _quote(value: str) -> str:
    return value.replace("'", "''")


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    from app.database.session import Base
    import app.models  # noqa: F401 - registra el metadata completo

    Base.metadata.create_all(bind=op.get_bind())

    for nombre, descripcion in ROLES:
        op.execute(
            "INSERT INTO roles (id, nombre, descripcion) "
            f"VALUES (gen_random_uuid(), '{_quote(nombre)}', '{_quote(descripcion)}') "
            "ON CONFLICT (nombre) DO NOTHING"
        )

    for nombre, descripcion in PERMISOS:
        op.execute(
            "INSERT INTO permisos (id, nombre, descripcion) "
            f"VALUES (gen_random_uuid(), '{_quote(nombre)}', '{_quote(descripcion)}') "
            "ON CONFLICT (nombre) DO NOTHING"
        )

    for rol, permisos in ROL_PERMISOS.items():
        lista = ", ".join(f"'{_quote(p)}'" for p in permisos)
        op.execute(
            "INSERT INTO rol_permiso (rol_id, permiso_id) "
            "SELECT r.id, p.id FROM roles r CROSS JOIN permisos p "
            f"WHERE r.nombre = '{_quote(rol)}' AND p.nombre IN ({lista}) "
            "ON CONFLICT DO NOTHING"
        )

    for codigo, nombre, url, tipo in FUENTES:
        op.execute(
            "INSERT INTO fuentes (id, codigo, nombre, url_base, tipo, activo, created_at, updated_at) "
            f"VALUES (gen_random_uuid(), '{_quote(codigo)}', '{_quote(nombre)}', "
            f"'{_quote(url)}', '{_quote(tipo)}', true, now(), now()) "
            "ON CONFLICT (codigo) DO NOTHING"
        )


def downgrade() -> None:
    from app.database.session import Base
    import app.models  # noqa: F401

    Base.metadata.drop_all(bind=op.get_bind())
