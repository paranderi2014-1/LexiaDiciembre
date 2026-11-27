/**
 * Catálogo legal paraguayo — adaptado de ParaguayLegalCatalog.kt.
 *
 * Fueros, estados de vigencia, categorías de fuente, portales oficiales,
 * plantillas de escritos judiciales y reglas de plazos procesales.
 * Datos estáticos verificables; sin corpus de demostración como legislación real.
 */

export const FUEROS = [
  "Todos",
  "Constitucional",
  "Civil y Comercial",
  "Penal",
  "Laboral",
  "Niñez y Adolescencia",
  "Administrativo",
] as const;

export const VIGENCIA_OPTIONS = [
  "Todas",
  "VIGENTE",
  "MODIFICADA",
  "REGLAMENTADA",
  "DEROGADA",
  "REQUIERE_VERIFICACION",
] as const;

export const SOURCE_CATEGORIES = [
  "Todas",
  "BACN",
  "CSJ",
  "Poder Judicial",
  "Propios",
] as const;

export const OFFICIAL_DOMAINS = [
  "bacn.gov.py",
  "pj.gov.py",
  "csj.gov.py",
  "apps.csj.gov.py",
] as const;

export interface OfficialPortal {
  id: string;
  title: string;
  institution: string;
  category: string;
  url: string;
  description: string;
}

export const OFFICIAL_PORTALS: OfficialPortal[] = [
  {
    id: "bacn",
    title: "BACN — Leyes Paraguayas",
    institution: "Biblioteca y Archivo del Congreso Nacional",
    category: "Legislación",
    url: "https://www.bacn.gov.py/leyes-paraguayas",
    description:
      "Repositorio oficial de leyes vigentes, Constitución Nacional y códigos de la República del Paraguay.",
  },
  {
    id: "pj_home",
    title: "Portal del Poder Judicial",
    institution: "Poder Judicial del Paraguay",
    category: "Institucional",
    url: "https://www.pj.gov.py/",
    description:
      "Portal central de noticias judiciales, circunscripciones, acordadas y servicios al ciudadano.",
  },
  {
    id: "csj_portal",
    title: "CSJ — Portal Ciudadano y Profesional",
    institution: "Corte Suprema de Justicia",
    category: "Gestión",
    url: "https://www.csj.gov.py/portal",
    description:
      "Acceso unificado a trámites en línea, consultas de causas y sistemas de la Corte Suprema.",
  },
  {
    id: "csj_gestion",
    title: "CSJ — Gestión Jurisdiccional",
    institution: "Corte Suprema de Justicia",
    category: "Gestión",
    url: "https://www.csj.gov.py/gestion/",
    description:
      "Herramientas de seguimiento de expedientes, estadísticas y gestión administrativa judicial.",
  },
  {
    id: "csj_jurisprudencia",
    title: "CSJ — Jurisprudencia",
    institution: "Corte Suprema de Justicia",
    category: "Jurisprudencia",
    url: "https://www.csj.gov.py/jurisprudencia/",
    description:
      "Buscador oficial de Acuerdos y Sentencias de las Salas Constitucional, Civil y Penal.",
  },
  {
    id: "csj_legislacion",
    title: "CSJ — Legislación y Acordadas",
    institution: "Corte Suprema de Justicia",
    category: "Legislación",
    url: "https://www.csj.gov.py/legislacion/",
    description:
      "Digesto normativo de acordadas reglamentarias, resoluciones y legislación compilada por la CSJ.",
  },
  {
    id: "csj_login",
    title: "Expediente Judicial Electrónico",
    institution: "Aplicaciones CSJ",
    category: "Trámites",
    url: "https://apps.csj.gov.py/login",
    description:
      "Acceso autenticado para abogados y auxiliares de justicia al sistema de trámites electrónicos.",
  },
  {
    id: "csj_ingresos",
    title: "Ingresos Judiciales CSJ",
    institution: "Aplicaciones CSJ",
    category: "Trámites",
    url: "https://apps.csj.gov.py/ingresos-judiciales",
    description:
      "Liquidación y pago de tasas judiciales, antecedentes y aranceles del Poder Judicial.",
  },
];

export type DeadlineDayType = "HABILES" | "CORRIDOS";

export interface DeadlineRuleSpec {
  key: string;
  title: string;
  fuero: string;
  codeRef: string;
  days: number;
  dayType: DeadlineDayType;
  notes: string;
}

export const DEADLINE_RULES: DeadlineRuleSpec[] = [
  {
    key: "contestacion_demanda_cpc",
    title: "Contestación de Demanda Ordinaria",
    fuero: "Civil y Comercial",
    codeRef: "Art. 235 CPC (Ley N° 1337/88)",
    days: 18,
    dayType: "HABILES",
    notes: "Plazo para contestar demanda ordinaria bajo el CPC.",
  },
  {
    key: "reposicion_cpc",
    title: "Recurso de Reposición",
    fuero: "Civil y Comercial",
    codeRef: "Arts. 390–394 CPC (Ley N° 1337/88)",
    days: 3,
    dayType: "HABILES",
    notes: "Interposición contra providencias o autos interlocutorios.",
  },
  {
    key: "apelacion_cpc",
    title: "Recurso de Apelación",
    fuero: "Civil y Comercial",
    codeRef: "Arts. 395, 396 CPC (Ley N° 1337/88)",
    days: 5,
    dayType: "HABILES",
    notes: "Plazo para fundar apelación ante el Tribunal de Apelaciones.",
  },
  {
    key: "contestacion_cpt",
    title: "Contestación en Juicio Laboral",
    fuero: "Laboral",
    codeRef: "Art. 30 CPT (Ley N° 213/93)",
    days: 6,
    dayType: "HABILES",
    notes: "Plazo para contestar demanda en el Código del Trabajo.",
  },
  {
    key: "apelacion_cpt",
    title: "Apelación en Juicio Laboral",
    fuero: "Laboral",
    codeRef: "Art. 124 CPT (Ley N° 213/93)",
    days: 3,
    dayType: "HABILES",
    notes: "Plazo para apelar sentencia definitiva en el fuero laboral.",
  },
  {
    key: "querella_cpp",
    title: "Presentación de Querella",
    fuero: "Penal",
    codeRef: "Art. 284 CPP (Ley N° 1286/98)",
    days: 60,
    dayType: "CORRIDOS",
    notes: "Plazo de prescripción para acciones penales dependientes (verificar caso por caso).",
  },
  {
    key: "casacion_csj",
    title: "Interposición de Casación",
    fuero: "Civil y Comercial",
    codeRef: "Acordada CSJ N° 198 (Reglamento de Casación)",
    days: 5,
    dayType: "HABILES",
    notes: "Plazo para interponer recurso de casación ante la CSJ.",
  },
  {
    key: "incidente_cpc",
    title: "Contestación de Incidente",
    fuero: "Civil y Comercial",
    codeRef: "Art. 245 CPC (Ley N° 1337/88)",
    days: 5,
    dayType: "HABILES",
    notes: "Plazo para contestar un incidente planteado en el proceso civil.",
  },
];

export interface LegalTemplateSpec {
  key: string;
  title: string;
  fuero: string;
  category: string;
  summary: string;
  requiredFactsHint: string;
  normativeRefs: string;
  skeleton: string;
}

export const LEGAL_TEMPLATES: LegalTemplateSpec[] = [
  {
    key: "demanda_civil",
    title: "Demanda Civil Ordinaria / Ejecutiva",
    fuero: "Civil y Comercial",
    category: "Escritos Judiciales",
    summary: "Escrito inicial conforme al Art. 215 del Código Procesal Civil del Paraguay.",
    requiredFactsHint:
      "Actor, demandado, domicilio real y procesal, objeto/monto, hechos cronológicos, pruebas documentales y petitorio.",
    normativeRefs: "Arts. 215, 219 CPC (Ley N° 1337/88); Código Civil (Ley N° 1183/85).",
    skeleton:
      "OBJETO: PROMOVER DEMANDA ORDINARIA DE [OBJETO].\n\nSEÑOR JUEZ DE PRIMERA INSTANCIA EN LO CIVIL Y COMERCIAL:\n\n[NOMBRE DEL PROFESIONAL], abogado de la matrícula N° [...], en representación de [CLIENTE]...\n\nI. OBJETO\nII. HECHOS\nIII. DERECHO (Arts. 215 CPC y concordantes)\nIV. PRUEBAS\nV. PETITORIO",
  },
  {
    key: "contestacion_demanda",
    title: "Contestación de Demanda y Excepciones",
    fuero: "Civil y Comercial",
    category: "Escritos Judiciales",
    summary:
      "Replica hechos, opone defensas y acompaña instrumental dentro del plazo de 18 días (Art. 235 CPC).",
    requiredFactsHint:
      "Carátula, juzgado, fecha de notificación, negativa categórica de hechos, excepciones, versión de hechos y pruebas.",
    normativeRefs: "Arts. 222, 224, 235 CPC (Ley N° 1337/88).",
    skeleton:
      "OBJETO: CONTESTAR DEMANDA Y OPONER DEFENSAS.\n\nSEÑOR JUEZ:\n\nI. PERSONERÍA Y DOMICILIO\nII. NEGATIVA GENERAL Y ESPECÍFICA\nIII. RELATO DEFENSIVO DE LOS HECHOS\nIV. DERECHO Y JURISPRUDENCIA CSJ\nV. OFRECIMIENTO DE PRUEBAS\nVI. PETITORIO",
  },
  {
    key: "recurso_reposicion",
    title: "Recurso de Reposición (con Apelación en Subsidio)",
    fuero: "Civil y Comercial",
    category: "Recursos",
    summary:
      "Impugna providencia o auto interlocutorio que causa gravamen dentro de 3 días (Arts. 390–394 CPC).",
    requiredFactsHint:
      "Resolución impugnada, fecha de notificación, agravio concreto y solución jurídica pretendida.",
    normativeRefs: "Arts. 390, 391, 392, 394 CPC (Ley N° 1337/88).",
    skeleton:
      "OBJETO: INTERPONER RECURSO DE REPOSICIÓN Y APELACIÓN EN SUBSIDIO.\n\nSEÑOR JUEZ:\n\nI. TEMPORANEIDAD\nII. RESOLUCIÓN IMPUGNADA\nIII. FUNDAMENTACIÓN DEL AGRAVIO\nIV. PETITORIO",
  },
  {
    key: "recurso_apelacion",
    title: "Recurso de Apelación y Expresión de Agravios",
    fuero: "Civil y Comercial",
    category: "Recursos",
    summary:
      "Fundamentación ante Tribunal de Apelaciones señalando errores in judicando o in procedendo.",
    requiredFactsHint:
      "Sentencia Definitiva o A.I. apelado, puntos agraviantes, prueba mal valorada y norma infringida.",
    normativeRefs: "Arts. 395, 396, 419, 420 CPC (Ley N° 1337/88).",
    skeleton:
      "OBJETO: EXPRESAR AGRAVIOS.\n\nEXCMA. CÁMARA DE APELACIONES:\n\nI. SÍNTESIS DE LA RESOLUCIÓN RECURRIDA\nII. PRIMER AGRAVIO\nIII. SEGUNDO AGRAVIO\nIV. PETITORIO (Revocatoria / Nulidad)",
  },
  {
    key: "demanda_laboral",
    title: "Demanda Laboral",
    fuero: "Laboral",
    category: "Escritos Judiciales",
    summary: "Demanda conforme al procedimiento del Código del Trabajo (Ley 213/93).",
    requiredFactsHint:
      "Trabajador, empleador, relación laboral, remuneración, hechos del despido, pretensión y pruebas.",
    normativeRefs: "Arts. 26, 30, 31 CPT (Ley N° 213/93); Código Civil (Ley N° 1183/85).",
    skeleton:
      "OBJETO: PROMOVER DEMANDA LABORAL.\n\nSEÑOR JUEZ DE PRIMERA INSTANCIA DEL TRABAJO:\n\nI. OBJETO Y PERSONERÍA\nII. HECHOS\nIII. DERECHO (Arts. 26, 30 CPT)\nIV. PRUEBAS\nV. PETITORIO",
  },
  {
    key: "casacion_csj",
    title: "Recurso de Casación",
    fuero: "Civil y Comercial",
    category: "Recursos",
    summary:
      "Interposición de casación ante la Corte Suprema de Justicia por infracción a normas procesales o sustantivas.",
    requiredFactsHint:
      "Sentencia recurrida, norma infringida, doctrina aplicable y petitorio de casación.",
    normativeRefs: "Acordada CSJ N° 198; CPC (Ley N° 1337/88).",
    skeleton:
      "OBJETO: INTERPONER RECURSO DE CASACIÓN.\n\nEXCMA. CORTE SUPREMA DE JUSTICIA:\n\nI. TEMPORANEIDAD Y PROCEDENCIA\nII. INFRACCIÓN DENUNCIADA\nIII. DOCTRINA Y JURISPRUDENCIA\nIV. PETITORIO",
  },
];
