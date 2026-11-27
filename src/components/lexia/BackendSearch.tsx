import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink, Gavel, Landmark, Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, apiConfigured, type FragmentoItem, type FuenteEstado } from "@/lib/api";

/**
 * Búsqueda en vivo sobre el corpus ingestado por el backend FastAPI + pgvector.
 * Se conecta a /api/fuentes, /api/jurisprudencia y /api/leyes del servicio central.
 */
export function BackendSearch() {
  const [tipo, setTipo] = useState<"jurisprudencia" | "ley">("jurisprudencia");
  const [q, setQ] = useState("");
  const [busqueda, setBusqueda] = useState("");

  const fuentes = useQuery({
    queryKey: ["api-fuentes"],
    queryFn: api.fuentes,
    staleTime: 60_000,
  });

  const resultados = useQuery<FragmentoItem[]>({
    queryKey: ["api-search", tipo, busqueda],
    queryFn: async () => {
      if (!busqueda.trim()) return [];
      if (tipo === "jurisprudencia") {
        const r = await api.buscarJurisprudencia(busqueda);
        return r.items;
      }
      const r = await api.leyes({ q: busqueda, limit: 12 });
      return r.items.map((d) => ({
        fragmento_id: d.id,
        documento_id: d.id,
        titulo: d.titulo,
        tipo: d.tipo,
        numero: d.numero,
        articulo: null,
        fuente: d.fuente?.nombre ?? "—",
        url: d.url_original,
        score: 0,
        texto: "",
      }));
    },
    enabled: busqueda.trim().length > 0,
  });

  if (!apiConfigured()) {
    return (
      <div className="card mt-6 p-4 text-sm text-muted-foreground">
        VITE_API_URL no está configurada. La búsqueda en vivo del backend se habilita al
        desplegar con el servicio FastAPI.
      </div>
    );
  }

  return (
    <div className="card mt-6 p-4 sm:p-6">
      <h2 className="flex items-center gap-2 text-lg font-bold">
        <Landmark size={20} className="text-gold" />
        Biblioteca ingestada en vivo · FastAPI + pgvector
      </h2>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {fuentes.isLoading ? (
          <p className="small text-muted-foreground">Cargando fuentes…</p>
        ) : fuentes.data?.length ? (
          fuentes.data.map((f) => <FuenteCard key={f.codigo} fuente={f} />)
        ) : (
          <p className="small text-muted-foreground">
            {fuentes.error ? "No se pudo conectar con el backend." : "Sin fuentes indexadas todavía."}
          </p>
        )}
      </div>

      <form
        className="mt-5"
        onSubmit={(e) => {
          e.preventDefault();
          setBusqueda(q.trim());
        }}
      >
        <div className="flex flex-wrap items-end gap-3">
          <label className="field min-w-0 flex-1">
            Buscar
            <input
              aria-label="Buscar en la biblioteca ingestada"
              value={q}
              maxLength={300}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Ej.: honorarios, amparo, prescripción"
            />
          </label>
          <label className="field w-40">
            Tipo
            <select value={tipo} onChange={(e) => setTipo(e.target.value as "jurisprudencia" | "ley")}>
              <option value="jurisprudencia">Jurisprudencia</option>
              <option value="ley">Leyes</option>
            </select>
          </label>
          <Button type="submit" disabled={resultados.isFetching}>
            {resultados.isFetching ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            Buscar
          </Button>
        </div>
      </form>

      {resultados.isError && (
        <p role="alert" className="mt-4 border-l-2 border-destructive pl-3 text-sm text-destructive">
          No se pudo consultar el backend: {(resultados.error as Error).message}
        </p>
      )}

      {busqueda && !resultados.isFetching && !resultados.isError && (
        <p role="status" className="mt-4 text-xs text-muted-foreground">
          {resultados.data?.length ?? 0} resultado(s) del corpus ingestado ·{" "}
          {tipo === "jurisprudencia" ? "búsqueda híbrida BM25 + vectorial" : "listado de leyes"}
        </p>
      )}

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {resultados.data?.map((f) => (
          <article key={f.fragmento_id} className="min-w-0 rounded-md border bg-card p-4">
            <p className="text-xs font-bold uppercase text-kicker">
              {f.fuente} · {f.tipo}
              {f.numero ? ` · ${f.numero}` : ""}
              {f.articulo ? ` · art. ${f.articulo}` : ""}
            </p>
            <h3 className="mt-2 break-words text-sm font-bold leading-relaxed">{f.titulo}</h3>
            {f.texto && <p className="mt-2 line-clamp-4 text-xs leading-relaxed text-muted-foreground">{f.texto}</p>}
            <a
              className="mt-3 flex items-center gap-1 text-xs font-bold text-link underline"
              href={f.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Ver en fuente oficial <ExternalLink size={12} />
            </a>
          </article>
        ))}
      </div>

      {busqueda && !resultados.data?.length && !resultados.isFetching && !resultados.isError && (
        <p className="mt-5 text-sm text-muted-foreground">
          Sin coincidencias. Probá otro término o ejecutá una nueva ingesta desde el backend.
        </p>
      )}
    </div>
  );
}

function FuenteCard({ fuente }: { fuente: FuenteEstado }) {
  return (
    <a
      href={fuente.url_base}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-md border bg-card p-3 transition-shadow hover:shadow-lg"
    >
      <span className="flex items-center gap-1 text-xs font-bold uppercase text-kicker">
        <Gavel size={12} /> {fuente.codigo}
        <span
          className={`ml-auto rounded px-1.5 py-0.5 text-[10px] ${fuente.activo ? "bg-success/15 text-success" : "bg-muted text-muted-foreground"}`}
        >
          {fuente.activo ? "activa" : "inactiva"}
        </span>
      </span>
      <h3 className="mt-2 text-sm font-bold leading-tight">{fuente.nombre}</h3>
      <p className="small mt-2 text-muted-foreground">{fuente.documentos} documento(s) indexados</p>
    </a>
  );
}
