# Auditoría del sistema actual — Chat y Motor de Investigación Jurídica

## 1. Arquitectura actual

### Frontend (TanStack Start + React 19 + Vite)
- **Chat**: `src/components/lexia/LexiaChat.tsx` — interfaz con selectores de fuero y modo de análisis, streaming NDJSON vía `/api/lexia`.
- **Route handler**: `src/routes/api/lexia.ts` — streaming directo a OpenAI Responses API + Firecrawl search + Supabase para persistencia.
- **Análisis (6 modos)**: `src/lib/lexia-analysis.ts` — WEB_SEARCH, EXPLAIN, DEEP_RESEARCH, CONTRACT_REVIEW, DRAFT_PREP, CASE_SUMMARY.
- **Firecrawl (frontend)**: `src/lib/firecrawl.server.ts` — search + scrape contra `api.firecrawl.dev/v2`.
- **API client**: `src/lib/api.ts` — cliente tipado para FastAPI (catálogo público + cuenta).
- **Live relay**: `src/lib/live-relay.server.ts` — WebSocket para voz en tiempo real (Gemini Live vía Lovable gateway).

### Backend (FastAPI + PostgreSQL 16 + pgvector + Redis)
- **Chat**: `backend/app/routes/chat.py` → `POST /api/chat` — RAG no-streaming, requiere Firebase auth.
- **Análisis**: `backend/app/routes/analysis.py` — 7 endpoints (contract-review, document-comparison, generate-draft, hearing-prep, case-extraction, analogous-cases, client-lead-triage).
- **Catálogo**: `backend/app/routes/catalog.py` — leyes, documentos, jurisprudencia (público).
- **RAG**: `backend/app/services/rag.py` — recuperación híbrida + modelo + citas + caché.
- **Búsqueda**: `backend/app/services/search.py` — BM25 (ts_rank_cd) + vectorial (pgvector halfvec cosine).
- **Embeddings**: `backend/app/services/embeddings.py` — OpenAI text-embedding-3-large (3072 dim).
- **ETL**: `backend/app/jobs/etl.py` — extract → transform → load con scrapers por portal.
- **Scrapers**: `backend/app/scrapers/portals.py` — BACN, CSJ Legislación, CSJ Jurisprudencia, PJ.
- **Scheduler**: `backend/app/jobs/scheduler.py` — actualización automática diaria.
- **Modelos**: `backend/app/models/catalog.py` — Fuente, Documento, VersionDocumento, Articulo, Fragmento, ReferenciaNormativa, etc.
- **Admin**: `backend/app/routes/admin.py` — usuarios, roles, auditoría.

## 2. Matriz de funcionalidades

| # | Funcionalidad | Estado | Detalle |
|---|---|---|---|
| **CHAT** | | | |
| 1 | Interfaz de conversación | EXISTENTE | Layout con header, mensajes, composer. No ocupa pantalla completa. |
| 2 | Streaming de respuestas | EXISTENTE | NDJSON vía `/api/lexia` → OpenAI Responses API. |
| 3 | Selectores de fuero y modo | EXISTENTE | 6 modos en `lexia-analysis.ts`. |
| 4 | Auto-scroll al último mensaje | EXISTENTE | `ConversationScrollButton` de ai-elements. |
| 5 | Persistencia de historial | EXISTENTE | Supabase `lexia_threads` + `lexia_messages`. |
| 6 | Fecha/hora en mensajes | PENDIENTE | No se muestran timestamps en la UI. |
| 7 | Pantalla completa sin columnas | PENDIENTE | El chat tiene header y área lateral de selectores. |
| 8 | Botones solo-icono | PENDIENTE | Los selectores muestran texto. |
| 9 | Menú hamburguesa superior-izq | PENDIENTE | No existe. |
| 10 | Chat temporal (sup-der) | PENDIENTE | No existe. |
| 11 | Adjuntar archivo (dispositivo/almacenamiento) | PENDIENTE | No existe. |
| 12 | Botón Analizar con submenú | PARCIAL | Los 6 modos son botones de texto, no un menú desplegable. |
| 13 | Botón más opciones (...) | PENDIENTE | No existe. |
| 14 | Botón micrófono circular negro | PENDIENTE | No existe. |
| **VOZ** | | | |
| 15 | Reconocimiento de voz (STT) | PENDIENTE | No implementado. |
| 16 | Síntesis de voz (TTS) | PENDIENTE | No implementado (live-relay existe pero no conectado al chat). |
| 17 | Controles play/pausar/detener | PENDIENTE | No existen. |
| 18 | Selección de voz | PENDIENTE | No existe. |
| **FIRECRAWL** | | | |
| 19 | Search | EXISTENTE (frontend) | `firecrawl.server.ts` — search en dominios oficiales. |
| 20 | Scrape | EXISTENTE (frontend) | `firecrawl.server.ts` — scrape de URL oficial. |
| 21 | Map | PENDIENTE | No implementado. |
| 22 | Crawl | PENDIENTE | No implementado. |
| 23 | JSON extraction | PENDIENTE | No implementado. |
| 24 | Monitor / Change Tracking | PENDIENTE | No implementado. |
| 25 | Firecrawl en backend (FastAPI) | PENDIENTE | Solo existe en frontend. Debe pasar por FastAPI. |
| **MOTOR DE INVESTIGACIÓN** | | | |
| 26 | Identificación de leyes/decretos/acordadas | EXISTENTE | Scrapers detectan tipo + número. |
| 27 | Extracción de metadatos | EXISTENTE | Título, número, fecha, fuente, URL. |
| 28 | Clasificación por fueros | PARCIAL | El campo `fuero` existe pero no se clasifica automáticamente. |
| 29 | Fragmentación documental | EXISTENTE | `chunk_text` en ETL. |
| 30 | Generación de embeddings | EXISTENTE | OpenAI text-embedding-3-large, halfvec. |
| 31 | Búsqueda híbrida léxica + semántica | EXISTENTE | BM25 + vectorial en `search.py`. |
| 32 | Verificación de citas y enlaces | EXISTENTE | `citaciones.py` + `isOfficialUrl`. |
| 33 | Registro de versiones | EXISTENTE | `VersionDocumento` en ETL. |
| 34 | Relaciones entre normas | PARCIAL | Modelo `ReferenciaNormativa` existe, no se puebla. |
| 35 | Detección y comparación de cambios | PARCIAL | ETL guarda versión anterior, no compara contenido. |
| 36 | Conexión motor → chat | PARCIAL | RAG del backend no está conectado al chat del frontend. |
| **CONTROL DE ACTUALIZACIONES** | | | |
| 37 | Circuito de revisión humana | PENDIENTE | ETL actualiza directamente sin revisión. |
| 38 | Clasificación de cambios | PENDIENTE | No clasifica tipo de cambio. |
| 39 | Trazabilidad de versiones | EXISTENTE | `VersionDocumento` conserva versiones anteriores. |
| 40 | Aprobación antes de actualizar índice | PENDIENTE | No existe workflow de aprobación. |
| **PANEL TÉCNICO** | | | |
| 41 | Estado de Firecrawl | PENDIENTE | No existe. |
| 42 | Últimas tareas | PENDIENTE | No existe. |
| 43 | Fuentes consultadas | PARCIAL | `/api/fuentes` muestra conteos. |
| 44 | Documentos extraídos | PARCIAL | `/api/documentos` lista documentos. |
| 45 | Errores y reintentos | PENDIENTE | ETL reporta errores pero no se exponen. |
| 46 | Consumo y créditos | PENDIENTE | No se trackea. |
| 47 | Documentos pendientes de revisión | PENDIENTE | No existe. |
| 48 | Estado de embeddings/indexación | PENDIENTE | No existe. |
| 49 | Historial de modificaciones | PARCIAL | `Auditoria` registra acciones pero no cambios documentales. |
| **PRUEBAS** | | | |
| 50 | Pruebas E2E de los 6 modos | PENDIENTE | No existen pruebas de integración frontend-backend por modo. |
| 51 | Pruebas de autenticación | PENDIENTE | Sin credenciales Firebase. |
| 52 | Pruebas de persistencia | PENDIENTE | No verificadas. |
| 53 | Pruebas de fuentes y citas | PENDIENTE | No verificadas. |
| 54 | Pruebas de archivos adjuntos | PENDIENTE | No existe la funcionalidad. |

## 3. Credenciales necesarias

| Variable | Estado | Propósito |
|---|---|---|
| `FIREBASE_PROJECT_ID` | PENDIENTE | Verificación de ID tokens. |
| `FIREBASE_CREDENTIALS` | PENDIENTE | Cuenta de servicio. |
| `OPENAI_API_KEY` | PENDIENTE | Chat + embeddings + análisis. |
| `FIRECRAWL_API_KEY` | PENDIENTE | Motor de investigación documental. |
| `SUPABASE_URL` | CONFIGURADO | Persistencia del chat (frontend). |
| `SUPABASE_PUBLISHABLE_KEY` | CONFIGURADO | Auth del chat (frontend). |

## 4. Adaptaciones necesarias

1. **Chat**: Rediseñar a pantalla completa con layout especificado, botones solo-icono, submenús.
2. **Voz**: Implementar STT (Web Speech API) + TTS (speechSynthesis) en el frontend.
3. **Firecrawl backend**: Crear servicio + rutas en FastAPI para map/search/scrape/crawl/json/monitor.
4. **Control de actualizaciones**: Modelo de revisión + workflow de aprobación en ETL.
5. **Panel técnico**: Nuevos endpoints para monitoreo de Firecrawl, ETL, embeddings, revisiones.
6. **Conexión motor→chat**: El RAG del backend debe alimentar las respuestas del chat del frontend.
