import { describe, expect, it } from "vitest";

import { deriveBattleView, playbackEventIndexes } from "./battlePresentation";
import type { BattleTranscript } from "./types";

describe("battle presentation malformed legacy events", () => {
  it("skips null and primitive event entries instead of crashing the replay", () => {
    const transcript = {
      battle_id: "legacy-malformed-events",
      rounds: 1,
      sha256: "legacy",
      winner_label: "Home",
      winner_team: "career-home",
      spec: {
        home_club: "Home",
        away_club: "Away",
        home_species: "Pidgey",
        away_species: "Rattata",
        region: "kanto",
        league: "junior",
      },
      initial_state: {
        round: 1,
        battle_over: false,
        combatants: [
          { id: "career-home-1", name: "Pidgey", species: "Pidgey", team: "career-home", hp: 30, max_hp: 30 },
          { id: "career-away-1", name: "Rattata", species: "Rattata", team: "career-away", hp: 28, max_hp: 28 },
        ],
      },
      final_state: {
        round: 1,
        battle_over: true,
        winner_team: "career-home",
        combatants: [
          { id: "career-home-1", name: "Pidgey", species: "Pidgey", team: "career-home", hp: 30, max_hp: 30 },
          { id: "career-away-1", name: "Rattata", species: "Rattata", team: "career-away", hp: 20, max_hp: 28 },
        ],
      },
      events: [
        null,
        "legacy-marker",
        { type: "move", round: 1, actor: "career-home-1", target: "career-away-1", move: "Tackle", hit: true, damage: 8, target_hp: 20 },
      ],
    } as unknown as BattleTranscript;

    expect(() => playbackEventIndexes(transcript)).not.toThrow();
    expect(playbackEventIndexes(transcript)).toEqual([2]);
    expect(() => deriveBattleView(transcript, 2)).not.toThrow();
    expect(deriveBattleView(transcript, 2).combatants.find((entry) => entry.id === "career-away-1")?.hp).toBe(20);
  });

  it("survives missing legacy event and combatant arrays", () => {
    const transcript = {
      battle_id: "legacy-malformed-state-arrays",
      rounds: 0,
      sha256: "legacy",
      winner_label: "",
      winner_team: null,
      spec: {
        home_club: "Home",
        away_club: "Away",
        home_species: "Pidgey",
        away_species: "Rattata",
        region: "kanto",
        league: "junior",
      },
      initial_state: { round: 0, battle_over: false, combatants: null },
      final_state: { round: 0, battle_over: false, combatants: "legacy" },
      events: null,
    } as unknown as BattleTranscript;

    expect(() => playbackEventIndexes(transcript)).not.toThrow();
    expect(playbackEventIndexes(transcript)).toEqual([]);
    expect(() => deriveBattleView(transcript, 0)).not.toThrow();
    expect(deriveBattleView(transcript, 0).combatants).toEqual([]);
    expect(deriveBattleView(transcript, 0).complete).toBe(true);
  });
});
