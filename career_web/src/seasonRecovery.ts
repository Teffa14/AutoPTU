import type { CareerPokemon, CareerRun } from "./types";

export type PendingBattleRecovery = {
  battleId: string | null;
  seasonNumber: number;
  decisionsCompleted: number;
  decisionsRequired: number;
  phaseRepairNeeded: boolean;
};

function decisionProgress(run: CareerRun): { completed: number; required: number; displayedCompleted: number } {
  const season = run.season;
  const required = Math.max(0, season?.decisions_required ?? 0);
  const completed = Math.max(0, season?.decisions_completed ?? 0);
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

export function normalizedActiveLineup(run: CareerRun): CareerPokemon[] {
  const activeRoster = Array.isArray(run.active_roster) ? run.active_roster : [];
  const pokemon = Array.isArray(run.pokemon)
    ? run.pokemon.filter((entry): entry is CareerPokemon => Boolean(entry) && typeof entry === "object" && typeof entry.id === "string")
    : [];
  const byId = new Map(pokemon.map((entry) => [entry.id, entry]));
  return activeRoster
    .filter((id): id is string => typeof id === "string")
    .map((id) => byId.get(id))
    .filter((entry): entry is CareerPokemon => entry !== undefined);
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
