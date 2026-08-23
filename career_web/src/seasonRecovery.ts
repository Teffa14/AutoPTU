import type { CareerRun } from "./types";

export type PendingBattleRecovery = {
  battleId: string | null;
  seasonNumber: number;
  decisionsCompleted: number;
  decisionsRequired: number;
  phaseRepairNeeded: boolean;
};

function isExhaustedDecisionPhase(run: CareerRun): boolean {
  const season = run.season;
  if (run.status !== "active" || !season || season.status !== "decision") return false;
  const required = season.decisions_required ?? 0;
  const completed = season.decisions_completed ?? 0;
  return required > 0 && completed >= required;
}

export function repairExhaustedDecisionPhase(run: CareerRun): CareerRun | null {
  if (!isExhaustedDecisionPhase(run) || !run.season) return null;
  const battleIds = (run.season.battle_ids ?? []).filter((value) => typeof value === "string" && value.length > 0);
  if (!battleIds.length) return null;
  return {
    ...run,
    season: {
      ...run.season,
      status: "battle",
    },
  };
}

export function pendingBattleRecovery(run: CareerRun): PendingBattleRecovery | null {
  const season = run.season;
  if (run.status !== "active" || !season) return null;
  const phaseRepairNeeded = isExhaustedDecisionPhase(run);
  if (season.status !== "battle" && !phaseRepairNeeded) return null;

  const battleIds = (season.battle_ids ?? []).filter((value) => typeof value === "string" && value.length > 0);
  return {
    battleId: battleIds.at(-1) ?? null,
    seasonNumber: season.number ?? run.season_number,
    decisionsCompleted: season.decisions_completed ?? 0,
    decisionsRequired: season.decisions_required ?? 0,
    phaseRepairNeeded,
  };
}
