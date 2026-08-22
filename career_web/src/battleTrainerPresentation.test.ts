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
} as unknown as CareerRun;

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
    expect(formalRivalMemory(run, "Cerulean Current", 3)).toEqual({
      previousMeetings: 2,
      firstSeason: 1,
      lastSeason: 1,
      seasonsSinceLastMeeting: 2,
    });
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
    expect(presentation.away.line).toContain("Pasó tiempo");
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
    expect(presentation.away.line).toContain("Ya tenemos historia");
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
});
