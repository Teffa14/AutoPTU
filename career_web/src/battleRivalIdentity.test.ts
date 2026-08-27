import { describe, expect, it } from "vitest";

import { battleTrainerPresentation, formalRivalMemory } from "./battleTrainerPresentation";
import type { BattleTranscript, CareerRun } from "./types";

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

  it("does not fabricate rival meetings from coerced timeline seasons", () => {
    const run = {
      timeline: [
        { type: "season.completed", season: true, opponents: ["Cerulean Current"] },
        { type: "season.completed", season: { valueOf: () => 2 }, opponents: ["Cerulean Current"] },
      ],
    } as unknown as CareerRun;

    expect(formalRivalMemory(run, "Cerulean Current", 3)).toEqual({
      previousMeetings: 0,
      firstSeason: null,
      lastSeason: null,
      seasonsSinceLastMeeting: null,
    });
  });

  it("does not attribute a club's historical meetings to a relationship-selected featured rival", () => {
    const featured = {
      ...baseTranscript,
      spec: { ...baseTranscript.spec, featured: true, season: 7 },
    } as BattleTranscript;
    const run = {
      build: { name: "Ari", region: "kanto", starter: "Bulbasaur", classes: [], pokeballs: 10 },
      relationships: { "Blue · Rival · kanto": 4 },
      timeline: [
        { type: "season.completed", season: 1, opponents: ["Cerulean Current"] },
        { type: "season.completed", season: 2, opponents: ["Cerulean Current"] },
        { type: "season.completed", season: 3, opponents: ["Cerulean Current"] },
        { type: "season.completed", season: 4, opponents: ["Cerulean Current"] },
        { type: "season.completed", season: 5, opponents: ["Cerulean Current"] },
      ],
    } as unknown as CareerRun;

    const presentation = battleTrainerPresentation("es", featured, run, false);
    expect(presentation.away.name).toBe("Blue");
    expect(presentation.rivalMemory.previousMeetings).toBe(5);
    expect(presentation.meetingLabel).toBe("RIVALIDAD ACTIVA");
    expect(presentation.meetingLabel).not.toContain("CRUCE #6");
  });

  it("keeps club-series meeting labels when no relationship rival overrides the featured opponent", () => {
    const featured = {
      ...baseTranscript,
      spec: { ...baseTranscript.spec, featured: true, season: 3 },
    } as BattleTranscript;
    const run = {
      build: { name: "Ari", region: "kanto", starter: "Bulbasaur", classes: [], pokeballs: 10 },
      timeline: [
        { type: "season.completed", season: 1, opponents: ["Cerulean Current"] },
        { type: "season.completed", season: 2, opponents: ["Cerulean Current"] },
      ],
    } as unknown as CareerRun;

    expect(battleTrainerPresentation("es", featured, run, false).meetingLabel).toBe("CRUCE #3");
  });
});
