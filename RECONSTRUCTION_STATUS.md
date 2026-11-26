# LexIAParaguay — informe de reconstrucción

## Fuente

Exportación de Lovable `p-gina-web-creativa-main.zip` recibida en esta conversación. Se conservó el proyecto React 19 + TypeScript + TanStack Start y sus rutas/componentes, migraciones y material visual de referencia.

## Conservado del código original

- Rutas de plataforma: inicio, asistente, autenticación, documentos, jurisprudencia, calculadoras, módulos, contratos, expedientes, gestión, vigilancia, academia, marketplace, precios, fuentes, contacto, reset de contraseña y administración.
- Componentes de chat, historial de conversaciones, espacio de trabajo de expedientes, biblioteca jurídica, demos de módulos y calculadoras.
- Esquemas y migraciones SQL para conversaciones, biblioteca jurídica, roles, expedientes, actuaciones y políticas de acceso a archivos.
- Búsqueda de jurisprudencia CSJ implementada en el código fuente.
- Material de referencia HTML y `grok-workspace.zip`, preservado en `reference-materials/`.

## Cambios realizados en esta reconstrucción

1. Refinamiento visual premium: paleta azul marino/dorado, superficies limpias, navegación lateral fija, tarjetas con jerarquía visual y adaptación móvil.
2. Selector de tema claro/oscuro con persistencia en `localStorage` y respeto inicial de la preferencia del sistema.
3. Inicio con encabezado de plataforma y contexto profesional, manteniendo el chat y las secciones existentes.
4. Autenticación social migrada desde el wrapper OAuth de Lovable a OAuth estándar de Google en Supabase. Requiere configurar Google en Supabase Auth y las URLs de redirección.
5. Chat principal migrado del AI Gateway de Lovable a OpenAI Responses API, con `web_search` restringido a dominios jurídicos oficiales. Requiere `OPENAI_API_KEY` y un modelo disponible en la cuenta.
6. Adaptador Firecrawl de búsqueda y extracción, limitado a HTTPS y dominios BACN/PJ/CSJ; el chat lo consulta primero cuando la clave está configurada.
7. Endpoint MCP Streamable HTTP stateless (versión 2026-07-28 y compatibilidad anterior), JSON-RPC protegido por `MCP_ACCESS_TOKEN`, con herramientas `paraguay_legal_search` y `paraguay_legal_scrape`.
8. Variables de entorno documentadas en `.env.example`; se excluye el `.env` original para no distribuir credenciales.
9. Eliminado el broker de sesión específico de la vista previa de Lovable y eliminadas dependencias OAuth/configuración de editor de Lovable que ya no usa el flujo principal.

## No afirmar como verificado todavía

- No se pudo instalar dependencias en este entorno: `npm install` agotó el tiempo de espera. Por eso no se ejecutaron `npm run build`, `npm test` ni `npm run lint`.
- OpenAI y Firecrawl no se pudieron probar contra servicios reales: requieren claves de la cuenta de despliegue.
- MCP quedó implementado en el código, pero requiere `MCP_ACCESS_TOKEN`, `FIRECRAWL_API_KEY` y una prueba desde un cliente MCP real.
- Los datos alojados en Supabase, usuarios, sesiones, buckets y secretos no forman parte del ZIP. Hay que conectar el proyecto Supabase original o migrar esos datos por separado.
- El relay de voz continúa usando `@lovable.dev/ai-gateway`; no se considera independiente de Lovable. Su ejecución también depende del runtime WebSocket compatible. Debe migrarse y probarse por separado antes de declarar voz lista para producción.
- La vigilancia automática de expedientes CSJ, credenciales de acceso privado, firma, Marketplace y otras funciones señaladas como demostrativas en la interfaz original no se convierten en servicios reales por esta reconstrucción. No se simularán accesos ni se almacenarán credenciales judiciales sin un mecanismo oficial y autorizado.
- Los módulos de demostración conservan su comportamiento original; deben someterse a una revisión funcional individual para separar operaciones reales de ejemplos.

## Próxima verificación necesaria

1. Completar `.env` a partir de credenciales nuevas/confirmadas.
2. Aplicar las migraciones SQL en el proyecto Supabase de destino y verificar RLS/Storage.
3. Ejecutar `npm install`, `npm run lint`, `npm test` y `npm run build`.
4. Probar registro, login, recuperación de contraseña, aislamiento de conversaciones y expedientes por usuario.
5. Probar OpenAI con una consulta jurídica y verificar citas HTTPS de BACN/PJ/CSJ.
6. Probar `initialize`, `tools/list` y ambas herramientas MCP desde un cliente real.
7. Migrar el relay de voz y verificar cada módulo antes del despliegue público.
