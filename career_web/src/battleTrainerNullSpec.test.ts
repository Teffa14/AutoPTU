import { describe, expect, it } from "vitest";

import { battleTrainerPresentation } from "./battleTrainerPresentation";
import type { BattleTranscript } from "./types";

describe("battle trainer presentation malformed spec resilience", () => {
  it("does not crash when a legacy transcript has a null spec", () => {
    const malformed = {
      battle_id: "legacy-null-spec",
      winner_team: "career-home",
      winner_label: "Home",
      rounds: 0,
      sha256: "legacy",
      spec: null,
      events: [],
      initial_state: { round: 1, battle_over: false, combatants: [] },
      final_state: { round: 1, battle_over: false, combatants: [] },
    } as unknown as BattleTranscript;

    expect(() => battleTrainerPresentation("es", malformed, null, false)).not.toThrow();
  });
});
