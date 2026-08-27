import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { battleTrainerPresentation } from "./battleTrainerPresentation";
import type { BattleTranscript, CareerRun } from "./types";

const transcript = {
  battle_id: "career-1-s5-m2",
  winner_team: "career-home",
  winner_label: "Home",
  rounds: 3,
  sha256: "abc",
  spec: {
    home_club: "Saffron Comets",
    away_club: "Cerulean Current",
    home_species: "Ivysaur",
    away_species: "Wartortle",
    home_team_levels: [28, 31, 33],
    away_team_levels: [30, 31, 32],
    region: "kanto",
    league: "regular",
    season: 5,
    level: 31,
    difficulty_label: "even",
  },
  events: [],
  initial_state: { round: 1, battle_over: false, combatants: [] },
  final_state: { round: 3, battle_over: true, combatants: [] },
} as BattleTranscript;

const run = {
  build: { name: "Ari", region: "kanto", starter: "Ivysaur", classes: [], pokeballs: 8 },
  reputation: 7,
  timeline: [{ type: "trainer.appearance_selected", trainer_sprite: "hilda" }],
} as unknown as CareerRun;

describe("player battle progression", () => {
  it("shows the player's actual season, scheduled team level and reputation beside the trainer", () => {
    const presentation = battleTrainerPresentation("es", transcript, run, false);
    expect(presentation.home.progression).toBe("T5 · NIVEL MEDIO 31 · REPUTACIÓN 7");
    expect(presentation.home.sprite).toBe("hilda");
  });

  it("fails closed for malformed player progression metadata", () => {
    const malformedTranscript = {
      ...transcript,
      spec: {
        ...transcript.spec,
        season: Number.POSITIVE_INFINITY,
        level: Number.NaN,
        home_team_levels: [Number.NaN, Number.POSITIVE_INFINITY, -2],
      },
    } as BattleTranscript;
    const malformedRun = { ...run, reputation: Number.NaN } as unknown as CareerRun;
    const progression = battleTrainerPresentation("es", malformedTranscript, malformedRun, false).home.progression;
    expect(progression).toBe("");
    expect(progression).not.toContain("NaN");
    expect(progression).not.toContain("Infinity");
  });

  it("renders the computed home progression in the battle trainer strip", () => {
    const source = readFileSync(fileURLToPath(new URL("./components/BattleTrainerStrip.tsx", import.meta.url)), "utf8");
    expect(source).toContain("progression={presentation.home.progression}");
  });
});
