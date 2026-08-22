import type { CareerRun } from "./types";

export type PendingBattleRecovery = {
  battleId: string | null;
  seasonNumber: number;
  decisionsCompleted: number;
  decisionsRequired: number;
};

export function pendingBattleRecovery(run: CareerRun): PendingBattleRecovery | null {
  const season = run.season;
  if (run.status !== "active" || !season || season.status !== "battle") return null;

  const battleIds = (season.battle_ids ?? []).filter((value) => typeof value === "string" && value.length > 0);
  return {
    battleId: battleIds.at(-1) ?? null,
    seasonNumber: season.number ?? run.season_number,
    decisionsCompleted: season.decisions_completed ?? 0,
    decisionsRequired: season.decisions_required ?? 0,
  };
}
