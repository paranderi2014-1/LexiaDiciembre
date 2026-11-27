/**
 * Modos de análisis del chat jurídico — adaptado de AnalysisOption en LexiaViewModel.kt.
 *
 * Cada modo define una instrucción específica que se envía al modelo de IA,
 * permitiendo que el usuario elija el tipo de análisis sin cambiar de pantalla.
 */

export type QueryMode = "SEARCH_GROUNDING" | "HIGH_THINKING";

export interface AnalysisOption {
  key: string;
  label: string;
  description: string;
  instruction: string;
  queryMode: QueryMode;
}

export const ANALYSIS_OPTIONS: AnalysisOption[] = [
  {
    key: "WEB_SEARCH",
    label: "Búsqueda web",
    description: "Verifica leyes y jurisprudencia en fuentes oficiales CSJ/BACN",
    instruction:
      "Prioriza la verificación con fuentes web oficiales paraguayas (BACN, PJ, CSJ).",
    queryMode: "SEARCH_GROUNDING",
  },
  {
    key: "EXPLAIN",
    label: "Explicar",
    description: "Explica conceptos jurídicos de forma clara, didáctica y con ejemplos",
    instruction:
      "Explica de forma didáctica, clara y paso a paso, con ejemplos prácticos aplicados al derecho paraguayo.",
    queryMode: "SEARCH_GROUNDING",
  },
  {
    key: "DEEP_RESEARCH",
    label: "Investigación profunda",
    description: "Análisis doctrinal y procesal exhaustivo con razonamiento avanzado",
    instruction:
      "Realiza una investigación jurídica profunda, sistemática y exhaustiva con doctrina, artículos concordantes y análisis procesal.",
    queryMode: "HIGH_THINKING",
  },
  {
    key: "CONTRACT_REVIEW",
    label: "Analizar contrato",
    description: "Detecta cláusulas riesgosas, omisiones y riesgos bajo el Código Civil",
    instruction:
      "Analiza cláusula por cláusula señalando riesgos (CRÍTICO/ALTO/MEDIO/BAJO), desequilibrios y mejoras de redacción bajo derecho paraguayo.",
    queryMode: "HIGH_THINKING",
  },
  {
    key: "DRAFT_PREP",
    label: "Estructurar escrito",
    description: "Genera esquema forense con citas y requisitos del CPC/CPT/CPP",
    instruction:
      "Estructura un borrador procesal paraguayo completo con Objeto, Hechos, Derecho, Pruebas y Petitorio, marcando entre corchetes los datos a completar.",
    queryMode: "SEARCH_GROUNDING",
  },
  {
    key: "CASE_SUMMARY",
    label: "Resumir expediente",
    description: "Extrae partes, plazos, pretensiones y riesgos del texto o caso",
    instruction:
      "Resume ejecutivamente hechos, partes, montos, plazos críticos, pretensiones, defensas y riesgos procesales en derecho paraguayo.",
    queryMode: "SEARCH_GROUNDING",
  },
];

export const DEFAULT_ANALYSIS_KEY = "WEB_SEARCH";

export function getAnalysisOption(key: string): AnalysisOption {
  return ANALYSIS_OPTIONS.find((o) => o.key === key) ?? ANALYSIS_OPTIONS[0];
}
