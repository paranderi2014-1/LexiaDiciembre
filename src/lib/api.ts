/**
 * Cliente tipado para la API central FastAPI (Plan Maestro §6).
 *
 * Base URL: VITE_API_URL (configurada en el entorno; en el preview apunta al
 * servicio `api` expuesto en su propio host público). El catálogo de leyes y
 * jurisprudencia es de lectura pública; los endpoints de cuenta (chat, consultas,
 * perfil, admin) requieren un ID token de Firebase enviado como Bearer.
 *
 * Las credenciales reales (Firebase, OpenAI, CORS) se insertan en producción
 * desde el panel de secretos; aquí solo se definen los tipos y el transporte.
 */

import { supabase } from "@/integrations/supabase/client";

const API_URL =
  ((import.meta.env.VITE_API_URL as string | undefined) ?? "").replace(/\/$/, "") || "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function apiConfigured(): boolean {
  return Boolean(API_URL);
}

/** Token de autenticación disponible (Firebase ID token cuando la sesión exista). */
async function authToken(): Promise<string | null> {
  try {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  } catch {
    return null;
  }
}

function parseBody(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (!API_URL) throw new ApiError(0, "VITE_API_URL no está configurada.");
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const token = await authToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  const payload = parseBody(await res.text());
  if (!res.ok) {
    const message =
      (payload && typeof payload === "object" && ("detail" in payload || "message" in payload)
        ? String((payload as Record<string, unknown>).detail ?? (payload as Record<string, unknown>).message)
        : res.statusText) || `Error ${res.status}`;
    throw new ApiError(res.status, message);
  }
  return payload as T;
}

// --- Tipos (espejo de backend/app/schemas/api.py) --------------------------
export interface FuenteEstado {
  codigo: string;
  nombre: string;
  url_base: string;
  activo: boolean;
  documentos: number;
}

export interface FuenteRef {
  codigo: string;
  nombre: string;
  url_base: string;
}

export interface DocumentoItem {
  id: string;
  tipo: string;
  numero: string | null;
  titulo: string;
  fecha_publicacion: string | null;
  fecha_vigencia: string | null;
  estado: string;
  url_original: string;
  fuente: FuenteRef | null;
}

export interface DocumentoPagina {
  total: number;
  limite: number;
  desplazamiento: number;
  items: DocumentoItem[];
}

export interface FragmentoItem {
  fragmento_id: string;
  documento_id: string;
  titulo: string;
  tipo: string;
  numero: string | null;
  articulo: string | null;
  fuente: string;
  url: string;
  score: number;
  texto: string;
}

export interface BusquedaResultado {
  termino: string;
  total: number;
  modo_vectorial: boolean;
  items: FragmentoItem[];
}

export interface Perfil {
  id: string;
  email: string | null;
  nombre: string | null;
  activo: boolean;
  roles: string[];
  permisos: string[];
}

// --- Llamadas (catálogo público + cuenta) ----------------------------------
export const api = {
  health: () => request<Record<string, unknown>>("/api/health"),
  fuentes: () => request<FuenteEstado[]>("/api/fuentes"),

  documentos: (params: { tipo?: string; q?: string; anio?: number; limit?: number; offset?: number } = {}) =>
    request<DocumentoPagina>(`/api/documentos${toQuery(params)}`),
  leyes: (params: { q?: string; anio?: number; limit?: number; offset?: number } = {}) =>
    request<DocumentoPagina>(`/api/leyes${toQuery(params)}`),

  buscarJurisprudencia: (q: string, anio?: number, limit = 10) =>
    request<BusquedaResultado>(`/api/jurisprudencia${toQuery({ q, anio, limit })}`),

  documento: (id: string) => request<DocumentoItem & { texto: string; articulos: unknown[] }>(`/api/documentos/${id}`),

  // Cuenta (requieren Firebase ID token):
  crearSesion: () => request<{ perfil: Perfil }>("/api/auth/session", { method: "POST" }),
  perfil: () => request<Perfil>("/api/profile"),
  chat: (pregunta: string, canal: "web" | "android" | "api" = "web") =>
    request<{
      consulta_id: string;
      respuesta: string;
      fuentes: unknown[];
      fundamento_suficiente: boolean;
      modelo: string;
      desde_cache: boolean;
      latencia_ms: number;
    }>("/api/chat", { method: "POST", body: JSON.stringify({ pregunta, canal }) }),
  consultas: (limit = 20) => request<unknown[]>(`/api/consultas?limit=${limit}`),

  // --- Análisis jurídico (§12.2) -----------------------------------------
  contractReview: (contractText: string, fuero: string) =>
    request<unknown>("/api/analysis/contract-review", {
      method: "POST",
      body: JSON.stringify({ contractText, fuero }),
    }),
  documentComparison: (versionATitle: string, versionAText: string, versionBTitle: string, versionBText: string, fuero: string) =>
    request<unknown>("/api/analysis/document-comparison", {
      method: "POST",
      body: JSON.stringify({ versionATitle, versionAText, versionBTitle, versionBText, fuero }),
    }),
  generateDraft: (templateKey: string, factsAndInstructions: string, fuero: string) =>
    request<unknown>("/api/analysis/generate-draft", {
      method: "POST",
      body: JSON.stringify({ templateKey, factsAndInstructions, fuero }),
    }),
  hearingPrep: (hearingTopic: string, fuero: string) =>
    request<unknown>("/api/analysis/hearing-prep", {
      method: "POST",
      body: JSON.stringify({ hearingTopic, fuero }),
    }),
  caseExtraction: (documentTitle: string, rawText: string, fuero: string) =>
    request<unknown>("/api/analysis/case-extraction", {
      method: "POST",
      body: JSON.stringify({ documentTitle, rawText, fuero }),
    }),
  analogousCases: (caseSummary: string, fuero: string) =>
    request<unknown>("/api/analysis/analogous-cases", {
      method: "POST",
      body: JSON.stringify({ caseSummary, fuero }),
    }),
  clientLeadTriage: (clientName: string, legalArea: string, description: string) =>
    request<unknown>("/api/analysis/client-lead-triage", {
      method: "POST",
      body: JSON.stringify({ clientName, legalArea, description }),
    }),
};

function toQuery(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    sp.set(key, String(value));
  }
  const qs = sp.toString();
  return qs ? `?${qs}` : "";
}
