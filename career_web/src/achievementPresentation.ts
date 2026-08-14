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

export function achievementDescription(value: string, locale: Locale): string {
  const descriptions: Record<string, [string, string]> = {
    "First victory": ["Ganaste tu primer combate oficial de liga.", "You won your first official league battle."],
    "Full squad": ["Capturaste al menos seis Pokémon durante la carrera.", "You caught at least six Pokémon during the career."],
    "Perfect season": ["Terminaste una temporada con victorias y sin derrotas.", "You finished a season with wins and no losses."],
    "Evolution specialist": ["Tu equipo registró al menos tres evoluciones.", "Your team recorded at least three evolutions."],
    "Rising star": ["Conseguiste un ascenso de liga.", "You earned promotion to a higher league."],
    "Elite contender": ["Alcanzaste la Liga Elite.", "You reached the Elite League."],
    Veteran: ["Completaste al menos cinco temporadas profesionales.", "You completed at least five professional seasons."],
  };
  const direct = descriptions[value];
  if (direct) return direct[locale === "es" ? 0 : 1];
  if (/ champion$/i.test(value)) return locale === "es" ? "Ganaste el título de esa liga." : "You won that league title.";
  return locale === "es" ? "Hito conseguido durante esta carrera." : "Milestone earned during this career.";
}
