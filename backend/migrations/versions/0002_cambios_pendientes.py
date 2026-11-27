"""Tabla de cambios pendientes de revisión humana.

Revision ID: 0002_cambios_pendientes
Revises: 0001_esquema_inicial
Create Date: 2026-11-27

Crea la tabla `cambios_pendientes` para el circuito de control de actualizaciones:
los cambios detectados por el ETL ingresan aquí en estado `pendiente` y solo se
aplican al documento vigente tras aprobación humana.
"""

from __future__ import annotations

from alembic import op

revision = "0002_cambios_pendientes"
down_revision = "0001_esquema_inicial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Añadir permiso admin.firecrawl
    op.execute(
        "INSERT INTO permisos (id, nombre, descripcion) "
        "VALUES (gen_random_uuid(), 'admin.firecrawl', 'Operaciones avanzadas de Firecrawl (crawl, extract)') "
        "ON CONFLICT (nombre) DO NOTHING"
    )
    op.execute(
        "INSERT INTO rol_permiso (rol_id, permiso_id) "
        "SELECT r.id, p.id FROM roles r CROSS JOIN permisos p "
        "WHERE r.nombre = 'admin' AND p.nombre = 'admin.firecrawl' "
        "ON CONFLICT DO NOTHING"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cambios_pendientes (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            documento_id    UUID REFERENCES documentos(id) ON DELETE SET NULL,
            fuente_codigo   VARCHAR(40)  NOT NULL,
            url             VARCHAR(1000) NOT NULL,
            titulo          VARCHAR(600) NOT NULL DEFAULT '',
            hash_anterior   VARCHAR(64),
            hash_nuevo      VARCHAR(64)  NOT NULL,
            texto_nuevo     TEXT NOT NULL DEFAULT '',
            texto_anterior  TEXT NOT NULL DEFAULT '',
            tipo_cambio     VARCHAR(40),
            estado          VARCHAR(20)  NOT NULL DEFAULT 'pendiente',
            acto_sustento   VARCHAR(600),
            revisado_por     UUID REFERENCES usuarios(id) ON DELETE SET NULL,
            revisado_en     TIMESTAMPTZ,
            motivo_revision TEXT,
            metadatos       JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS cambios_pendientes_estado_idx ON cambios_pendientes (estado)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS cambios_pendientes_documento_idx ON cambios_pendientes (documento_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cambios_pendientes")
