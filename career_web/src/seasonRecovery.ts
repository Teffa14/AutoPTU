import type { CareerPokemon, CareerRun } from "./types";

export type PendingBattleRecovery = {
  battleId: string | null;
  seasonNumber: number;
  decisionsCompleted: number;
  decisionsRequired: number;
  phaseRepairNeeded: boolean;
};

function safeNonnegativeInteger(value: unknown): number {
  if (typeof value !== "number" && typeof value !== "string") return 0;
  if (typeof value === "string" && !value.trim()) return 0;
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) return 0;
  return Math.trunc(parsed);
}

function decisionProgress(run: CareerRun): { completed: number; required: number; displayedCompleted: number } {
  const season = run.season;
  const required = safeNonnegativeInteger(season?.decisions_required);
  const completed = safeNonnegativeInteger(season?.decisions_completed);
  return {
    completed,
    required,
    displayedCompleted: required > 0 ? Math.min(completed, required) : completed,
  };
}

function isExhaustedDecisionPhase(run: CareerRun): boolean {
  const season = run.season;
  if (run.status !== "active" || !season || season.status !== "decision") return false;
  const progress = decisionProgress(run);
  return progress.required > 0 && progress.completed >= progress.required;
}

function normalizedBattleIds(run: CareerRun): string[] {
  return (run.season?.battle_ids ?? [])
    .filter((value): value is string => typeof value === "string")
    .map((value) => value.trim())
    .filter(Boolean);
}

function normalizedPokemon(run: CareerRun): CareerPokemon[] {
  if (!Array.isArray(run.pokemon)) return [];
  const seen = new Set<string>();
  const normalized: CareerPokemon[] = [];
  let changed = false;
  for (const entry of run.pokemon) {
    if (!entry || typeof entry !== "object" || typeof entry.id !== "string" || !entry.id.trim()) {
      changed = true;
      continue;
    }
    if (seen.has(entry.id)) {
      changed = true;
      continue;
    }
    seen.add(entry.id);
    normalized.push(entry);
  }
  return changed ? normalized : (run.pokemon as CareerPokemon[]);
}

export function normalizedActiveLineup(run: CareerRun): CareerPokemon[] {
  const activeRoster = Array.isArray(run.active_roster) ? run.active_roster : [];
  const pokemon = normalizedPokemon(run);
  const byId = new Map(pokemon.map((entry) => [entry.id, entry]));
  const seen = new Set<string>();
  return activeRoster
    .filter((id): id is string => typeof id === "string")
    .map((id) => id.trim())
    .filter(Boolean)
    .filter((id) => {
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    })
    .map((id) => byId.get(id))
    .filter((entry): entry is CareerPokemon => entry !== undefined)
    .slice(0, 6);
}

export function normalizeSeasonRosterState(run: CareerRun): CareerRun {
  const pokemon = normalizedPokemon(run);
  const activeRoster = normalizedActiveLineup({ ...run, pokemon }).map((entry) => entry.id);
  const rosterUnchanged =
    Array.isArray(run.active_roster) &&
    activeRoster.length === run.active_roster.length &&
    activeRoster.every((id, index) => id === run.active_roster[index]);
  if (pokemon === run.pokemon && rosterUnchanged) return run;
  return { ...run, pokemon, active_roster: activeRoster };
}

export function repairExhaustedDecisionPhase(run: CareerRun): CareerRun | null {
  if (!isExhaustedDecisionPhase(run) || !run.season) return null;
  const battleIds = normalizedBattleIds(run);
  if (!battleIds.length) return null;
  const progress = decisionProgress(run);
  return {
    ...run,
    season: {
      ...run.season,
      battle_ids: battleIds,
      decisions_completed: progress.displayedCompleted,
      status: "battle",
    },
  };
}

export function pendingBattleRecovery(run: CareerRun): PendingBattleRecovery | null {
  const season = run.season;
  if (run.status !== "active" || !season) return null;
  const phaseRepairNeeded = isExhaustedDecisionPhase(run);
  if (season.status !== "battle" && !phaseRepairNeeded) return null;

  const battleIds = normalizedBattleIds(run);
  const progress = decisionProgress(run);
  return {
    battleId: battleIds.at(-1) ?? null,
    seasonNumber: season.number ?? run.season_number,
    decisionsCompleted: progress.displayedCompleted,
    decisionsRequired: progress.required,
    phaseRepairNeeded,
  };
}
