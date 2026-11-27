/**
 * Hook de voz para el chat jurídico de Lexia.
 *
 * STT: Web Speech API (SpeechRecognition) — dictado de consultas.
 * TTS: Web Speech API (speechSynthesis) — síntesis de voz real, no simulada.
 *
 * No requiere claves API ni llamadas a servidor; usa las APIs nativas del navegador.
 * Si el navegador no soporta una función, se reporta `supported: false` sin simular.
 */

import { useCallback, useEffect, useRef, useState } from "react";

// --- Tipos mínimos para SpeechRecognition (no en TS DOM lib por defecto) ---
interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}
interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}
interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}
interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}
interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}
interface ISpeechRecognition extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}
type SpeechRecognitionCtor = new () => ISpeechRecognition;

function getRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  return (
    (window as unknown as { SpeechRecognition?: SpeechRecognitionCtor }).SpeechRecognition ||
    (window as unknown as { webkitSpeechRecognition?: SpeechRecognitionCtor }).webkitSpeechRecognition ||
    null
  );
}

export interface VoiceState {
  sttSupported: boolean;
  ttsSupported: boolean;
  listening: boolean;
  speaking: boolean;
  paused: boolean;
  transcript: string;
  interimTranscript: string;
  error: string | null;
  voices: SpeechSynthesisVoice[];
  selectedVoiceURI: string | null;
}

export function useVoice() {
  const recognitionRef = useRef<ISpeechRecognition | null>(null);
  const [sttSupported] = useState(() => getRecognitionCtor() !== null);
  const [ttsSupported] = useState(() => typeof window !== "undefined" && "speechSynthesis" in window);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [paused, setPaused] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoiceURI, setSelectedVoiceURI] = useState<string | null>(null);

  // Cargar voces disponibles
  useEffect(() => {
    if (!ttsSupported) return;
    const loadVoices = () => {
      const available = window.speechSynthesis.getVoices();
      setVoices(available);
      // Preferir voz en español
      const esVoice = available.find((v) => v.lang.startsWith("es"));
      if (esVoice && !selectedVoiceURI) setSelectedVoiceURI(esVoice.voiceURI);
    };
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, [ttsSupported]); // eslint-disable-line react-hooks/exhaustive-deps

  // --- STT ---
  const startListening = useCallback(() => {
    const Ctor = getRecognitionCtor();
    if (!Ctor) {
      setError("Tu navegador no soporta reconocimiento de voz.");
      return;
    }
    setError(null);
    setTranscript("");
    setInterimTranscript("");

    const rec = new Ctor();
    rec.lang = "es-PY";
    rec.continuous = false;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    rec.onstart = () => setListening(true);
    rec.onend = () => {
      setListening(false);
      setInterimTranscript("");
    };
    rec.onerror = (e) => {
      setListening(false);
      if (e.error === "not-allowed") setError("Permiso de micrófono denegado.");
      else if (e.error === "no-speech") setError("No se detectó voz.");
      else setError(`Error de reconocimiento: ${e.error}`);
    };
    rec.onresult = (e) => {
      let final = "";
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const result = e.results[i];
        if (result.isFinal) final += result[0].transcript;
        else interim += result[0].transcript;
      }
      if (final) setTranscript((prev) => (prev ? prev + " " : "") + final.trim());
      setInterimTranscript(interim);
    };

    recognitionRef.current = rec;
    rec.start();
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
  }, []);

  // --- TTS ---
  const speak = useCallback(
    (text: string) => {
      if (!ttsSupported || !text.trim()) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "es-PY";
      if (selectedVoiceURI) {
        const voice = voices.find((v) => v.voiceURI === selectedVoiceURI);
        if (voice) utterance.voice = voice;
      }
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.onstart = () => { setSpeaking(true); setPaused(false); };
      utterance.onend = () => { setSpeaking(false); setPaused(false); };
      utterance.onerror = () => { setSpeaking(false); setPaused(false); };
      window.speechSynthesis.speak(utterance);
    },
    [ttsSupported, selectedVoiceURI, voices],
  );

  const pauseSpeech = useCallback(() => {
    if (!ttsSupported) return;
    window.speechSynthesis.pause();
    setPaused(true);
  }, [ttsSupported]);

  const resumeSpeech = useCallback(() => {
    if (!ttsSupported) return;
    window.speechSynthesis.resume();
    setPaused(false);
  }, [ttsSupported]);

  const stopSpeech = useCallback(() => {
    if (!ttsSupported) return;
    window.speechSynthesis.cancel();
    setSpeaking(false);
    setPaused(false);
  }, [ttsSupported]);

  const selectVoice = useCallback((uri: string) => {
    setSelectedVoiceURI(uri);
  }, []);

  // Limpiar al desmontar
  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      if (ttsSupported) window.speechSynthesis.cancel();
    };
  }, [ttsSupported]);

  return {
    sttSupported,
    ttsSupported,
    listening,
    speaking,
    paused,
    transcript,
    interimTranscript,
    error,
    voices,
    selectedVoiceURI,
    startListening,
    stopListening,
    speak,
    pauseSpeech,
    resumeSpeech,
    stopSpeech,
    selectVoice,
  };
}
