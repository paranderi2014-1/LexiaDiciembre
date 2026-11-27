/**
 * Verificación de citas jurídicas — adaptado de CitationVerificationService.kt.
 *
 * Detecta referencias a leyes, artículos y acordadas en el texto de respuestas,
 * las contrasta con fragmentos recuperados y fuentes oficiales, y clasifica
 * el estado de verificación (corpus, web oficial, norma con reforma, requiere verificación).
 * Pure function; sin dependencias externas.
 */

export type CitationVerificationStatus =
  | "VERIFICADA_CORPUS"
  | "RESPALDO_WEB_OFICIAL"
  | "NORMA_CON_REFORMA"
  | "REQUIERE_VERIFICACION";

export interface VerifiedCitationItem {
  detectedReference: string;
  status: CitationVerificationStatus;
  matchedDocumentTitle: string;
  matchedArticle: string;
  vigenciaStatus: string;
  officialUrl: string;
  excerpt: string;
  diagnosticNote: string;
}

export interface CorpusChunk {
  documentTitle: string;
  articleRef: string;
  normNumber: string;
  content: string;
  vigenciaStatus: string;
  sourceName: string;
  sourceUrl: string;
  relatedNorms: string;
}

export interface DiffSegment {
  changeType: "ADDED" | "REMOVED" | "UNCHANGED";
  lineText: string;
}

export interface ConflictCheckResult {
  hasConflict: boolean;
  warnings: string[];
}

const OFFICIAL_DOMAINS = ["bacn.gov.py", "pj.gov.py", "csj.gov.py", "apps.csj.gov.py"];

const ARTICLE_REGEX =
  /Art(?:ículo|\.)?\s*\d+[°º]?(?:\s+(?:de\s+la|del)\s+(?:Constitución|Código\s+(?:Civil|Penal|Procesal\s+Civil|Procesal\s+Penal|del\s+Trabajo|de\s+la\s+Niñez|Electoral|Aduanero)|Ley\s*(?:N[°º]?\s*)?\d{2,5}\/\d{2,4}|CPC|CPP|CPT|CC|CP|CT|CN))?/gi;

const LAW_REGEX = /Ley\s*(?:N[°º]?\s*)?\d{2,5}\/\d{2,4}/gi;
const ACORDADA_REGEX = /Acordada\s*(?:N[°º]?\s*)?\d{2,5}/gi;
const URL_REGEX = /https?:\/\/[^\s)\]>]+/gi;

function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function isOfficialDomain(url: string): boolean {
  return OFFICIAL_DOMAINS.some((d) => url.toLowerCase().includes(d));
}

export function verifyCitations(
  responseText: string,
  groundingSources: string[],
  corpusChunks: CorpusChunk[],
): VerifiedCitationItem[] {
  const candidates = new Set<string>();

  // Reset regex lastIndex
  for (const re of [LAW_REGEX, ARTICLE_REGEX, ACORDADA_REGEX]) re.lastIndex = 0;

  for (const m of responseText.matchAll(LAW_REGEX)) candidates.add(m[0].trim());
  for (const m of responseText.matchAll(ARTICLE_REGEX)) candidates.add(m[0].trim());
  for (const m of responseText.matchAll(ACORDADA_REGEX)) candidates.add(m[0].trim());
  URL_REGEX.lastIndex = 0;
  for (const m of responseText.matchAll(URL_REGEX)) {
    if (isOfficialDomain(m[0])) candidates.add(m[0].trim());
  }
  for (const src of groundingSources) if (src.trim()) candidates.add(src.trim());

  if (candidates.size === 0) {
    return [
      {
        detectedReference: "Texto sin cita normativa explícita",
        status: "REQUIERE_VERIFICACION",
        matchedDocumentTitle: "Sin coincidencia directa",
        matchedArticle: "-",
        vigenciaStatus: "REQUIERE_VERIFICACION",
        officialUrl: "https://www.bacn.gov.py/leyes-paraguayas",
        excerpt:
          "No se detectaron artículos ni leyes numeradas en esta respuesta. Contrastá manualmente en BACN o CSJ.",
        diagnosticNote: "Cautela académica: validá norma aplicable antes de usar en escritos.",
      },
    ];
  }

  return Array.from(candidates)
    .slice(0, 12)
    .map((ref) => {
      const normRef = normalize(ref);
      const extractedNum = normRef.match(/\d{1,5}(?:\/\d{2,4})?/)?.[0];

      const bestChunk = corpusChunks
        .map((chunk) => {
          const chunkSearch = normalize(
            `${chunk.documentTitle} ${chunk.articleRef} ${chunk.normNumber} ${chunk.content}`,
          );
          let score = 0;
          if (normRef && chunkSearch.includes(normRef)) score += 10;
          if (extractedNum && chunkSearch.includes(extractedNum)) score += 6;
          const words = normRef.split(" ").filter((w) => w.length >= 4);
          score += words.filter((w) => chunkSearch.includes(w)).length * 2;
          return { chunk, score };
        })
        .sort((a, b) => b.score - a.score)[0];

      const hasValidMatch =
        bestChunk &&
        bestChunk.score > 0 &&
        (() => {
          const cs = normalize(
            `${bestChunk.chunk.documentTitle} ${bestChunk.chunk.articleRef} ${bestChunk.chunk.normNumber}`,
          );
          return (
            (extractedNum && cs.includes(extractedNum)) ||
            (normRef.length >= 6 && cs.includes(normRef))
          );
        })();

      URL_REGEX.lastIndex = 0;
      const detectedUrl = ref.match(URL_REGEX)?.[0];
      const isOfficial =
        (detectedUrl ?? bestChunk?.chunk.sourceUrl ?? "").length > 0 &&
        isOfficialDomain(detectedUrl ?? bestChunk?.chunk.sourceUrl ?? "");

      if (hasValidMatch && bestChunk) {
        const chunk = bestChunk.chunk;
        if (chunk.vigenciaStatus === "MODIFICADA" || chunk.vigenciaStatus === "DEROGADA") {
          return {
            detectedReference: ref,
            status: "NORMA_CON_REFORMA",
            matchedDocumentTitle: chunk.documentTitle,
            matchedArticle: chunk.articleRef,
            vigenciaStatus: chunk.vigenciaStatus,
            officialUrl: chunk.sourceUrl,
            excerpt: chunk.content.slice(0, 320),
            diagnosticNote: `Atención de vigencia (${chunk.vigenciaStatus}): ${
              chunk.relatedNorms || "Revisar reformas en BACN"
            }.`,
          };
        }
        return {
          detectedReference: ref,
          status: "VERIFICADA_CORPUS",
          matchedDocumentTitle: chunk.documentTitle,
          matchedArticle: chunk.articleRef,
          vigenciaStatus: chunk.vigenciaStatus,
          officialUrl: chunk.sourceUrl,
          excerpt: chunk.content.slice(0, 320),
          diagnosticNote: `Coincidencia exacta con fragmento controlado (${chunk.sourceName}).`,
        };
      }

      if (isOfficial && detectedUrl) {
        return {
          detectedReference: ref,
          status: "RESPALDO_WEB_OFICIAL",
          matchedDocumentTitle: ref.split(" — ")[0],
          matchedArticle: "Fuente web oficial paraguaya",
          vigenciaStatus: "VIGENTE",
          officialUrl: detectedUrl,
          excerpt: `Referenciada mediante búsqueda en dominio oficial del Paraguay (${detectedUrl}).`,
          diagnosticNote: "Abrir enlace oficial para confirmar texto literal completo.",
        };
      }

      return {
        detectedReference: ref,
        status: "REQUIERE_VERIFICACION",
        matchedDocumentTitle: "No localizada en índice local",
        matchedArticle: ref,
        vigenciaStatus: "REQUIERE_VERIFICACION",
        officialUrl: "https://www.csj.gov.py/legislacion/",
        excerpt:
          "Esta referencia no coincide literalmente con el corpus local ni con URL oficial adjunta.",
        diagnosticNote:
          "Verificar en BACN o CSJ Legislación antes de presentar ante juzgado.",
      };
    });
}

export function computeTextDiffSummary(versionA: string, versionB: string): DiffSegment[] {
  const linesA = versionA
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 0);
  const linesB = versionB
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 0);
  const setA = new Set(linesA);
  const setB = new Set(linesB);

  const segments: DiffSegment[] = [];

  // Lines in A not in B = removed
  for (const line of linesA) {
    if (!setB.has(line)) segments.push({ changeType: "REMOVED", lineText: line });
  }
  // Lines in B not in A = added
  for (const line of linesB) {
    if (!setA.has(line)) segments.push({ changeType: "ADDED", lineText: line });
  }
  // Lines in both = unchanged
  for (const line of linesA) {
    if (setB.has(line)) segments.push({ changeType: "UNCHANGED", lineText: line });
  }

  return segments;
}

export function checkConflict(
  clientName: string,
  counterparty: string,
  existingCases: Array<{ clientName: string; counterparty: string; id: string }>,
  ignoreCaseId?: string,
): ConflictCheckResult {
  const warnings: string[] = [];
  const name = normalize(clientName);
  const counter = normalize(counterparty);

  for (const c of existingCases) {
    if (ignoreCaseId && c.id === ignoreCaseId) continue;
    const caseClient = normalize(c.clientName);
    const caseCounter = normalize(c.counterparty);
    if (
      (name && caseClient.includes(name)) ||
      (counter && caseCounter.includes(counter)) ||
      (name && caseCounter.includes(name)) ||
      (counter && caseClient.includes(counter))
    ) {
      warnings.push(
        `Posible conflicto de interés con expediente: cliente ${c.clientName} / contraparte ${c.counterparty}`,
      );
    }
  }

  return { hasConflict: warnings.length > 0, warnings };
}
