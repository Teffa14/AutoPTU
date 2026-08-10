import type { Locale } from "./types";

const copy = {
  es: {
    season: "Temporada", trainer: "Entrenador", timeline: "Historia", daily: "Reto diario",
    createTitle: "Tu carrera empieza abajo", createBody: "Doce años. Diez Poké Balls. Un compañero al que nadie eligió.",
    start: "Firmar primer contrato", health: "Salud", score: "Índice competitivo", choose: "Tomar esta decisión",
    retire: "Retirarse", battle: "Retransmisión", skip: "Saltar al resultado", speed: "Velocidad", back: "Volver a la temporada",
  },
  en: {
    season: "Season", trainer: "Trainer", timeline: "Story", daily: "Daily challenge",
    createTitle: "Your career starts at the bottom", createBody: "Twelve years old. Ten Poké Balls. One partner nobody chose.",
    start: "Sign first contract", health: "Health", score: "Competitive index", choose: "Make this decision",
    retire: "Retire", battle: "Broadcast", skip: "Skip to result", speed: "Speed", back: "Back to season",
  },
} as const;

export function t(locale: Locale) {
  return copy[locale];
}
