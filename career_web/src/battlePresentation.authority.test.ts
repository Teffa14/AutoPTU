import { describe, expect, it } from "vitest";

import { battleCommentary, deriveBattleView, eventTitle, playbackEventIndexes } from "./battlePresentation";
import type { BattleTranscript } from "./types";

const baseTranscript: BattleTranscript = {
  battle_id: "battle-authority",
  rounds: 1,
  sha256: "authority",
  winner_label: "Home",
  winner_team: "career-home",
  spec: {
    home_club: "Home",
    away_club: "Away",
    home_species: "Spearow",
    away_species: "Paras",
    region: "kanto",
    league: "junior",
  },
  initial_state: {
    round: 1,
    battle_over: false,
    combatants: [
      { id: "career-home-1", name: "Spearow", species: "Spearow", team: "career-home", hp: 39, max_hp: 39 },
      { id: "career-away-1", name: "Paras", species: "Paras", team: "career-away", hp: 42, max_hp: 42 },
    ],
  },
  final_state: {
    round: 1,
    battle_over: true,
    winner_team: "career-home",
    combatants: [],
  },
  events: [],
};

describe("battle presentation label authority", () => {
  it("does not coerce malformed event labels into visible battle facts", () => {
    const malformed = {
      ...baseTranscript,
      events: [
        {
          type: "move",
          round: 1,
          actor: "career-home-1",
          target: "career-away-1",
          move: { toString: () => "Invented Move" },
          hit: true,
          damage: 0,
          target_hp: 42,
        },
      ],
    } as unknown as BattleTranscript;

    const view = deriveBattleView(malformed, 0);

    expect(view.move).toBe("");
    expect(eventTitle("en", view)).toBe("ATTACK");
    expect(battleCommentary("en", malformed, view)).toBe("Spearow uses a move.");
  });

  it("ignores malformed event types instead of coercing them into presented events", () => {
    const malformed = {
      ...baseTranscript,
      events: [{ type: { toString: () => "move" }, round: 1 }],
    } as unknown as BattleTranscript;

    expect(playbackEventIndexes(malformed)).toEqual([]);
  });
});
