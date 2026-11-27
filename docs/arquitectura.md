# Arquitectura central — LexIAParaguay

Implementación del Plan Maestro de instalación (v1) sobre el repositorio existente.
**Nada del sitio actual se eliminó**: las rutas, demos, calculadoras, chat y expedientes
siguen funcionando; la API central se agrega como servicio nuevo.

## Capas

| Capa | Implementación | Ruta |
|---|---|---|
| Interfaz web | TanStack Start + React 19 (se conserva la existente) | `src/` |
| API central | Python 3.12 · FastAPI · SQLAlchemy 2 async · Alembic | `backend/` |
| Base jurídica | PostgreSQL 16 + pgvector + pg_trgm | `backend/migrations/` |
| Identidad | Firebase Authentication (ID tokens verificados en el backend) | `backend/app/core/security.py` |
| Caché y coordinación | Redis 7 | `backend/app/services/cache.py` |
| Indexación automática | Scrapers BACN/CSJ/PJ + ETL + planificador diario | `backend/app/scrapers`, `backend/app/jobs` |

## Flujo

```
Web / Android → Firebase Auth → ID token
      → FastAPI (verify_id_token) → perfil + roles/permisos en PostgreSQL
      → búsqueda híbrida (BM25 ts_rank_cd + similitud coseno pgvector)
      → contexto RAG → modelo → validación de citas
      → respuesta + historial + auditoría (+ caché Redis)
```

## Por qué no se reescribió la interfaz

El Plan Maestro (§objetivo, §15) exige preservar la identidad visual y las funciones
existentes y evitar una reconstrucción innecesaria. La web actual se mantiene tal cual;
la conexión de sus pantallas a los endpoints nuevos es el siguiente paso (ver
`docs/api.md`, sección "Pendiente").

## Estado verificado en esta entrega

- Esquema y migraciones Alembic aplicadas sobre PostgreSQL 16 + pgvector.
- Búsqueda híbrida con similitud vectorial real (no una lista sin puntajes).
- Sesión con ID token de Firebase, perfil vinculado al UID, roles y permisos en backend.
- Respuesta de contingencia cuando no hay fundamento documental.
- 27 pruebas de backend y 15 de frontend en verde.

## Pendiente (no se declara hecho)

- Credenciales reales de Firebase y OpenAI (`FIREBASE_*`, `OPENAI_API_KEY`).
- Primera carga masiva de documentos desde los portales oficiales.
- Conexión de las pantallas web al API central y cliente Android.
- Despliegue en Azure (§18) y CI/CD (§18.1).
