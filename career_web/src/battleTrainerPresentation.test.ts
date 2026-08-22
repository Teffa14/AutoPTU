import { describe, expect, it } from "vitest";

import { battleTrainerPresentation, previousMeetings } from "./battleTrainerPresentation";
import type { BattleTranscript, CareerRun } from "./types";

const transcript = {
  battle_id: "battle-1",
  winner_team: "career-home",
  winner_label: "Home",
  rounds: 3,
  sha256: "abc",
  spec: {
    home_club: "Saffron Comets",
    away_club: "Cerulean Current",
    home_species: "Bulbasaur",
    away_species: "Squirtle",
    region: "kanto",
    league: "junior",
    season: 3,
    difficulty_label: "even",
  },
  events: [],
  initial_state: { round: 1, battle_over: false, combatants: [] },
  final_state: { round: 3, battle_over: true, combatants: [] },
} as BattleTranscript;

const run = {
  build: { name: "QA Trainer", region: "kanto", starter: "Bulbasaur", classes: [], pokeballs: 10 },
  timeline: [
    { type: "trainer.appearance_selected", trainer_sprite: "hilda" },
    { type: "season.completed", season: 1, opponents: ["Cerulean Current", "Pewter Foundry", "Cerulean Current"] },
    { type: "season.completed", season: 2, opponents: ["Fuchsia Wardens"] },
    // Simulates finalizeSeason finishing while the season-3 replay is still on screen.
    { type: "season.completed", season: 3, opponents: ["Cerulean Current"] },
  ],
} as CareerRun;

describe("battle trainer presentation", () => {
  it("keeps a stable rival identity for the same regional club", () => {
    const first = battleTrainerPresentation("es", transcript, run, false);
    const second = battleTrainerPresentation("es", transcript, run, false);
    expect(first.away.name).toBe(second.away.name);
    expect(first.away.sprite).toBe(second.away.sprite);
  });

  it("counts only formal meetings before the battle currently being replayed", () => {
    expect(previousMeetings(run, "Cerulean Current")).toBe(3);
    expect(previousMeetings(run, "Cerulean Current", 3)).toBe(2);
    expect(battleTrainerPresentation("es", transcript, run, false).meeting).toBe(3);
    expect(battleTrainerPresentation("es", transcript, run, false).meetingLabel).toBe("CRUCE #3");
  });

  it("uses the selected player trainer sprite and changes dialogue after the result", () => {
    const opening = battleTrainerPresentation("es", transcript, run, false);
    const result = battleTrainerPresentation("es", transcript, run, true);
    expect(opening.home.name).toBe("QA Trainer");
    expect(opening.home.sprite).toBe("hilda");
    expect(result.home.line).not.toBe(opening.home.line);
    expect(result.away.line).not.toBe(opening.away.line);
  });
});
