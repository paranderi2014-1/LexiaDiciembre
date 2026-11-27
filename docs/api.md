# API central

Base local: `http://localhost:8000` · Documentación interactiva: `/docs` · OpenAPI: `/openapi.json`

Todas las rutas protegidas exigen `Authorization: Bearer <Firebase_ID_Token>`.

| Método | Endpoint | Permiso | Función |
|---|---|---|---|
| GET | `/api/health` | público | Estado de PostgreSQL, Redis, Firebase y OpenAI |
| POST | `/api/auth/session` | token válido | Verifica el token, vincula el UID con su perfil y audita el acceso |
| GET | `/api/profile` | token válido | Perfil, roles y permisos del usuario autenticado |
| POST | `/api/chat` | `chat.usar` | Consulta jurídica con RAG, citas verificables e historial |
| GET | `/api/consultas` | token válido | Historial propio de consultas |
| GET | `/api/documentos` | `documentos.leer` | Lista y busca documentos (`tipo`, `numero`, `anio`, `q`) |
| GET | `/api/documentos/{id}` | `documentos.leer` | Documento con sus artículos |
| GET | `/api/leyes` | `documentos.leer` | Leyes por número, año o texto |
| GET | `/api/articulos` | `documentos.leer` | Búsqueda de artículos |
| GET | `/api/jurisprudencia` | `documentos.leer` | Búsqueda híbrida de sentencias |
| GET | `/api/jurisprudencia/{id}` | `documentos.leer` | Sentencia con sus artículos |
| GET | `/api/admin/users` | `admin.usuarios` | Listado de usuarios con roles |
| PATCH | `/api/admin/users/{id}` | `admin.usuarios` | Activa/desactiva y asigna roles |
| GET | `/api/admin/auditoria` | `admin.auditoria` | Últimos eventos auditados |

## Códigos de error

| Código | Significado |
|---|---|
| 401 | Falta el encabezado Bearer o el ID token no es válido/expiró |
| 403 | El usuario no tiene el permiso exigido |
| 404 | El documento o usuario no existe |
| 503 | Firebase sin configurar, o modelo de chat/embeddings no disponible |

## Ejemplo

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pregunta":"¿Cómo se regulan los honorarios judiciales?","canal":"web"}'
```

Respuesta (resumida):

```json
{
  "consulta_id": "…",
  "respuesta": "… [[f:8f14e45f-…]]",
  "fuentes": [{"titulo": "Ley 1376/88", "articulo": "32", "url": "https://www.bacn.gov.py/…"}],
  "fundamento_suficiente": true,
  "modelo": "gpt-5",
  "desde_cache": false,
  "latencia_ms": 1830
}
```

Sin fundamento documental la respuesta es exactamente:

> No se encontró fundamento jurídico suficiente en las fuentes indexadas para responder esta consulta.

## Pendiente

Las pantallas web actuales siguen usando sus servicios actuales. Conectar `LexiaChat`,
`/jurisprudencia`, `/documentos` y `/admin` a estos endpoints (enviando el ID token de
Firebase) es el siguiente paso del Plan Maestro §15 y §16.
