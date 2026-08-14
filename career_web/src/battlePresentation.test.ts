import { describe, expect, it } from "vitest";

import { battleCommentary, deriveBattleView, playbackEventIndexes } from "./battlePresentation";
import type { BattleTranscript } from "./types";

const transcript: BattleTranscript = {
  battle_id: "battle-1", rounds: 1, sha256: "abc", winner_label: "Home", winner_team: "career-home",
  spec: { home_club: "Home", away_club: "Away", home_species: "Spearow", away_species: "Paras", region: "kanto", league: "junior" },
  initial_state: { round: 1, battle_over: false, combatants: [
    { id: "career-home-1", name: "Spearow", species: "Spearow", team: "career-home", hp: 39, max_hp: 39, types: ["Normal", "Flying"], stats: { atk: 10 }, abilities: ["Keen Eye"] },
    { id: "career-away-1", name: "Paras", species: "Paras", team: "career-away", hp: 42, max_hp: 42, types: ["Bug", "Grass"], stats: { def: 5 }, abilities: ["Effect Spore"] },
  ] },
  final_state: { round: 1, battle_over: true, winner_team: "career-home", combatants: [
    { id: "career-home-1", name: "Spearow", species: "Spearow", team: "career-home", hp: 39, max_hp: 39 },
    { id: "career-away-1", name: "Paras", species: "Paras", team: "career-away", hp: 18, max_hp: 42 },
  ] },
  events: [
    { type: "round_start", round: 1 },
    { type: "phase", round: 1 },
    { type: "move", round: 1, actor: "career-home-1", target: "career-away-1", move: "U-Turn", hit: true, damage: 24, target_hp: 18, type_multiplier: 2, attack_value: 10, defense_value: 5, effective_db: 7, context: { roll_options: ["stab"] } },
  ],
};

describe("battle presentation", () => {
  it("filters engine plumbing and applies deterministic HP changes", () => {
    expect(playbackEventIndexes(transcript)).toEqual([0, 2]);
    expect(deriveBattleView(transcript, 2).combatants.find((entry) => entry.id === "career-away-1")?.hp).toBe(18);
  });

  it("turns a mechanical event into readable Spanish commentary", () => {
    const view = deriveBattleView(transcript, 2);
    expect(battleCommentary("es", transcript, view)).toBe("Spearow usa U-Turn. Paras pierde 24 PS. Es muy eficaz.");
    expect(view.effectiveness).toBe(2);
    expect(view.stab).toBe(true);
    expect(view.attackValue).toBe(10);
    expect(view.defenseValue).toBe(5);
    expect(view.effectiveDb).toBe(7);
  });

  it("presents positioning and forced movement instead of hiding it", () => {
    const tactical: BattleTranscript = {
      ...transcript,
      events: [
        { type: "shift", round: 1, actor: "career-home-1", to: [4, 4] },
        { type: "forced_movement", round: 1, actor: "career-home-1", target: "career-away-1", to: [8, 4] },
      ],
    };
    expect(playbackEventIndexes(tactical)).toEqual([0, 1]);
    expect(deriveBattleView(tactical, 1).combatants.find((entry) => entry.id === "career-away-1")?.position).toEqual([8, 4]);
  });
});
