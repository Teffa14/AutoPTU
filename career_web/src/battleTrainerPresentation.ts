import type { BattleTranscript, CareerRun, Locale } from "./types";
import { DEFAULT_TRAINER_SPRITE, trainerSpriteForRun } from "./trainerSprites";

export type BattleTrainerCard = {
  name: string;
  sprite: string;
  line: string;
  progression?: string;
};

export type RivalMemory = {
  previousMeetings: number;
  firstSeason: number | null;
  lastSeason: number | null;
  seasonsSinceLastMeeting: number | null;
};

export type BattleTrainerPresentation = {
  home: BattleTrainerCard;
  away: BattleTrainerCard;
  meeting: number;
  meetingLabel: string;
  rivalMemory: RivalMemory;
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
  const rivalMemory = formalRivalMemory(run, awayClub, transcript.spec.season);
  const meeting = rivalMemory.previousMeetings + 1;
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
        ? rivalResultLine(locale, userWon, rivalMemory)
        : rivalOpeningLine(locale, rivalMemory),
      progression: rivalProgressionLine(locale, transcript),
    },
    meeting,
    meetingLabel: meetingLabel(locale, meeting, rivalMemory),
    rivalMemory,
  };
}

export function formalRivalMemory(
  run: CareerRun | null | undefined,
  awayClub: string,
  beforeSeason?: number,
): RivalMemory {
  if (!run) return { previousMeetings: 0, firstSeason: null, lastSeason: null, seasonsSinceLastMeeting: null };
  const normalizedAwayClub = normalizeClubIdentity(awayClub);
  if (!normalizedAwayClub) return { previousMeetings: 0, firstSeason: null, lastSeason: null, seasonsSinceLastMeeting: null };
  let previousMeetings = 0;
  let firstSeason: number | null = null;
  let lastSeason: number | null = null;
  const timeline = Array.isArray(run.timeline) ? run.timeline : [];
  for (const event of timeline) {
    if (!event || typeof event !== "object") continue;
    if (event.type !== "season.completed" || !Array.isArray(event.opponents)) continue;
    const eventSeason = Number(event.season ?? 0);
    if (!Number.isFinite(eventSeason) || eventSeason <= 0) continue;
    if (beforeSeason !== undefined && eventSeason >= beforeSeason) continue;
    const meetings = event.opponents.filter((opponent) => normalizeClubIdentity(opponent) === normalizedAwayClub).length;
    if (!meetings) continue;
    previousMeetings += meetings;
    firstSeason = firstSeason === null ? eventSeason : Math.min(firstSeason, eventSeason);
    lastSeason = lastSeason === null ? eventSeason : Math.max(lastSeason, eventSeason);
  }
  const seasonsSinceLastMeeting = beforeSeason !== undefined && lastSeason !== null
    ? Math.max(0, beforeSeason - lastSeason)
    : null;
  return { previousMeetings, firstSeason, lastSeason, seasonsSinceLastMeeting };
}

export function previousMeetings(
  run: CareerRun | null | undefined,
  awayClub: string,
  beforeSeason?: number,
): number {
  return formalRivalMemory(run, awayClub, beforeSeason).previousMeetings;
}

function normalizeClubIdentity(value: unknown): string {
  if (typeof value !== "string") return "";
  return value.trim().replace(/\s+/g, " ").toLocaleLowerCase("en-US");
}

function stableIndex(value: string, modulo: number): number {
  let hash = 2166136261;
  for (const character of value) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return modulo > 0 ? hash % modulo : 0;
}

function meetingLabel(locale: Locale, meeting: number, memory: RivalMemory): string {
  if (meeting === 1) return locale === "es" ? "PRIMER CRUCE" : "FIRST MEETING";
  if (memory.previousMeetings >= 5) return locale === "es" ? `RIVALIDAD · CRUCE #${meeting}` : `RIVALRY · MEETING #${meeting}`;
  if ((memory.seasonsSinceLastMeeting ?? 0) >= 3) return locale === "es" ? `REENCUENTRO · CRUCE #${meeting}` : `REUNION · MEETING #${meeting}`;
  return locale === "es" ? `CRUCE #${meeting}` : `MEETING #${meeting}`;
}

function rivalProgressionLine(locale: Locale, transcript: BattleTranscript): string {
  const seasonValue = Number(transcript.spec.season ?? 0);
  const season = Number.isFinite(seasonValue) && seasonValue > 0 ? Math.floor(seasonValue) : null;
  const levels = Array.isArray(transcript.spec.away_team_levels)
    ? transcript.spec.away_team_levels
      .map((value) => Number(value))
      .filter((value) => Number.isFinite(value) && value > 0)
    : [];
  const fallbackLevel = Number(transcript.spec.level ?? 0);
  const averageLevel = levels.length
    ? Math.round(levels.reduce((total, value) => total + value, 0) / levels.length)
    : Number.isFinite(fallbackLevel) && fallbackLevel > 0
      ? Math.round(fallbackLevel)
      : null;
  const stage = season === null
    ? null
    : season >= 8
      ? (locale === "es" ? "VETERANO" : "VETERAN")
      : season >= 4
        ? (locale === "es" ? "CONSOLIDADO" : "ESTABLISHED")
        : (locale === "es" ? "EN DESARROLLO" : "DEVELOPING");
  const parts = [
    season === null ? "" : `${locale === "es" ? "T" : "S"}${season}`,
    averageLevel === null ? "" : `${locale === "es" ? "NIVEL MEDIO" : "AVG LEVEL"} ${averageLevel}`,
    stage ?? "",
  ].filter(Boolean);
  return parts.join(" · ");
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

function rivalOpeningLine(locale: Locale, memory: RivalMemory): string {
  if (locale === "es") {
    if (memory.previousMeetings >= 5) return "Ya tenemos historia. Hoy no alcanza con repetir lo que funcionó antes.";
    if ((memory.seasonsSinceLastMeeting ?? 0) >= 3) return "Pasó tiempo. Quiero ver qué cambió desde la última vez.";
    if (memory.previousMeetings > 0) return "Ya vi tu plan una vez. Mostrame qué cambiaste.";
    return "Quiero ver cómo resolvés cuando el plan se rompe.";
  }
  if (memory.previousMeetings >= 5) return "We have history now. Repeating what worked before will not be enough.";
  if ((memory.seasonsSinceLastMeeting ?? 0) >= 3) return "It has been a while. Show me what changed since last time.";
  if (memory.previousMeetings > 0) return "I have seen your plan before. Show me what changed.";
  return "I want to see what you do when the plan breaks.";
}

function homeResultLine(locale: Locale, userWon: boolean): string {
  if (locale === "es") return userWon ? "Listo. Esto queda en el registro." : "Anoten dónde nos abrió. Lo trabajamos.";
  return userWon ? "Done. This goes in the record." : "Mark where they opened us up. We work on it.";
}

function rivalResultLine(locale: Locale, userWon: boolean, memory: RivalMemory): string {
  if (locale === "es") {
    if (memory.previousMeetings >= 5) return userWon ? "Otra para vos. El registro sigue abierto." : "Otra para mí. El registro sigue abierto.";
    return userWon ? "Bien. La próxima vengo con otra respuesta." : "La próxima vas a tener que cambiar algo.";
  }
  if (memory.previousMeetings >= 5) return userWon ? "Another one for you. The record stays open." : "Another one for me. The record stays open.";
  return userWon ? "Good. Next time I bring a different answer." : "Next time you will have to change something.";
}
