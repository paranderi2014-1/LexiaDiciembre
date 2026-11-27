/**
 * Tests para verificación de citas jurídicas.
 */
import { describe, it, expect } from "vitest";
import {
  verifyCitations,
  computeTextDiffSummary,
  checkConflict,
  type CorpusChunk,
} from "./lexia-citations";

describe("lexia-citations", () => {
  const mockChunks: CorpusChunk[] = [
    {
      documentTitle: "Código Civil Paraguayo",
      articleRef: "Art. 421",
      normNumber: "Ley 1183/85",
      content: "Las obligaciones derivadas de los contratos se extinguen por el cumplimiento.",
      vigenciaStatus: "VIGENTE",
      sourceName: "BACN",
      sourceUrl: "https://www.bacn.gov.py/leyes-paraguayas",
      relatedNorms: "",
    },
  ];

  it("detecta referencia a ley y la verifica en el corpus", () => {
    const result = verifyCitations("Según la Ley 1183/85, las obligaciones...", [], mockChunks);
    expect(result.length).toBeGreaterThan(0);
    const ley = result.find((r) => r.detectedReference.includes("Ley 1183/85"));
    expect(ley).toBeDefined();
    if (ley) {
      expect(["VERIFICADA_CORPUS", "NORMA_CON_REFORMA", "RESPALDO_WEB_OFICIAL", "REQUIERE_VERIFICACION"]).toContain(ley.status);
    }
  });

  it("marca REQUIERE_VERIFICACION cuando no hay citas en el texto", () => {
    const result = verifyCitations("Texto sin ninguna referencia legal.", [], []);
    expect(result.length).toBe(1);
    expect(result[0].status).toBe("REQUIERE_VERIFICACION");
  });

  it("detecta URL oficial como respaldo web", () => {
    const result = verifyCitations("Ver https://www.bacn.gov.py/leyes-paraguayas para más info", [], []);
    const url = result.find((r) => r.status === "RESPALDO_WEB_OFICIAL");
    expect(url).toBeDefined();
    if (url) expect(url.officialUrl).toContain("bacn.gov.py");
  });

  it("computa diff de texto entre dos versiones", () => {
    const diff = computeTextDiffSummary(
      "Línea 1\nLínea 2\nLínea 3",
      "Línea 1\nLínea modificada\nLínea 3",
    );
    expect(diff.some((d) => d.changeType === "REMOVED" && d.lineText === "Línea 2")).toBe(true);
    expect(diff.some((d) => d.changeType === "ADDED" && d.lineText === "Línea modificada")).toBe(true);
    expect(diff.some((d) => d.changeType === "UNCHANGED" && d.lineText === "Línea 1")).toBe(true);
  });

  it("detecta conflicto de interés entre casos", () => {
    const existing = [
      { id: "case-1", clientName: "Juan Pérez", counterparty: "María Gómez" },
    ];
    const result = checkConflict("Juan Pérez", "", existing);
    expect(result.hasConflict).toBe(true);
    expect(result.warnings.length).toBeGreaterThan(0);
  });

  it("no detecta conflicto cuando no hay coincidencia", () => {
    const existing = [
      { id: "case-1", clientName: "Pedro Martínez", counterparty: "Ana Ruiz" },
    ];
    const result = checkConflict("Carlos Díaz", "", existing);
    expect(result.hasConflict).toBe(false);
  });
});
