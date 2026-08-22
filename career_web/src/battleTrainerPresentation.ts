import type { BattleTranscript, CareerRun, Locale } from "./types";
import { DEFAULT_TRAINER_SPRITE, trainerSpriteForRun } from "./trainerSprites";

export type BattleTrainerCard = {
  name: string;
  sprite: string;
  line: string;
};

export type BattleTrainerPresentation = {
  home: BattleTrainerCard;
  away: BattleTrainerCard;
  meeting: number;
  meetingLabel: string;
};

type RivalIdentity = { name: string; sprite: string };

const REGIONAL_RIVALS: Record<string, RivalIdentity[]> = {
  kanto: [
    { name: "Blue", sprite: "blue" },
    { name: "Red", sprite: "red" },
    { name: "Trace", sprite: "trace" },
  ],
  johto: [
    { name: "Silver", sprite: "silver" },
    { name: "Ethan", sprite: "ethan" },
    { name: "Lyra", sprite: "lyra" },
  ],
  hoenn: [
    { name: "Brendan", sprite: "brendan" },
    { name: "May", sprite: "may" },
    { name: "Wally", sprite: "wally" },
  ],
  sinnoh: [
    { name: "Barry", sprite: "barry-masters" },
    { name: "Lucas", sprite: "lucas" },
    { name: "Dawn", sprite: "dawn" },
  ],
  unova: [
    { name: "Bianca", sprite: "bianca" },
    { name: "Hilbert", sprite: "hilbert" },
    { name: "Hilda", sprite: "hilda" },
  ],
  kalos: [
    { name: "Serena", sprite: "serena" },
    { name: "Calem", sprite: "calem" },
    { name: "Shauna", sprite: "shauna" },
  ],
  alola: [
    { name: "Hau", sprite: "hau" },
    { name: "Gladion", sprite: "gladion" },
    { name: "Selene", sprite: "selene" },
  ],
  galar: [
    { name: "Hop", sprite: "hop" },
    { name: "Bede", sprite: "bede" },
    { name: "Marnie", sprite: "marnie" },
  ],
  paldea: [
    { name: "Nemona", sprite: "nemona-s" },
    { name: "Arven", sprite: "arven-s" },
    { name: "Penny", sprite: "penny" },
  ],
};

export function battleTrainerPresentation(
  locale: Locale,
  transcript: BattleTranscript,
  run?: CareerRun | null,
  complete = false,
): BattleTrainerPresentation {
  const region = String(transcript.spec.region || "kanto").toLowerCase();
  const awayClub = String(transcript.spec.away_club || "Opponent");
  const pool = REGIONAL_RIVALS[region] ?? REGIONAL_RIVALS.kanto;
  const rival = pool[stableIndex(`${region}:${awayClub}`, pool.length)];
  const meeting = previousMeetings(run, awayClub, transcript.spec.season) + 1;
  const userWon = transcript.winner_team === "career-home";
  const difficulty = transcript.spec.difficulty_label ?? "even";

  return {
    home: {
      name: run?.build.name || transcript.spec.home_club || (locale === "es" ? "Entrenador" : "Trainer"),
      sprite: run ? trainerSpriteForRun(run) : DEFAULT_TRAINER_SPRITE,
      line: complete
        ? homeResultLine(locale, userWon)
        : homePlanLine(locale, difficulty),
    },
    away: {
      name: rival.name,
      sprite: rival.sprite,
      line: complete
        ? rivalResultLine(locale, userWon)
        : rivalOpeningLine(locale, meeting),
    },
    meeting,
    meetingLabel: meeting === 1
      ? (locale === "es" ? "PRIMER CRUCE" : "FIRST MEETING")
      : (locale === "es" ? `CRUCE #${meeting}` : `MEETING #${meeting}`),
  };
}

export function previousMeetings(
  run: CareerRun | null | undefined,
  awayClub: string,
  beforeSeason?: number,
): number {
  if (!run) return 0;
  return run.timeline.reduce((total, event) => {
    if (event.type !== "season.completed" || !Array.isArray(event.opponents)) return total;
    const eventSeason = Number(event.season ?? 0);
    if (beforeSeason !== undefined && eventSeason >= beforeSeason) return total;
    return total + event.opponents.filter((opponent) => String(opponent) === awayClub).length;
  }, 0);
}

function stableIndex(value: string, modulo: number): number {
  let hash = 2166136261;
  for (const character of value) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return modulo > 0 ? hash % modulo : 0;
}

function homePlanLine(locale: Locale, difficulty: "favored" | "even" | "dangerous"): string {
  if (locale === "es") {
    if (difficulty === "dangerous") return "Primer turno: información. Después aceleramos.";
    if (difficulty === "favored") return "Nada de relajarse. Terminamos el trabajo.";
    return "No adivinen. Lean y ejecuten.";
  }
  if (difficulty === "dangerous") return "First turn: information. Then we accelerate.";
  if (difficulty === "favored") return "No relaxing. Finish the job.";
  return "Do not guess. Read and execute.";
}

function rivalOpeningLine(locale: Locale, meeting: number): string {
  if (locale === "es") {
    return meeting > 1
      ? "Ya vi tu plan una vez. Mostrame qué cambiaste."
      : "Quiero ver cómo resolvés cuando el plan se rompe.";
  }
  return meeting > 1
    ? "I have seen your plan before. Show me what changed."
    : "I want to see what you do when the plan breaks.";
}

function homeResultLine(locale: Locale, userWon: boolean): string {
  if (locale === "es") return userWon ? "Listo. Esto queda en el registro." : "Anoten dónde nos abrió. Lo trabajamos.";
  return userWon ? "Done. This goes in the record." : "Mark where they opened us up. We work on it.";
}

function rivalResultLine(locale: Locale, userWon: boolean): string {
  if (locale === "es") return userWon ? "Bien. La próxima vengo con otra respuesta." : "La próxima vas a tener que cambiar algo.";
  return userWon ? "Good. Next time I bring a different answer." : "Next time you will have to change something.";
}
