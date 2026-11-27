# Base de datos jurídica

PostgreSQL 16 con las extensiones `uuid-ossp`, `vector` y `pg_trgm`.

## Tablas

| Grupo | Tablas |
|---|---|
| Fuentes y documentos | `fuentes`, `documentos`, `versiones_documento`, `archivos` |
| Estructura jurídica | `articulos`, `fragmentos`, `etiquetas`, `documento_etiqueta`, `referencias_normativas`, `jurisprudencia_relacionada`, `precedentes` |
| Usuarios y permisos | `usuarios`, `roles`, `permisos`, `rol_permiso`, `usuario_rol` |
| IA y control | `consultas`, `respuestas_ia`, `auditoria`, `cache_respuestas`, `configuraciones`, `estadisticas_busqueda` |

## Decisiones técnicas

- **Embeddings en `halfvec(3072)`.** `text-embedding-3-large` produce 3072 dimensiones.
  El índice HNSW de pgvector admite hasta 2000 dimensiones con `vector` y 4000 con
  `halfvec`, así que la columna usa `halfvec` con `halfvec_cosine_ops`. Si cambia el
  modelo o la dimensión, hay que regenerar vectores e índices (§10).
- **`fragmentos.texto_tsv`** es una columna generada `to_tsvector('spanish', texto)` con
  índice GIN: la búsqueda textual siempre ve el texto vigente.
- **Deduplicación por `hash`** del texto normalizado (sin depender del maquetado del
  portal). Un cambio real crea una fila en `versiones_documento` y reindexa.
- **Fragmentación**: 500 tokens con 100 de solapamiento (`CHUNK_TOKENS`,
  `CHUNK_OVERLAP_TOKENS`), conservando el vínculo con documento y artículo.
- **Roles iniciales**: `admin` (todos los permisos), `editor` (carga y versiona) y
  `usuario` (chat y consulta). Se asignan en la migración `0001_esquema_inicial`.

## Operación

```bash
# aplicar migraciones (servicio migrate del compose)
alembic upgrade head

# carga manual de una fuente
python -m scripts.load_sources bacn --limite 5

# actualización completa (también corre a las 03:00 de America/Asuncion)
python -m app.jobs.scheduler --once
```
