import { useEffect, useRef, useState, useCallback } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useQueryClient } from "@tanstack/react-query";
import type { UIMessage, ChatStatus } from "ai";
import {
  ArrowUp,
  Paperclip,
  Mic,
  Square,
  Sparkles,
  MoreHorizontal,
  Menu,
  Plus,
  FileText,
  FolderOpen,
  Search,
  GraduationCap,
  Microscope,
  FileSearch,
  FileSignature,
  ClipboardList,
  Volume2,
  Pause,
  X,
  Copy,
  ShieldCheck,
  Gavel,
} from "lucide-react";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageContent,
  MessageResponse,
  MessageAction,
} from "@/components/ai-elements/message";
import { Shimmer } from "@/components/ai-elements/shimmer";
import { Tool, ToolHeader, ToolContent } from "@/components/ai-elements/tool";
import { Button } from "@/components/ui/button";
import { supabase } from "@/integrations/supabase/client";
import { createThread } from "@/lib/lexia-chat.functions";
import { isOfficialUrl, streamEventSchema } from "@/lib/lexia-chat";
import { SOURCES } from "@/lib/lexia-data";
import { FUEROS } from "@/lib/lexia-catalog";
import { ANALYSIS_OPTIONS, getAnalysisOption } from "@/lib/lexia-analysis";
import { useLexiaAuth } from "./AuthProvider";
import { useVoice } from "@/hooks/useVoice";
import emblem from "@/assets/lexia-emblem.jpg";

// --- Iconos por modo de análisis -----------------------------------------
const ANALYSIS_ICONS: Record<string, typeof Search> = {
  WEB_SEARCH: Search,
  EXPLAIN: GraduationCap,
  DEEP_RESEARCH: Microscope,
  CONTRACT_REVIEW: FileSearch,
  DRAFT_PREP: FileSignature,
  CASE_SUMMARY: ClipboardList,
};

// Modos que van en el botón "Analizar" (los 3 principales)
const PRIMARY_MODES = ["WEB_SEARCH", "EXPLAIN", "DEEP_RESEARCH"];
// Modos avanzados que van en "Más opciones" (...)
const ADVANCED_MODES = ["CONTRACT_REVIEW", "DRAFT_PREP", "CASE_SUMMARY"];

// --- Hook para cerrar menús al tocar fuera --------------------------------
function useClickOutside<T extends HTMLElement>(onClose: () => void) {
  const ref = useRef<T>(null);
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);
  return ref;
}

export function LexiaChat({
  threadId,
  initialMessages = [],
}: {
  threadId?: string;
  initialMessages?: UIMessage[];
}) {
  const [messages, setMessages] = useState<UIMessage[]>(initialMessages);
  const [status, setStatus] = useState<ChatStatus>("ready");
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [fuero, setFuero] = useState<string>(FUEROS[0]);
  const [analysisMode, setAnalysisMode] = useState<string>("WEB_SEARCH");
  const [showAnalyze, setShowAnalyze] = useState(false);
  const [showMore, setShowMore] = useState(false);
  const [showAttach, setShowAttach] = useState(false);
  const [showFuero, setShowFuero] = useState(false);
  const [showVoiceControls, setShowVoiceControls] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, ready } = useLexiaAuth();
  const navigate = useNavigate();
  const create = useServerFn(createThread);
  const queryClient = useQueryClient();
  const textarea = useRef<HTMLTextAreaElement>(null);
  const abort = useRef<AbortController | null>(null);
  const sendRef = useRef<((question: string) => Promise<void>) | null>(null);
  const busy = status === "submitted" || status === "streaming";

  const voice = useVoice();

  // --- Cerrar menús al tocar fuera ---
  const analyzeRef = useClickOutside<HTMLDivElement>(() => setShowAnalyze(false));
  const moreRef = useClickOutside<HTMLDivElement>(() => setShowMore(false));
  const attachRef = useClickOutside<HTMLDivElement>(() => setShowAttach(false));
  const fueroRef = useClickOutside<HTMLDivElement>(() => setShowFuero(false));

  useEffect(() => {
    textarea.current?.focus({ preventScroll: true });
    return () => abort.current?.abort();
  }, []);

  // --- Auto-expandir textarea ---
  const adjustTextarea = useCallback(() => {
    const el = textarea.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, []);

  // --- STT: cuando hay transcript final, ponerlo en el input ---
  useEffect(() => {
    if (voice.transcript) {
      setInput((prev) => (prev ? prev + " " : "") + voice.transcript);
      voice.transcript = ""; // consumir
    }
  }, [voice.transcript]); // eslint-disable-line react-hooks/exhaustive-deps

  // --- TTS: leer la última respuesta del asistente ---
  const speakLast = useCallback(() => {
    const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
    if (!lastAssistant) return;
    const text = lastAssistant.parts
      .filter((p) => p.type === "text")
      .map((p) => (p as { text: string }).text)
      .join("\n");
    if (text) {
      voice.speak(text);
      setShowVoiceControls(true);
    }
  }, [messages, voice]);

  const send = async (question: string) => {
    if (!user || busy || !question.trim()) return;
    setError("");
    if (!threadId) {
      setStatus("submitted");
      try {
        const thread = await create({ data: { title: question.slice(0, 150) } });
        sessionStorage.setItem(`lexia-pending-${thread.id}`, question);
        await queryClient.invalidateQueries({ queryKey: ["lexia-threads"] });
        await navigate({ to: "/asistente/$threadId", params: { threadId: thread.id } });
      } catch {
        setError("No se pudo crear la conversación.");
        setStatus("error");
      }
      return;
    }
    const assistantId = crypto.randomUUID();
    const timestamp = new Date();
    setMessages((old) => [
      ...old,
      { id: crypto.randomUUID(), role: "user", parts: [{ type: "text", text: question }] },
      { id: assistantId, role: "assistant", parts: [] },
    ]);
    setInput("");
    setStatus("submitted");
    textarea.current?.focus();
    if (textarea.current) textarea.current.style.height = "auto";
    const control = new AbortController();
    abort.current = control;
    let text = "";
    const sources = new Map<string, string>();
    let toolState: "input-available" | "output-available" | "output-error" = "input-available";
    const update = () => {
      const toolBase = {
        type: "dynamic-tool" as const,
        toolName: "investigacion-oficial",
        toolCallId: assistantId,
        input: { fuentes: SOURCES.map((s) => s.name) },
      };
      const tool: UIMessage["parts"][number] =
        toolState === "output-available"
          ? { ...toolBase, state: "output-available", output: { fuentes: [...sources.keys()] } }
          : toolState === "output-error"
            ? { ...toolBase, state: "output-error", errorText: "Investigación no completada." }
            : { ...toolBase, state: "input-available" };
      setMessages((old) =>
        old.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                parts: [
                  tool,
                  { type: "text", text },
                  ...[...sources].map(([url, title], i) => ({
                    type: "source-url" as const,
                    sourceId: String(i),
                    url,
                    title,
                  })),
                ],
              }
            : m,
        ),
      );
    };
    try {
      const { data } = await supabase.auth.getSession();
      if (!data.session) throw new Error("Iniciá sesión para continuar.");
      const response = await fetch("/api/lexia", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${data.session.access_token}`,
        },
        body: JSON.stringify({ threadId, question, fuero, analysisMode }),
        signal: control.signal,
      });
      if (!response.ok || !response.body)
        throw new Error("No pude iniciar la investigación. Revisá tu sesión.");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let doneReceived = false;
      while (true) {
        const result = await reader.read();
        if (result.done) break;
        buffer += decoder.decode(result.value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line) continue;
          const event = streamEventSchema.parse(JSON.parse(line));
          if (event.kind === "text") {
            text += event.delta;
            setStatus("streaming");
          }
          if (event.kind === "search") toolState = event.state;
          if (event.kind === "source" && isOfficialUrl(event.url))
            sources.set(event.url, event.title);
          if (event.kind === "error") throw new Error(event.message);
          if (event.kind === "done") doneReceived = true;
          update();
        }
      }
      if (!doneReceived)
        throw new Error("La respuesta quedó incompleta; no reintenté automáticamente.");
      setStatus("ready");
      await queryClient.invalidateQueries({ queryKey: ["lexia-thread", threadId] });
    } catch (e) {
      if (control.signal.aborted) {
        setError("Consulta detenida. La respuesta parcial no se guardó.");
        setStatus("ready");
      } else {
        setError(e instanceof Error ? e.message : "No pude completar la consulta.");
        setInput(question);
        setStatus("error");
        toolState = "output-error";
        update();
      }
    } finally {
      abort.current = null;
      textarea.current?.focus({ preventScroll: true });
    }
  };

  useEffect(() => { sendRef.current = send; });
  useEffect(() => {
    if (!threadId || !user) return;
    const pending = sessionStorage.getItem(`lexia-pending-${threadId}`);
    if (!pending) return;
    let active = true;
    queueMicrotask(() => {
      if (!active) return;
      sessionStorage.removeItem(`lexia-pending-${threadId}`);
      void sendRef.current?.(pending);
    });
    return () => { active = false; };
  }, [threadId, user]);

  const handleSend = () => { if (input.trim()) void send(input); };
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  // --- Adjuntar archivo ---
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    // Por ahora solo anexamos el nombre del archivo al input
    // (la subida real requiere endpoint de backend)
    const names = Array.from(files).map((f) => f.name).join(", ");
    setInput((prev) => prev ? `${prev}\n[Archivo adjunto: ${names}]` : `[Archivo adjunto: ${names}]`);
    setShowAttach(false);
  };

  // --- Seleccionar modo de análisis ---
  const selectMode = (key: string) => {
    setAnalysisMode(key);
    setShowAnalyze(false);
    setShowMore(false);
  };

  const activeMode = getAnalysisOption(analysisMode);
  const ActiveIcon = ANALYSIS_ICONS[analysisMode] ?? Search;

  return (
    <section className="lexia-chat flex h-full flex-col" aria-label="Chat Lexia" data-client-ready={ready}>
      {/* --- Barra superior --- */}
      <div className="flex items-center justify-between border-b px-4 py-2.5">
        {/* Menú hamburguesa */}
        <button
          type="button"
          onClick={() => setSidebarOpen((v) => !v)}
          className="rounded-lg p-2 text-foreground hover:bg-muted transition-colors"
          title="Menú"
          aria-label="Abrir menú de navegación"
        >
          <Menu size={20} />
        </button>

        {/* Centro: título */}
        <div className="flex items-center gap-2">
          <img src={emblem} alt="" width={28} height={28} className="h-7 w-7 rounded-md" />
          <span className="font-display text-sm font-semibold text-navy hidden sm:inline">Lexia</span>
        </div>

        {/* Chat temporal (nueva conversación) */}
        <button
          type="button"
          onClick={() => { if (threadId) navigate({ to: "/asistente" }); }}
          className="rounded-lg p-2 text-foreground hover:bg-muted transition-colors"
          title="Nueva conversación"
          aria-label="Iniciar nueva conversación temporal"
        >
          <Plus size={20} />
        </button>
      </div>

      {/* --- Panel lateral desplegable --- */}
      {sidebarOpen && (
        <div className="absolute left-0 top-12 z-20 w-64 rounded-br-xl border bg-popover p-3 shadow-lg">
          <div className="mb-3 flex items-center gap-2 pb-2 border-b">
            <Gavel size={16} className="text-navy" />
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">LexIAParaguay</span>
          </div>
          <nav className="flex flex-col gap-1">
            <Link to="/" onClick={() => setSidebarOpen(false)} className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent">Inicio</Link>
            <Link to="/modulos" onClick={() => setSidebarOpen(false)} className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent">Módulos</Link>
            <Link to="/jurisprudencia" onClick={() => setSidebarOpen(false)} className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent">Jurisprudencia</Link>
            <Link to="/fuentes" onClick={() => setSidebarOpen(false)} className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent">Fuentes</Link>
            <Link to="/precios" onClick={() => setSidebarOpen(false)} className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent">Precios</Link>
            {!user && (
              <Link to="/auth" onClick={() => setSidebarOpen(false)} className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-primary hover:bg-accent">Ingresar</Link>
            )}
          </nav>
          <div className="mt-3 pt-3 border-t">
            <p className="flex items-center gap-1 text-[10px] text-success">
              <ShieldCheck size={12} /> Fuentes oficiales verificadas
            </p>
          </div>
        </div>
      )}

      {/* --- Área de mensajes (centro, pantalla completa) --- */}
      <Conversation className="min-h-0 flex-1">
        <ConversationContent className="mx-auto w-full max-w-3xl gap-5 p-4 sm:p-6">
          {messages.length === 0 && (
            <div className="flex min-h-56 flex-col items-center justify-center text-center sm:min-h-72">
              <img src={emblem} alt="Emblema de Lexia" width={64} height={64} className="mb-4 h-16 w-16 rounded-md" />
              <p className="text-xs font-bold uppercase tracking-widest text-kicker">Derecho paraguayo · www.lexiapy.com</p>
              <h1 className="font-display mt-3 text-2xl font-semibold text-navy">¿Qué necesitás resolver?</h1>
              <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
                Consultas, normas y procedimientos, con fundamentos verificables y supervisión humana.
              </p>
              <div className="mt-5 grid w-full gap-2 sm:grid-cols-2">
                {[
                  "¿Qué establece el Código del Trabajo sobre despido sin causa?",
                  "¿Qué ley regula los contratos de alquiler en Paraguay?",
                  "¿Cómo se regulan los honorarios judiciales?",
                  "¿Cómo se solicita asistencia alimenticia?",
                ].map((q) => (
                  <Button key={q} variant="outline" className="h-auto min-h-12 whitespace-normal text-left text-xs" onClick={() => { setInput(q); textarea.current?.focus(); }}>
                    {q}
                  </Button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m) => (
            <Message key={m.id} from={m.role}>
              {/* Timestamp */}
              <div className={`mb-1 text-[10px] text-muted-foreground ${m.role === "user" ? "text-right" : "text-left"}`}>
                {m.role === "user" ? "Vos" : "Lexia"} · {new Date().toLocaleTimeString("es-PY", { hour: "2-digit", minute: "2-digit" })}
              </div>
              <MessageContent
                className={
                  m.role === "user"
                    ? "group-[.is-user]:bg-primary group-[.is-user]:text-primary-foreground"
                    : "w-full"
                }
              >
                {m.parts.map((part, i) => {
                  if (part.type === "text")
                    return (
                      <MessageResponse key={i} isAnimating={busy && m.id === messages.at(-1)?.id}>
                        {part.text}
                      </MessageResponse>
                    );
                  if (part.type === "dynamic-tool")
                    return (
                      <Tool key={i} defaultOpen={false}>
                        <ToolHeader type="dynamic-tool" toolName="investigacion-oficial" title="Investigación oficial" state={part.state} />
                        <ToolContent>
                          <p className="text-xs text-muted-foreground">BACN · Poder Judicial · CSJ · Legislación y jurisprudencia paraguayas</p>
                        </ToolContent>
                      </Tool>
                    );
                  if (part.type === "source-url" && isOfficialUrl(part.url))
                    return (
                      <a key={i} href={part.url} target="_blank" rel="noopener noreferrer" className="flex items-start gap-2 break-words text-xs font-semibold text-link underline">
                        {part.title ?? part.url}
                      </a>
                    );
                  return null;
                })}
              </MessageContent>
              {m.role === "assistant" && m.parts.some((p) => p.type === "text" && (p as { text: string }).text) && (
                <div className="flex items-center gap-1">
                  <MessageAction tooltip="Copiar respuesta" label="Copiar" onClick={() => void navigator.clipboard.writeText(m.parts.filter((p) => p.type === "text").map((p) => (p as { text: string }).text).join("\n"))}>
                    <Copy size={14} />
                  </MessageAction>
                  {voice.ttsSupported && (
                    <button
                      type="button"
                      onClick={speakLast}
                      title="Escuchar respuesta"
                      className="rounded-md p-1.5 text-muted-foreground hover:bg-muted"
                    >
                      <Volume2 size={14} />
                    </button>
                  )}
                </div>
              )}
            </Message>
          ))}
          {status === "submitted" && <Shimmer className="text-sm">Investigando legislación paraguaya…</Shimmer>}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      {/* --- Controles de voz (TTS) --- */}
      {showVoiceControls && voice.speaking && (
        <div className="mx-auto flex w-full max-w-3xl items-center gap-2 px-4 pb-1">
          <button type="button" onClick={voice.paused ? voice.resumeSpeech : voice.pauseSpeech} className="rounded-md border p-1.5 text-foreground hover:bg-muted" title={voice.paused ? "Reanudar" : "Pausar"}>
            {voice.paused ? <Volume2 size={16} /> : <Pause size={16} />}
          </button>
          <button type="button" onClick={() => { voice.stopSpeech(); setShowVoiceControls(false); }} className="rounded-md border p-1.5 text-foreground hover:bg-muted" title="Detener">
            <X size={16} />
          </button>
          <span className="text-xs text-muted-foreground">{voice.paused ? "Pausado" : "Reproduciendo…"}</span>
        </div>
      )}

      {/* --- Error --- */}
      {error && (
        <p role="alert" className="mx-auto w-full max-w-3xl px-4 pb-1 text-sm text-destructive">{error}</p>
      )}

      {/* --- Auth prompt --- */}
      {!user && (
        <div className="mx-auto flex w-full max-w-3xl flex-wrap items-center justify-between gap-2 px-4 pb-1">
          <span className="text-xs text-muted-foreground">Iniciá sesión para consultar y guardar tus conversaciones.</span>
          <Button asChild size="sm"><Link to="/auth">Ingresar a mi cuenta</Link></Button>
        </div>
      )}

      {/* --- Barra inferior: adjuntar + textarea + analizar + más + mic --- */}
      <div className="mx-auto w-full max-w-3xl px-4 pb-3 pt-1">
        <div className="flex items-end gap-2 rounded-2xl border bg-background p-2 shadow-sm">
          {/* Adjuntar (abajo a la izquierda) */}
          <div className="relative" ref={attachRef}>
            <button
              type="button"
              onClick={() => setShowAttach((v) => !v)}
              className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="Adjuntar"
              aria-label="Adjuntar archivo"
            >
              <Paperclip size={20} />
            </button>
            {showAttach && (
              <div className="absolute bottom-full left-0 mb-2 z-10 w-52 rounded-xl border bg-popover p-1.5 shadow-lg">
                <label className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-accent" onClick={() => setShowAttach(false)}>
                  <FileText size={16} /> Desde el dispositivo
                  <input type="file" className="hidden" onChange={handleFileSelect} />
                </label>
                <button type="button" className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-accent" onClick={() => setShowAttach(false)}>
                  <FolderOpen size={16} /> Desde el almacenamiento
                </button>
              </div>
            )}
          </div>

          {/* Textarea central (expandible) */}
          <textarea
            ref={textarea}
            value={input + (voice.interimTranscript ? " " + voice.interimTranscript : "")}
            onChange={(e) => { setInput(e.target.value); adjustTextarea(); }}
            onKeyDown={handleKeyDown}
            aria-label="Tu consulta a Lexia"
            placeholder="Escribí tu consulta jurídica…"
            disabled={busy}
            rows={1}
            className="flex-1 resize-none border-0 bg-transparent py-2 text-sm outline-none placeholder:text-muted-foreground disabled:opacity-50"
            style={{ maxHeight: "200px" }}
          />

          {/* Botón Analizar (centro inferior) */}
          <div className="relative" ref={analyzeRef}>
            <button
              type="button"
              onClick={() => setShowAnalyze((v) => !v)}
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-2 text-xs font-medium transition-colors ${
                analysisMode !== "WEB_SEARCH" ? "bg-gold/10 text-navy" : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
              title={activeMode.label}
              aria-label="Modo de análisis"
            >
              <ActiveIcon size={18} />
            </button>
            {showAnalyze && (
              <div className="absolute bottom-full right-0 mb-2 z-10 w-56 rounded-xl border bg-popover p-1.5 shadow-lg">
                <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Analizar</p>
                {PRIMARY_MODES.map((key) => {
                  const opt = getAnalysisOption(key);
                  const Icon = ANALYSIS_ICONS[key];
                  return (
                    <button key={key} type="button" onClick={() => selectMode(key)} className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm hover:bg-accent ${analysisMode === key ? "bg-accent font-medium" : ""}`}>
                      <Icon size={16} className="shrink-0" />
                      <div className="text-left">
                        <div>{opt.label}</div>
                        <div className="text-[10px] text-muted-foreground">{opt.description}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Más opciones (...) */}
          <div className="relative" ref={moreRef}>
            <button
              type="button"
              onClick={() => setShowMore((v) => !v)}
              className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="Más opciones"
              aria-label="Más opciones"
            >
              <MoreHorizontal size={20} />
            </button>
            {showMore && (
              <div className="absolute bottom-full right-0 mb-2 z-10 w-60 rounded-xl border bg-popover p-1.5 shadow-lg">
                {/* Modos avanzados */}
                <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Análisis avanzado</p>
                {ADVANCED_MODES.map((key) => {
                  const opt = getAnalysisOption(key);
                  const Icon = ANALYSIS_ICONS[key];
                  return (
                    <button key={key} type="button" onClick={() => selectMode(key)} className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm hover:bg-accent ${analysisMode === key ? "bg-accent font-medium" : ""}`}>
                      <Icon size={16} className="shrink-0" />
                      <div className="text-left">
                        <div>{opt.label}</div>
                        <div className="text-[10px] text-muted-foreground">{opt.description}</div>
                      </div>
                    </button>
                  );
                })}
                <div className="my-1 border-t" />
                {/* Selector de fuero */}
                <div className="relative" ref={fueroRef}>
                  <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Fuero / Materia</p>
                  {FUEROS.map((f) => (
                    <button key={f} type="button" onClick={() => { setFuero(f); setShowFuero(false); setShowMore(false); }} className={`flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-sm hover:bg-accent ${f === fuero ? "bg-accent font-medium" : ""}`}>
                      {f}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Enviar / Detener */}
          <button
            type="button"
            onClick={() => (busy ? abort.current?.abort() : handleSend())}
            disabled={!user || (!busy && !input.trim())}
            className="rounded-lg bg-primary p-2.5 text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-40"
            title={busy ? "Detener" : "Enviar"}
            aria-label={busy ? "Detener consulta" : "Enviar consulta"}
          >
            {busy ? <Square size={18} className="fill-current" /> : <ArrowUp size={18} />}
          </button>

          {/* Micrófono (abajo a la derecha, circular negro) */}
          <button
            type="button"
            onClick={() => voice.listening ? voice.stopListening() : voice.startListening()}
            disabled={!voice.sttSupported}
            className={`rounded-full p-2.5 transition-colors ${
              voice.listening
                ? "bg-red-600 text-white animate-pulse"
                : "bg-black text-white hover:bg-black/80 disabled:opacity-30"
            }`}
            title={voice.listening ? "Detener dictado" : "Dictar por voz"}
            aria-label={voice.listening ? "Detener dictado por voz" : "Iniciar dictado por voz"}
          >
            <Mic size={18} />
          </button>
        </div>

        {/* Error de voz */}
        {voice.error && (
          <p className="mt-1 text-center text-[10px] text-muted-foreground">{voice.error}</p>
        )}
        {/* Indicador de escucha */}
        {voice.listening && (
          <p className="mt-1 text-center text-[10px] text-success">🎙 Escuchando… {voice.interimTranscript}</p>
        )}

        <p className="mt-1.5 text-center text-[10px] text-muted-foreground">
          Lexia puede cometer errores. Verificá las citas y la vigencia con un profesional.
        </p>
      </div>
    </section>
  );
}
