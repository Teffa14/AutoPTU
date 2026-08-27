import { describe, expect, it } from "vitest";

import { battleTrainerPresentation, formalRivalMemory, previousMeetings } from "./battleTrainerPresentation";
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
    level: 13,
    away_team_levels: [12, 13, 14],
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
    { type: "season.completed", season: 3, opponents: ["Cerulean Current"] },
  ],
} as unknown as CareerRun;

describe("battle trainer presentation", () => {
  it("keeps a stable rival identity for the same regional club", () => {
    const first = battleTrainerPresentation("es", transcript, run, false);
    const second = battleTrainerPresentation("es", transcript, run, false);
    expect(first.away.name).toBe(second.away.name);
    expect(first.away.sprite).toBe(second.away.sprite);
  });

  it("shows rival progression from the battle data the engine actually scheduled", () => {
    const presentation = battleTrainerPresentation("es", transcript, run, false);
    expect(presentation.away.progression).toBe("T3 · NIVEL MEDIO 13 · EN DESARROLLO");

    const veteranTranscript = {
      ...transcript,
      spec: { ...transcript.spec, season: 9, level: 44, away_team_levels: [42, 44, 46] },
    } as BattleTranscript;
    expect(battleTrainerPresentation("en", veteranTranscript, run, false).away.progression)
      .toBe("S9 · AVG LEVEL 44 · VETERAN");
  });

  it("never exposes NaN or Infinity when persisted battle level metadata is malformed", () => {
    const malformed = {
      ...transcript,
      spec: {
        ...transcript.spec,
        season: 4,
        level: Number.NaN,
        away_team_levels: [Number.NaN, Number.POSITIVE_INFINITY, -4],
      },
    } as BattleTranscript;
    const progression = battleTrainerPresentation("es", malformed, run, false).away.progression;
    expect(progression).toBe("T4 · CONSOLIDADO");
    expect(progression).not.toContain("NaN");
    expect(progression).not.toContain("Infinity");
  });

  it("does not fabricate rival progression from coercible persisted metadata", () => {
    const coercible = {
      ...transcript,
      spec: {
        ...transcript.spec,
        season: true,
        level: true,
        away_team_levels: [true, { valueOf: () => 99 }],
      },
    } as unknown as BattleTranscript;
    expect(battleTrainerPresentation("es", coercible, run, false).away.progression).toBe("");
  });

  it("counts only formal meetings before the battle currently being replayed", () => {
    expect(previousMeetings(run, "Cerulean Current")).toBe(3);
    expect(previousMeetings(run, "Cerulean Current", 3)).toBe(2);
    expect(formalRivalMemory(run, "Cerulean Current", 3)).toEqual({
      previousMeetings: 2,
      firstSeason: 1,
      lastSeason: 1,
      seasonsSinceLastMeeting: 2,
    });
    expect(battleTrainerPresentation("es", transcript, run, false).meeting).toBe(3);
    expect(battleTrainerPresentation("es", transcript, run, false).meetingLabel).toBe("CRUCE #3");
  });

  it("preserves formal rival memory across harmless persisted club-name formatting drift", () => {
    const migratedRun = {
      ...run,
      timeline: [
        { type: "season.completed", season: 1, opponents: [" cerulean   current ", "CERULEAN CURRENT"] },
        { type: "season.completed", season: 2, opponents: [null, 123, { name: "Cerulean Current" }] },
      ],
    } as unknown as CareerRun;
    expect(formalRivalMemory(migratedRun, "Cerulean Current", 3)).toEqual({
      previousMeetings: 2,
      firstSeason: 1,
      lastSeason: 1,
      seasonsSinceLastMeeting: 2,
    });
    expect(formalRivalMemory(migratedRun, "   ", 3).previousMeetings).toBe(0);
  });

  it("uses the selected player sprite without injecting result dialogue", () => {
    const opening = battleTrainerPresentation("es", transcript, run, false);
    const result = battleTrainerPresentation("es", transcript, run, true);
    expect(opening.home.name).toBe("QA Trainer");
    expect(opening.home.sprite).toBe("hilda");
    expect(result.home).toEqual(opening.home);
    expect("line" in opening.home).toBe(false);
    expect("line" in opening.away).toBe(false);
  });

  it("distinguishes a reunion after several seasons from an ordinary rematch", () => {
    const reunionRun = {
      ...run,
      timeline: [
        { type: "season.completed", season: 1, opponents: ["Cerulean Current"] },
        { type: "season.completed", season: 2, opponents: ["Pewter Foundry"] },
        { type: "season.completed", season: 3, opponents: ["Fuchsia Wardens"] },
        { type: "season.completed", season: 4, opponents: ["Saffron Comets"] },
      ],
    } as unknown as CareerRun;
    const laterTranscript = { ...transcript, spec: { ...transcript.spec, season: 5 } } as BattleTranscript;
    const presentation = battleTrainerPresentation("es", laterTranscript, reunionRun, false);
    expect(presentation.rivalMemory.seasonsSinceLastMeeting).toBe(4);
    expect(presentation.meetingLabel).toBe("REENCUENTRO · CRUCE #2");
  });

  it("marks long-running formal rivalries without changing battle mechanics", () => {
    const rivalryRun = {
      ...run,
      timeline: Array.from({ length: 5 }, (_, index) => ({
        type: "season.completed",
        season: index + 1,
        opponents: ["Cerulean Current"],
      })),
    } as unknown as CareerRun;
    const rivalryTranscript = { ...transcript, spec: { ...transcript.spec, season: 6 } } as BattleTranscript;
    const presentation = battleTrainerPresentation("es", rivalryTranscript, rivalryRun, false);
    expect(presentation.meeting).toBe(6);
    expect(presentation.meetingLabel).toBe("RIVALIDAD · CRUCE #6");
  });

  it("handles malformed and huge timelines without counting future or invalid records", () => {
    const extremeRun = {
      ...run,
      timeline: [
        { type: "season.completed", season: "bad", opponents: ["Cerulean Current"] },
        ...Array.from({ length: 100 }, (_, index) => ({
          type: "season.completed",
          season: index + 1,
          opponents: ["Cerulean Current", "Cerulean Current"],
        })),
      ],
    } as unknown as CareerRun;
    const memory = formalRivalMemory(extremeRun, "Cerulean Current", 51);
    expect(memory.previousMeetings).toBe(100);
    expect(memory.firstSeason).toBe(1);
    expect(memory.lastSeason).toBe(50);
    expect(memory.seasonsSinceLastMeeting).toBe(1);
  });

  it("falls back to no rival history when a persisted timeline is missing or contains null entries", () => {
    const missingTimelineRun = { ...run, timeline: null } as unknown as CareerRun;
    expect(formalRivalMemory(missingTimelineRun, "Cerulean Current", 3)).toEqual({
      previousMeetings: 0,
      firstSeason: null,
      lastSeason: null,
      seasonsSinceLastMeeting: null,
    });

    const mixedTimelineRun = {
      ...run,
      timeline: [
        null,
        { type: "season.completed", season: 1, opponents: ["Cerulean Current"] },
      ],
    } as unknown as CareerRun;
    expect(formalRivalMemory(mixedTimelineRun, "Cerulean Current", 3).previousMeetings).toBe(1);
  });
});
