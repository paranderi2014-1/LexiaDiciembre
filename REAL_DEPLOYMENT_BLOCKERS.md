# Puesta en marcha real — bloqueos que requieren acceso del propietario

No se deben inventar ni reutilizar secretos. Para continuar se necesitan accesos controlados del propietario:

- Proyecto Supabase de destino (URL, publishable key y acceso de administrador al panel/CLI). La service-role key solo debe configurarse directamente en el gestor de secretos del despliegue; no enviarla por chat.
- Clave OpenAI API y confirmación del modelo habilitado en esa cuenta. Configurarla solo como secreto de servidor.
- Clave Firecrawl API, también como secreto de servidor.
- Hosting/runtime de destino que soporte el WebSocket/upgrade requerido por la voz actual, o decisión de migrar a un proveedor Realtime con endpoint compatible.
- Cliente MCP que se usará para la prueba y un token MCP nuevo generado por el propietario. No reutilizar tokens publicados en mensajes.
- Repositorio GitHub destino (`owner/repo`) y rama autorizada para entregar cambios; todavía no hay un repositorio identificado ni permiso para escribir en uno.

## Estado comprobado en esta sesión

- Se inspeccionó el ZIP fuente y las 12 rutas de módulos.
- Se comprobó que el relay de voz todavía importa `@lovable.dev/ai-gateway`; por tanto, la independencia de Lovable no está completa.
- Se comprobó que las migraciones SQL están en `drizzle/migrations`, pero la exportación no incluía el bucket privado creado; se añadió una migración Supabase explícita para `lexia-case-files` y políticas de carpeta por usuario.
- Se añadieron copias de las migraciones de aplicación en `supabase/migrations` para despliegue con Supabase CLI.
- Se añadió una matriz de aceptación para los 12 módulos, separando demos de integraciones que requieren pruebas reales.
- `npm install --ignore-scripts --no-audit --no-fund` agotó el tiempo disponible. No se afirma que build, lint o tests pasen.

## Secuencia segura

1. Hacer backup de base de datos y Storage del proyecto original.
2. Aplicar las migraciones en un proyecto Supabase de staging, nunca primero en producción.
3. Ejecutar pruebas negativas A/B de aislamiento antes de cargar datos reales.
4. Configurar claves en secrets del hosting y probar OpenAI/Firecrawl/MCP con tokens temporales.
5. Migrar y probar voz en el runtime elegido.
6. Completar los 12 módulos según `MODULE_ACCEPTANCE_MATRIX.md`.
7. Solo después preparar migración de datos y despliegue productivo.
