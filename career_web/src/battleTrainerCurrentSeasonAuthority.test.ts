import { describe, expect, it } from "vitest";

import { battleTrainerPresentation, formalRivalMemory } from "./battleTrainerPresentation";
import type { BattleTranscript, CareerRun } from "./types";

const run = {
  build: { name: "QA Trainer", region: "kanto", starter: "Bulbasaur", classes: [], pokeballs: 10 },
  timeline: [
    { type: "season.completed", season: 1, opponents: ["Cerulean Current"] },
    { type: "season.completed", season: 2, opponents: ["Cerulean Current"] },
  ],
} as unknown as CareerRun;

const transcript = {
  battle_id: "battle-current-season-authority",
  winner_team: "career-home",
  winner_label: "Home",
  rounds: 1,
  sha256: "authority",
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
  final_state: { round: 1, battle_over: true, combatants: [] },
} as BattleTranscript;

describe("battle rival current-season authority", () => {
  it("fails closed instead of coercing a malformed current battle season", () => {
    const hostileSeason = {
      valueOf: () => {
        throw new Error("persisted season coercion must not run");
      },
    };
    const malformedTranscript = {
      ...transcript,
      spec: { ...transcript.spec, season: hostileSeason },
    } as unknown as BattleTranscript;

    expect(() => battleTrainerPresentation("es", malformedTranscript, run, false)).not.toThrow();
    expect(battleTrainerPresentation("es", malformedTranscript, run, false).rivalMemory).toEqual({
      previousMeetings: 2,
      firstSeason: 1,
      lastSeason: 2,
      seasonsSinceLastMeeting: null,
    });
    expect(formalRivalMemory(run, "Cerulean Current", hostileSeason as unknown as number)).toEqual({
      previousMeetings: 2,
      firstSeason: 1,
      lastSeason: 2,
      seasonsSinceLastMeeting: null,
    });
  });
});
