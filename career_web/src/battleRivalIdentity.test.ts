import { describe, expect, it } from "vitest";

import { battleTrainerPresentation } from "./battleTrainerPresentation";
import type { BattleTranscript } from "./types";

const baseTranscript = {
  battle_id: "rival-formatting",
  winner_team: "career-home",
  winner_label: "Home",
  rounds: 3,
  sha256: "formatting",
  spec: {
    home_club: "Saffron Comets",
    away_club: "Cerulean Current",
    home_species: "Bulbasaur",
    away_species: "Squirtle",
    region: "kanto",
    league: "junior",
    season: 3,
    level: 13,
    away_team_levels: [12, 13, 14],
    difficulty_label: "even",
  },
  events: [],
  initial_state: { round: 1, battle_over: false, combatants: [] },
  final_state: { round: 3, battle_over: true, combatants: [] },
} as BattleTranscript;

describe("battle rival identity persistence", () => {
  it("keeps the same rival NPC when persisted club formatting drifts", () => {
    const canonical = battleTrainerPresentation("es", baseTranscript, null, false);
    const migrated = battleTrainerPresentation("es", {
      ...baseTranscript,
      spec: {
        ...baseTranscript.spec,
        region: " KANTO ",
        away_club: "  CERULEAN   CURRENT  ",
      },
    } as BattleTranscript, null, false);

    expect(migrated.away.name).toBe(canonical.away.name);
    expect(migrated.away.sprite).toBe(canonical.away.sprite);
  });
});
