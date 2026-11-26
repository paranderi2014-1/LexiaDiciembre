import { z } from "zod";

export const LEGAL_ALLOWED_HOSTS = ["bacn.gov.py", "pj.gov.py", "csj.gov.py", "apps.csj.gov.py"] as const;

export function isAllowedLegalUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && LEGAL_ALLOWED_HOSTS.some((host) => url.hostname === host || url.hostname.endsWith(`.${host}`));
  } catch {
    return false;
  }
}

function apiKey() {
  const key = process.env["FIRECRAWL_API_KEY"];
  if (!key) throw new Error("FIRECRAWL_API_KEY no está configurada en el servidor.");
  return key;
}

const searchSchema = z.object({
  query: z.string().trim().min(3).max(500),
  limit: z.number().int().min(1).max(10).optional().default(5),
});

export async function searchParaguayLegal(input: unknown) {
  const args = searchSchema.parse(input);
  const response = await fetch("https://api.firecrawl.dev/v2/search", {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey()}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      query: args.query,
      limit: args.limit,
      sources: [{ type: "web" }],
      includeDomains: [...LEGAL_ALLOWED_HOSTS],
      scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
    }),
    signal: AbortSignal.timeout(45000),
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(`Firecrawl search rechazó la solicitud (${response.status}).`);
  const parsed = z.object({ success: z.boolean().optional(), data: z.object({ web: z.array(z.record(z.string(), z.unknown())).optional() }).passthrough().optional() }).passthrough().parse(payload);
  if (parsed.success === false) throw new Error("Firecrawl no pudo completar la búsqueda.");
  const results = (parsed.data?.web ?? []).flatMap((item) => {
    const url = typeof item.url === "string" ? item.url : "";
    if (!isAllowedLegalUrl(url)) return [];
    return [{ title: String(item.title ?? "Fuente oficial"), url, description: String(item.description ?? item.markdown ?? "").slice(0, 5000) }];
  });
  return { results, count: results.length, provider: "Firecrawl", checkedAt: new Date().toISOString() };
}

const scrapeSchema = z.object({ url: z.string().url() });
export async function scrapeParaguayLegal(input: unknown) {
  const args = scrapeSchema.parse(input);
  if (!isAllowedLegalUrl(args.url)) throw new Error("Solo se permite consultar fuentes oficiales BACN, Poder Judicial y CSJ.");
  const response = await fetch("https://api.firecrawl.dev/v2/scrape", {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey()}`, "Content-Type": "application/json" },
    body: JSON.stringify({ url: args.url, formats: ["markdown"], onlyMainContent: true }),
    signal: AbortSignal.timeout(45000),
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(`Firecrawl scrape rechazó la solicitud (${response.status}).`);
  const parsed = z.object({ success: z.boolean().optional(), data: z.object({ markdown: z.string().optional(), metadata: z.record(z.string(), z.unknown()).optional() }).passthrough().optional() }).passthrough().parse(payload);
  if (parsed.success === false) throw new Error("Firecrawl no pudo extraer el contenido de la fuente.");
  return { url: args.url, markdown: parsed.data?.markdown ?? "", metadata: parsed.data?.metadata ?? {}, provider: "Firecrawl", checkedAt: new Date().toISOString() };
}
