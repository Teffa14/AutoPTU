import { describe, expect, it } from "vitest";

import { pendingBattleRecovery } from "./seasonRecovery";
import type { CareerRun } from "./types";

function runWithSeason(status: string, completed: number, required: number, battleIds: string[]): CareerRun {
  return {
    id: "run-1",
    status: "active",
    season_number: 1,
    build: { name: "QA", region: "kanto", starter: "Bulbasaur", classes: [], pokeballs: 10 },
    season: {
      number: 1,
      age: 12,
      league: "junior",
      club_name: "Saffron Comets",
      status,
      battle_ids: battleIds,
      decisions_required: required,
      decisions_completed: completed,
      decision_history: [],
      training_completed: false,
      training_method: "",
      training_completed_ids: [],
    },
  } as unknown as CareerRun;
}

describe("pendingBattleRecovery", () => {
  it("treats completed decisions plus battle status as recovery, not a new decision", () => {
    const recovery = pendingBattleRecovery(runWithSeason("battle", 1, 1, ["run-1-s1-m1", "run-1-s1-m6"]));
    expect(recovery).toEqual({
      battleId: "run-1-s1-m6",
      seasonNumber: 1,
      decisionsCompleted: 1,
      decisionsRequired: 1,
    });
  });

  it("works for advanced careers after the third decision", () => {
    const recovery = pendingBattleRecovery(runWithSeason("battle", 3, 3, ["featured"]));
    expect(recovery?.battleId).toBe("featured");
    expect(recovery?.decisionsCompleted).toBe(3);
  });

  it("does not intercept a real decision phase", () => {
    expect(pendingBattleRecovery(runWithSeason("decision", 0, 1, []))).toBeNull();
  });

  it("keeps a corrupt pending state visible even if the battle id is missing", () => {
    expect(pendingBattleRecovery(runWithSeason("battle", 1, 1, []))?.battleId).toBeNull();
  });
});
