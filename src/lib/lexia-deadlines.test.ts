/**
 * Tests para el cálculo de plazos procesales paraguayos.
 */
import { describe, it, expect } from "vitest";
import { calculateCustomDeadline, calculateDeadline } from "./lexia-deadlines";
import { DEADLINE_RULES } from "./lexia-catalog";

describe("lexia-deadlines", () => {
  // Lunes 10 de marzo de 2025 (epoch ms a las 12:00 UTC)
  const monday = Date.UTC(2025, 2, 10, 12, 0, 0);

  it("calcula 5 días hábiles saltando fin de semana", () => {
    const result = calculateCustomDeadline({
      title: "Reposición",
      codeRef: "Art. 390 CPC",
      days: 5,
      dayType: "HABILES",
      baseDateEpochMs: monday,
      nowEpochMs: monday,
    });
    // 10 mar (lun) → 11, 12, 13, 14 (jue), 17 (lun) = 5 hábiles
    // Sábado 15 y domingo 16 saltados
    expect(result.daysRequested).toBe(5);
    expect(result.skippedHolidaysAndWeekends.length).toBeGreaterThanOrEqual(2);
    expect(result.skippedHolidaysAndWeekends.some((s) => s.includes("Fin de semana"))).toBe(true);
  });

  it("calcula 3 días corridos prorrogando al siguiente hábil", () => {
    const result = calculateCustomDeadline({
      title: "Test corridos",
      codeRef: "Test",
      days: 3,
      dayType: "CORRIDOS",
      baseDateEpochMs: monday,
      nowEpochMs: monday,
    });
    // 10 + 3 = 13 marzo (jueves) — es hábil
    expect(result.daysRequested).toBe(3);
    const due = new Date(result.dueDateEpochMs);
    expect(due.getUTCMonth()).toBe(2); // marzo
    expect(due.getUTCDate()).toBe(13);
  });

  it("corrige el día de vencimiento si cae en feriado (corridos)", () => {
    // 13 de mayo 2025 es martes — 13 + 1 = 14 (Independencia, feriado)
    const may13 = Date.UTC(2025, 4, 13, 12, 0, 0);
    const result = calculateCustomDeadline({
      title: "Test feriado",
      codeRef: "Test",
      days: 1,
      dayType: "CORRIDOS",
      baseDateEpochMs: may13,
      nowEpochMs: may13,
    });
    expect(result.skippedHolidaysAndWeekends.some((s) => s.includes("Independencia"))).toBe(true);
  });

  it("clasifica urgencia CRITICA cuando faltan 2 días o menos", () => {
    const result = calculateCustomDeadline({
      title: "Urgente",
      codeRef: "Test",
      days: 2,
      dayType: "HABILES",
      baseDateEpochMs: monday,
      nowEpochMs: monday,
    });
    expect(result.urgency).toBe("CRITICA");
  });

  it("usa una regla del catálogo correctamente", () => {
    const rule = DEADLINE_RULES.find((r) => r.key === "reposicion_cpc");
    expect(rule).toBeDefined();
    if (!rule) return;
    const result = calculateDeadline(rule, monday, monday);
    expect(result.ruleTitle).toBe(rule.title);
    expect(result.codeRef).toContain("CPC");
    expect(result.daysRequested).toBe(3);
  });
});
