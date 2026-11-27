# LexIAParaguay

Plataforma jurídica para Paraguay. Este repositorio parte del código fuente exportado desde Lovable y conserva sus rutas, componentes, módulos, calculadoras, chat, expedientes y migraciones. Se incorporó una capa de diseño premium, tema claro/oscuro persistente, autenticación OAuth estándar de Supabase, chat con OpenAI Responses API y un servidor MCP HTTP para investigación con Firecrawl limitada a fuentes jurídicas oficiales paraguayas.

## Requisitos

- Node.js 20.19+ o 22.12+.
- npm.
- Proyecto Supabase propio con Auth habilitado y las migraciones SQL aplicadas.
- Clave de OpenAI para el chat jurídico.
- Clave de Firecrawl para las herramientas de búsqueda y extracción MCP.

## Inicio local

```bash
cp .env.example .env
# Completar las variables de entorno del archivo .env
npm install
npm run dev
```

## Variables de entorno

Copiar `.env.example` y completar:

| Variable | Uso | Exposición |
|---|---|---|
| `SUPABASE_URL` | Supabase server-side | Servidor |
| `SUPABASE_PUBLISHABLE_KEY` | Clave pública de Supabase | Cliente/servidor |
| `VITE_SUPABASE_URL` | URL de Supabase para el navegador | Cliente |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Clave publicable de Supabase | Cliente |
| `OPENAI_API_KEY` | Chat e investigación jurídica | Solo servidor |
| `OPENAI_MODEL` | Modelo Responses API (por defecto `gpt-6.2-astra`) | Solo servidor |
| `OPENAI_RESPONSES_URL` | Endpoint Responses API | Solo servidor |
| `FIRECRAWL_API_KEY` | Búsqueda y extracción oficial | Solo servidor |
| `MCP_ACCESS_TOKEN` | Autenticación Bearer del endpoint MCP | Solo servidor |

Nunca colocar `OPENAI_API_KEY`, `FIRECRAWL_API_KEY` ni `MCP_ACCESS_TOKEN` en variables `VITE_*`, código del navegador o repositorios públicos.

## Integración OpenAI

El endpoint `/api/lexia` utiliza OpenAI Responses API desde el servidor. Si `FIRECRAWL_API_KEY` está configurada, primero obtiene resultados preliminares de Firecrawl; luego ejecuta `web_search` de OpenAI restringido a `bacn.gov.py`, `pj.gov.py`, `csj.gov.py` y `apps.csj.gov.py`. El asistente no guarda una respuesta final si la investigación no se completa o no produce al menos una cita de un dominio autorizado.

## Servidor MCP de LexIAParaguay

Endpoint: `/api/mcp` (MCP Streamable HTTP stateless, JSON-RPC 2.0; protocolo actual `2026-07-28`, con compatibilidad para `2025-11-25`, `2025-06-18` y `2025-03-26`).

Autenticación requerida:

```http
Authorization: Bearer <MCP_ACCESS_TOKEN>
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/list
Accept: application/json, text/event-stream
Content-Type: application/json
```

Métodos disponibles:
- `tools/list` y `tools/call` en modo stateless actual.
- `ping`.
- `initialize` y `notifications/initialized` para clientes de versiones anteriores.
- `tools/list`
- `tools/call`

Herramientas:
- `paraguay_legal_search`: busca en BACN, Poder Judicial y CSJ mediante Firecrawl.
- `paraguay_legal_scrape`: extrae una URL HTTPS de esos dominios oficiales.

La ruta rechaza solicitudes sin token y limita la extracción a los dominios oficiales permitidos. Generá el token con `openssl rand -hex 32` y guardalo como secreto de servidor. Si el cliente envía `Origin`, declarà los orígenes exactos permitidos en `MCP_ALLOWED_ORIGINS` (separados por coma). Para el protocolo actual, incluí `_meta.io.modelcontextprotocol/protocolVersion: "2026-07-28"` dentro de `params`, además de `MCP-Protocol-Version` y `Mcp-Method` en los encabezados; para `tools/call`, agregá también `Mcp-Name` con el nombre de la herramienta.

## Supabase

Aplicar en el proyecto Supabase las migraciones de `drizzle/migrations/` en orden. Las políticas RLS incluidas aíslan conversaciones y expedientes por usuario. Revisar también el bucket `lexia-case-files` y las políticas de Storage antes de producción. Configurar el proveedor Google OAuth desde Supabase Auth si se habilita ese acceso.

## API central (Plan Maestro)

`backend/` implementa la arquitectura central del Plan Maestro sin reemplazar nada del
sitio actual: FastAPI + SQLAlchemy async + Alembic sobre PostgreSQL 16 con pgvector,
Firebase Authentication para identidad, Redis para caché y un planificador diario de
actualización de fuentes oficiales.

```bash
# Con el compose del entorno Base44 ya levantado:
make test        # 27 pruebas de API, búsqueda híbrida, citas y ETL
make test-web    # pruebas del frontend (vitest bajo Node)
make update      # actualización de fuentes (BACN, CSJ, PJ)
```

Documentación: `docs/arquitectura.md`, `docs/api.md`, `docs/base_datos.md`,
`docs/seguridad.md`. Variables nuevas en `backend/.env.example`.

Sin `FIREBASE_*` la API responde 503 en las rutas protegidas (no hay modo anónimo) y
`/api/health` informa `firebase: no_configurado`. Sin `OPENAI_API_KEY` la búsqueda
textual sigue operativa, pero `/api/chat` responde 503 al no poder generar respuestas.

## Comprobaciones

```bash
npm run lint
npm test
npm run build
```

No se incluyen secretos ni una copia de los datos alojados en Supabase. La exportación de código no exporta automáticamente usuarios, registros de base de datos, buckets, claves o configuraciones de terceros.

## Material de referencia

`reference-materials/` conserva el prototipo HTML y el ZIP visual complementario que venían dentro del archivo de origen. Son referencias, no recursos cargados automáticamente por la aplicación.

## Estado de funciones externas

Las rutas y adaptadores de OpenAI y Firecrawl requieren claves válidas y configuración del proveedor. El servidor MCP queda protegido por token. La voz en tiempo real conserva el relay anterior basado en el gateway de Lovable y todavía requiere migración a un proveedor Realtime independiente antes de considerar la independencia total. Las conexiones autenticadas a sistemas CSJ no se simulan ni se automatizan sin autorización oficial.
