import type { Locale } from "./types";

const LABELS: Record<string, [string, string]> = {
  "First victory": ["Primera victoria", "First victory"],
  "Full squad": ["Equipo completo", "Full squad"],
  "Perfect season": ["Temporada perfecta", "Perfect season"],
  "Evolution specialist": ["Especialista en evolución", "Evolution specialist"],
  "Rising star": ["Estrella en ascenso", "Rising star"],
  "Elite contender": ["Contendiente Elite", "Elite contender"],
  Veteran: ["Veterano de liga", "League veteran"],
};

export function achievementLabel(value: string, locale: Locale): string {
  const direct = LABELS[value];
  if (direct) return direct[locale === "es" ? 0 : 1];
  const champion = value.match(/^(.+) champion$/i);
  if (champion) return locale === "es" ? `Campeón de ${champion[1]}` : `${champion[1]} champion`;
  return value;
}
