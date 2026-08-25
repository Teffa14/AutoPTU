import type { CareerRun, Locale } from "./types";

export type ClubTransitionQuestion = "rebuild" | "momentum" | "recovery" | "continuity" | "contract";

export interface ClubTransitionBrief {
  season: number;
  previousClub: string;
  newClub: string;
  renewal: boolean;
  salary: number;
  seasons: number;
  returnedLoans: string[];
  incomingLoans: string[];
  giftSpecies: string;
  perkLabel: string;
  record: string;
  questions: ClubTransitionQuestion[];
}

export function latestClubTransition(run: CareerRun): ClubTransitionBrief | null {
  const timeline = Array.isArray(run.timeline) ? run.timeline : [];
  let signIndex = -1;
  for (let index = timeline.length - 1; index >= 0; index -= 1) {
    const entry = asRecord(timeline[index]);
    if (entry.type === "club.offer_signed" && Number(entry.season ?? 0) === run.season_number) {
      signIndex = index;
      break;
    }
  }
  if (signIndex < 0) return null;

  const signed = asRecord(timeline[signIndex]);
  const newClub = cleanText(signed.club);
  if (!newClub) return null;

  const renewal = signed.renewal === true;
  const previousClub = renewal ? newClub : previousSignedClub(timeline, signIndex) || returnedLoanClub(timeline, signIndex);
  const returnedLoans = renewal ? [] : returnedLoanSpecies(timeline, signIndex);
  const incomingLoans = stringList(signed.loan_species);
  const record = previousSeasonRecord(timeline, signIndex, run.season_number);

  return {
    season: run.season_number,
    previousClub,
    newClub,
    renewal,
    salary: finiteInt(signed.salary),
    seasons: Math.max(1, finiteInt(signed.seasons) || 1),
    returnedLoans,
    incomingLoans,
    giftSpecies: cleanText(signed.gift_species),
    perkLabel: cleanText(asRecord(signed.perk).label),
    record,
    questions: questionFamilies({ renewal, returnedLoans, record }),
  };
}

export function clubTransitionQuestionText(question: ClubTransitionQuestion, brief: ClubTransitionBrief, locale: Locale): string {
  const es = locale === "es";
  if (question === "rebuild") return es
    ? `Volvieron ${brief.returnedLoans.length} Pokémon cedidos. ¿Cómo vas a reconstruir el plantel en ${brief.newClub}?`
    : `${brief.returnedLoans.length} loan Pokémon returned. How will you rebuild the squad at ${brief.newClub}?`;
  if (question === "momentum") return es
    ? `Venís de un registro ${brief.record}. ¿Qué querés sostener en esta nueva etapa?`
    : `You are coming off a ${brief.record} record. What do you want to carry into this next chapter?`;
  if (question === "recovery") return es
    ? `Venís de un registro ${brief.record}. ¿Qué necesita cambiar esta temporada?`
    : `You are coming off a ${brief.record} record. What needs to change this season?`;
  if (question === "continuity") return es
    ? `Renovaste con ${brief.newClub}. ¿Qué querés consolidar con la continuidad?`
    : `You renewed with ${brief.newClub}. What do you want to consolidate through continuity?`;
  return es
    ? `Firmaste por ${brief.seasons} ${brief.seasons === 1 ? "temporada" : "temporadas"} con ${brief.newClub}. ¿Cuál es tu prioridad inmediata?`
    : `You signed for ${brief.seasons} ${brief.seasons === 1 ? "season" : "seasons"} with ${brief.newClub}. What is your immediate priority?`;
}

function questionFamilies(input: { renewal: boolean; returnedLoans: string[]; record: string }): ClubTransitionQuestion[] {
  const questions: ClubTransitionQuestion[] = [];
  if (input.returnedLoans.length >= 2) questions.push("rebuild");
  const recordTrend = parseRecord(input.record);
  if (recordTrend > 0) questions.push("momentum");
  else if (recordTrend < 0) questions.push("recovery");
  if (input.renewal) questions.push("continuity");
  questions.push("contract");
  return questions.slice(0, 3);
}

function previousSignedClub(timeline: Record<string, unknown>[], signIndex: number): string {
  for (let index = signIndex - 1; index >= 0; index -= 1) {
    const entry = asRecord(timeline[index]);
    if (entry.type !== "club.offer_signed") continue;
    const club = cleanText(entry.club);
    if (club) return club;
  }
  return "";
}

function returnedLoanClub(timeline: Record<string, unknown>[], signIndex: number): string {
  for (let index = signIndex - 1; index >= 0; index -= 1) {
    const entry = asRecord(timeline[index]);
    if (entry.type === "club.offer_signed") break;
    if (entry.type !== "club.loans_returned") continue;
    const club = cleanText(entry.club);
    if (club) return club;
  }
  return "";
}

function returnedLoanSpecies(timeline: Record<string, unknown>[], signIndex: number): string[] {
  const returned: string[] = [];
  for (let index = signIndex - 1; index >= 0; index -= 1) {
    const entry = asRecord(timeline[index]);
    if (entry.type === "club.offer_signed") break;
    if (entry.type !== "club.loans_returned") continue;
    const pokemon = Array.isArray(entry.pokemon) ? entry.pokemon : [];
    const species = pokemon.flatMap((value) => {
      const name = cleanText(asRecord(value).species);
      return name ? [name] : [];
    });
    returned.unshift(...species);
  }
  return returned;
}

function previousSeasonRecord(timeline: Record<string, unknown>[], signIndex: number, currentSeason: number): string {
  for (let index = signIndex - 1; index >= 0; index -= 1) {
    const entry = asRecord(timeline[index]);
    if (entry.type !== "season.completed") continue;
    const season = Number(entry.season ?? 0);
    if (season >= currentSeason) continue;
    return cleanText(entry.record);
  }
  return "";
}

function parseRecord(record: string): number {
  const values = record.match(/\d+/g)?.map(Number) ?? [];
  if (values.length < 2 || !values.every(Number.isFinite)) return 0;
  return values[0] - values[1];
}

function stringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map(cleanText).filter(Boolean);
}

function finiteInt(value: unknown): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.max(0, Math.trunc(parsed)) : 0;
}

function cleanText(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}
