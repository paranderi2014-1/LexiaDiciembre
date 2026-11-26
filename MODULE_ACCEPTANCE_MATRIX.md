# LexIAParaguay — matriz de aceptación de 12 módulos

Estado inicial basado en lectura estática del ZIP Lovable. **No equivale a prueba funcional**: para marcar un módulo como aprobado se necesita ejecutar el entorno con servicios y credenciales de prueba.

| # | Módulo | Evidencia en el código exportado | Estado para producción | Prueba que falta |
|---|---|---|---|---|
| 1 | Honorarios | Componente de demo y calculadoras locales | Parcial / no certificado | Contrastar fórmulas, jornales y tasas con norma vigente; casos de prueba y PDF real |
| 2 | Jurisprudencia | Funciones CSJ y pantalla de búsqueda | Integración externa no certificada | Consultas reales, paginación, ficha y PDF; registrar fuente y fecha |
| 3 | Vigilancia | Pantalla demo; no se acreditó API CSJ autorizada | Demostrativo | Integración autorizada, límites, alertas, auditoría y protección de credenciales |
| 4 | Contratos | Wizard y demo de cláusulas | Parcial / no certificado | Persistencia, generación DOCX/PDF, validación legal y pruebas por tipo de contrato |
| 5 | Ejecutivos | Pantalla demo / reglas locales | Parcial / no certificado | Títulos, excepciones, plazos, liquidación e intereses con escenarios revisados |
| 6 | Compliance | Checklist demo | Demostrativo | Reglas MTESS actualizadas, evidencias, responsables, exportación y trazabilidad |
| 7 | Litigios Laborales | Pantalla demo de gestión | Demostrativo | CRUD persistente, etapas, plazos, responsables y conexión con cálculos laborales |
| 8 | Predicción | Simulador UI | Demostrativo | Dataset judicial verificable, metodología, calibración y advertencia de incertidumbre |
| 9 | Gestión | Demo CRM local | Demostrativo | CRUD real multiusuario, RLS, agenda, facturación y exportación |
| 10 | Escritos | Generador UI | Parcial / no certificado | Plantillas paraguayas verificadas, generación DOCX/PDF, guardado y revisión de citas |
| 11 | Revisión | Demo de revisión documental | Demostrativo | Subida segura, extracción real, análisis, límites de archivo y eliminación |
| 12 | Privacidad | Demo de anonimización en sesión | Demostrativo | Pruebas de reidentificación, procesamiento seguro, retención y borrado verificable |

## Regla de aceptación

Cada módulo debe tener: (a) prueba unitaria de reglas; (b) prueba de integración con el backend; (c) prueba de autorización con dos usuarios; (d) prueba de error/timeout; (e) evidencia de fuente y fecha cuando dé información jurídica; y (f) revisión manual del resultado. No mostrar una función como "operativa" si solo modifica estado local o usa datos de ejemplo.
