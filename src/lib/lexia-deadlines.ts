/**
 * Cálculo de plazos procesales paraguayos — adaptado de ParaguayDeadlineCalculator.kt.
 *
 * Pure function: feriados nacionales fijos, Semana Santa (Pascua), días hábiles/corridos,
 * clasificación de urgencia. Sin dependencias externas; testeable directamente.
 */

import type { DeadlineDayType, DeadlineRuleSpec } from "./lexia-catalog";

export interface DeadlineResult {
  ruleTitle: string;
  codeRef: string;
  baseDateEpochMs: number;
  dueDateEpochMs: number;
  formattedBaseDate: string;
  formattedDueDate: string;
  daysRequested: number;
  dayType: DeadlineDayType;
  skippedHolidaysAndWeekends: string[];
  remainingCalendarDays: number;
  urgency: string;
}

const PARAGUAY_TZ = "America/Asuncion";

// Feriados nacionales fijos (mes 1-12, día)
const FIXED_HOLIDAYS: Record<string, string> = {
  "1-1": "Año Nuevo",
  "3-1": "Día de los Héroes",
  "5-1": "Día del Trabajo",
  "5-14": "Independencia Nacional (14 de Mayo)",
  "5-15": "Independencia Nacional (15 de Mayo)",
  "6-12": "Paz del Chaco",
  "8-15": "Fundación de Asunción",
  "9-29": "Victoria de Boquerón",
  "12-8": "Virgen de Caacupé",
  "12-25": "Navidad",
};

/** Cálculo de Pascua (Domingo de Resurrección) — algoritmo de Gauss/Computus. */
function easterSunday(year: number): Date {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31); // 3=Marzo, 4=Abril
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(Date.UTC(year, month - 1, day, 12, 0, 0));
}

function getHolidayName(date: Date): string | null {
  const key = `${date.getUTCMonth() + 1}-${date.getUTCDate()}`;
  if (FIXED_HOLIDAYS[key]) return FIXED_HOLIDAYS[key];

  const year = date.getUTCFullYear();
  const easter = easterSunday(year);
  const maundyThursday = new Date(easter.getTime() - 3 * 86400000);
  const goodFriday = new Date(easter.getTime() - 2 * 86400000);

  if (sameDate(date, maundyThursday)) return "Jueves Santo";
  if (sameDate(date, goodFriday)) return "Viernes Santo";
  return null;
}

function sameDate(a: Date, b: Date): boolean {
  return (
    a.getUTCFullYear() === b.getUTCFullYear() &&
    a.getUTCMonth() === b.getUTCMonth() &&
    a.getUTCDate() === b.getUTCDate()
  );
}

function isBusinessDay(date: Date): boolean {
  const dow = date.getUTCDay();
  if (dow === 0 || dow === 6) return false; // domingo o sábado
  return getHolidayName(date) === null;
}

function formatLongDate(epochMs: number): string {
  const days = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
  const months = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
  ];
  const d = new Date(epochMs);
  const dayName = days[d.getUTCDay()];
  const day = d.getUTCDate();
  const month = months[d.getUTCMonth()];
  const year = d.getUTCFullYear();
  return `${dayName.charAt(0).toUpperCase()}${dayName.slice(1)} ${String(day).padStart(2, "0")}/${String(month === "enero" ? 1 : months.indexOf(month) + 1).padStart(2, "0")}/${year}`;
}

function formatShortDate(epochMs: number): string {
  const d = new Date(epochMs);
  const dd = String(d.getUTCDate()).padStart(2, "0");
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  return `${dd}/${mm}/${d.getUTCFullYear()}`;
}

function normalizeToNoon(epochMs: number): number {
  const d = new Date(epochMs);
  d.setUTCHours(12, 0, 0, 0);
  return d.getTime();
}

export function calculateDeadline(
  rule: DeadlineRuleSpec,
  baseDateEpochMs: number,
  nowEpochMs: number = Date.now(),
): DeadlineResult {
  return calculateCustomDeadline({
    title: rule.title,
    codeRef: rule.codeRef,
    days: rule.days,
    dayType: rule.dayType,
    baseDateEpochMs,
    nowEpochMs,
  });
}

export function calculateCustomDeadline(params: {
  title: string;
  codeRef: string;
  days: number;
  dayType: DeadlineDayType;
  baseDateEpochMs: number;
  nowEpochMs?: number;
}): DeadlineResult {
  const { title, codeRef, dayType } = params;
  const safeDays = Math.max(1, Math.min(3650, params.days));
  const nowEpochMs = params.nowEpochMs ?? Date.now();

  const cursor = new Date(normalizeToNoon(params.baseDateEpochMs));
  const normalizedBaseMs = cursor.getTime();
  const skipped: string[] = [];

  if (dayType === "CORRIDOS") {
    cursor.setUTCDate(cursor.getUTCDate() + safeDays);
    while (!isBusinessDay(cursor)) {
      const reason = getHolidayName(cursor) ?? "Fin de semana";
      skipped.push(`${formatShortDate(cursor.getTime())} (${reason} · prórroga Art. 147 CPC)`);
      cursor.setUTCDate(cursor.getUTCDate() + 1);
    }
  } else {
    // Hábiles: los plazos empiezan a correr desde el día siguiente hábil
    let counted = 0;
    while (counted < safeDays) {
      cursor.setUTCDate(cursor.getUTCDate() + 1);
      const dow = cursor.getUTCDay();
      const holiday = getHolidayName(cursor);
      if (dow === 0 || dow === 6) {
        skipped.push(`${formatShortDate(cursor.getTime())} (Fin de semana)`);
      } else if (holiday !== null) {
        skipped.push(`${formatShortDate(cursor.getTime())} (${holiday})`);
      } else {
        counted++;
      }
    }
  }

  const dueMs = cursor.getTime();
  const diffDays = Math.round((dueMs - normalizeToNoon(nowEpochMs)) / 86400000);
  const urgency = diffDays <= 2 ? "CRITICA" : diffDays <= 5 ? "ALTA" : diffDays <= 12 ? "MEDIA" : "BAJA";

  return {
    ruleTitle: title,
    codeRef,
    baseDateEpochMs: normalizedBaseMs,
    dueDateEpochMs: dueMs,
    formattedBaseDate: formatLongDate(normalizedBaseMs),
    formattedDueDate: formatLongDate(dueMs),
    daysRequested: safeDays,
    dayType,
    skippedHolidaysAndWeekends: skipped,
    remainingCalendarDays: diffDays,
    urgency,
  };
}
