import { describe, expect, it } from "vitest";

import { battleTrainerPresentation } from "./battleTrainerPresentation";
import type { BattleTranscript, CareerRun } from "./types";

function battle(featured: boolean): BattleTranscript {
  return {
    battle_id: "known-rival-battle",
    winner_team: "career-home",
    winner_label: "Home",
    rounds: 3,
    sha256: "known-rival",
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
      featured,
    } as BattleTranscript["spec"] & { featured: boolean },
    events: [],
    initial_state: { round: 1, battle_over: false, combatants: [] },
    final_state: { round: 3, battle_over: true, combatants: [] },
  };
}

function career(relationships: Record<string, number>): CareerRun {
  return {
    build: { name: "QA Trainer", region: "kanto", starter: "Bulbasaur", classes: [], pokeballs: 10 },
    relationships,
    timeline: [],
  } as unknown as CareerRun;
}

describe("known rival continuity", () => {
  it("brings the strongest established regional rival into the featured battle", () => {
    const run = career({
      "Blue · rival · Kanto": 4,
      "Red · rival · Kanto": 2,
    });
    const presentation = battleTrainerPresentation("es", battle(true), run);
    expect(presentation.away.name).toBe("Blue");
    expect(presentation.away.sprite).toBe("blue");
  });

  it("keeps ordinary fixtures tied to their club identity", () => {
    const run = career({ "Blue · rival · Kanto": 8 });
    const presentation = battleTrainerPresentation("es", battle(false), run);
    expect(presentation.away.name).toBe("Trace");
  });

  it("ignores malformed, foreign-region and unknown rival contacts", () => {
    const run = career({
      "Blue · rival · Johto": 99,
      "Missingno · rival · Kanto": 50,
      "Red · mentor · Kanto": 40,
      "Trace · rival · Kanto": Number.NaN,
    });
    const presentation = battleTrainerPresentation("es", battle(true), run);
    expect(presentation.away.name).toBe("Trace");
  });
});
