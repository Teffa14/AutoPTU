import type { BattleTranscript, CareerRun, Locale } from "./types";
import { DEFAULT_TRAINER_SPRITE, trainerSpriteForRun } from "./trainerSprites";

export type BattleTrainerCard = {
  name: string;
  sprite: string;
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

const EMPTY_RIVAL_MEMORY: RivalMemory = {
  previousMeetings: 0,
  firstSeason: null,
  lastSeason: null,
  seasonsSinceLastMeeting: null,
};

export function battleTrainerPresentation(
  locale: Locale,
  transcript: BattleTranscript,
  run?: CareerRun | null,
  _complete = false,
): BattleTrainerPresentation {
  const region = normalizeRegionIdentity(transcript.spec.region);
  const awayClub = String(transcript.spec.away_club || "Opponent");
  const normalizedAwayClub = normalizeClubIdentity(awayClub) || "opponent";
  const pool = REGIONAL_RIVALS[region] ?? REGIONAL_RIVALS.kanto;
  const clubRival = pool[stableIndex(`${region}:${normalizedAwayClub}`, pool.length)];
  const featured = (transcript.spec as typeof transcript.spec & { featured?: unknown }).featured === true;
  const rival = featured ? knownRegionalRival(run, region, pool) ?? clubRival : clubRival;
  const rivalMemory = formalRivalMemory(run, awayClub, transcript.spec.season);
  const meeting = rivalMemory.previousMeetings + 1;

  return {
    home: {
      name: run?.build.name || transcript.spec.home_club || (locale === "es" ? "Entrenador" : "Trainer"),
      sprite: run ? trainerSpriteForRun(run) : DEFAULT_TRAINER_SPRITE,
    },
    away: {
      name: rival.name,
      sprite: rival.sprite,
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
  if (!run) return EMPTY_RIVAL_MEMORY;
  const normalizedAwayClub = normalizeClubIdentity(awayClub);
  if (!normalizedAwayClub) return EMPTY_RIVAL_MEMORY;

  let authoritativeBeforeSeason: number | undefined;
  if (beforeSeason !== undefined) {
    const parsedBeforeSeason = authoritativePositiveNumber(beforeSeason);
    if (parsedBeforeSeason === null) return EMPTY_RIVAL_MEMORY;
    authoritativeBeforeSeason = parsedBeforeSeason;
  }

  let previousMeetings = 0;
  let firstSeason: number | null = null;
  let lastSeason: number | null = null;
  const timeline = Array.isArray(run.timeline) ? run.timeline : [];
  for (const event of timeline) {
    if (!event || typeof event !== "object") continue;
    if (event.type !== "season.completed" || !Array.isArray(event.opponents)) continue;
    const eventSeason = authoritativePositiveNumber(event.season);
    if (eventSeason === null) continue;
    if (authoritativeBeforeSeason !== undefined && eventSeason >= authoritativeBeforeSeason) continue;
    const meetings = event.opponents.filter((opponent) => normalizeClubIdentity(opponent) === normalizedAwayClub).length;
    if (!meetings) continue;
    previousMeetings += meetings;
    firstSeason = firstSeason === null ? eventSeason : Math.min(firstSeason, eventSeason);
    lastSeason = lastSeason === null ? eventSeason : Math.max(lastSeason, eventSeason);
  }
  const seasonsSinceLastMeeting = authoritativeBeforeSeason !== undefined && lastSeason !== null
    ? Math.max(0, authoritativeBeforeSeason - lastSeason)
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

function knownRegionalRival(
  run: CareerRun | null | undefined,
  region: string,
  pool: RivalIdentity[],
): RivalIdentity | null {
  if (!run || !run.relationships || typeof run.relationships !== "object") return null;
  const regionLabel = region.toLocaleLowerCase("en-US");
  const candidates: { rival: RivalIdentity; bond: number }[] = [];
  for (const [rawContact, rawBond] of Object.entries(run.relationships)) {
    if (typeof rawContact !== "string") continue;
    const [rawName, rawRole, rawRegion] = rawContact.split(" · ");
    if (!rawName || rawRole?.trim().toLocaleLowerCase("en-US") !== "rival") continue;
    if (rawRegion?.trim().toLocaleLowerCase("en-US") !== regionLabel) continue;
    const rival = pool.find((entry) => entry.name.toLocaleLowerCase("en-US") === rawName.trim().toLocaleLowerCase("en-US"));
    if (!rival) continue;
    const bond = authoritativeNonNegativeNumber(rawBond);
    if (bond === null || bond <= 0) continue;
    candidates.push({ rival, bond });
  }
  candidates.sort((left, right) => right.bond - left.bond || left.rival.name.localeCompare(right.rival.name));
  return candidates[0]?.rival ?? null;
}

function normalizeRegionIdentity(value: unknown): string {
  if (typeof value !== "string") return "kanto";
  return value.trim().toLocaleLowerCase("en-US") || "kanto";
}

function normalizeClubIdentity(value: unknown): string {
  if (typeof value !== "string") return "";
  return value.trim().replace(/\s+/g, " ").toLocaleLowerCase("en-US");
}

function authoritativePositiveNumber(value: unknown): number | null {
  if (typeof value !== "number" && typeof value !== "string") return null;
  if (typeof value === "string" && !value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function authoritativeNonNegativeNumber(value: unknown): number | null {
  if (typeof value !== "number" && typeof value !== "string") return null;
  if (typeof value === "string" && !value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
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
  const seasonValue = authoritativePositiveNumber(transcript.spec.season);
  const season = seasonValue === null ? null : Math.floor(seasonValue);
  const levels = Array.isArray(transcript.spec.away_team_levels)
    ? transcript.spec.away_team_levels
      .map(authoritativePositiveNumber)
      .filter((value): value is number => value !== null)
    : [];
  const fallbackLevel = authoritativePositiveNumber(transcript.spec.level);
  const averageLevel = levels.length
    ? Math.round(levels.reduce((total, value) => total + value, 0) / levels.length)
    : fallbackLevel === null
      ? null
      : Math.round(fallbackLevel);
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
