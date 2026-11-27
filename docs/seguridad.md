# Seguridad

## Identidad (Plan Maestro §7)

- **Firebase Authentication** es el único proveedor de identidad. No se emite un JWT
  propio.
- El backend verifica cada ID token con **Firebase Admin SDK** (`verify_id_token`,
  con `check_revoked=True`).
- El UID se toma **del token verificado**, nunca del cuerpo de la petición.
- Sin credenciales de Firebase la API responde **503**; no existe un modo anónimo.
- PostgreSQL guarda perfiles, roles y permisos; nunca contraseñas.
- El perfil se crea o vincula por `firebase_uid` (restricción `UNIQUE`), lo que evita
  duplicados cuando el mismo usuario entra desde web y Android.

## Autorización

- Los permisos se aplican en el backend con `require_permission(...)`; ocultar botones
  no es un control de acceso.
- Permisos iniciales: `chat.usar`, `documentos.leer`, `documentos.escribir`,
  `admin.usuarios`, `admin.fuentes`, `admin.auditoria`.
- Roles: `admin`, `editor`, `usuario`.

## Datos y auditoría

- Cada acceso, consulta, búsqueda y cambio administrativo queda en `auditoria`.
- Las consultas se vinculan al usuario autenticado y su historial se filtra por dueño.
- Las respuestas sólo se cachean cuando tienen fundamento documental y la clave incluye
  la versión del índice, para no servir derecho desactualizado.

## Fuentes

- Sólo se indexan y citan URLs HTTPS de `bacn.gov.py`, `csj.gov.py`,
  `apps.csj.gov.py` y `pj.gov.py`.
- Toda cita que no corresponda a un fragmento recuperado se descarta; si no queda
  ninguna, se responde con el texto de contingencia.

## Secretos

- `FIREBASE_CREDENTIALS`, `OPENAI_API_KEY` y demás claves viven fuera del repositorio,
  en el gestor de secretos del entorno (`/run/base44/app.env` en la vista previa).
- Las credenciales de servicio de Firebase no se distribuyen a Android ni al navegador.

## Alcance no cubierto todavía

- RLS de las tablas Supabase existentes: se mantienen intactas; no fueron modificadas.
- El API central no se expone públicamente sin autenticación: no hay rutas anónimas
  salvo `/api/health`, `/docs` y `/openapi.json`.
- Firma digital, voz y accesos autenticados a sistemas CSJ siguen fuera de alcance.
