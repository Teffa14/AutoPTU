import { describe, expect, it } from "vitest";

import { opponentAbilityIsRevealed, opponentKnowledgeAtEvent, opponentMoveIsRevealed } from "./opponentKnowledge";
import type { BattleTranscript } from "./types";

function transcript(): BattleTranscript {
  return {
    battle_id: "knowledge-test",
    rounds: 2,
    sha256: "abc123",
    spec: {
      home_club: "Home",
      away_club: "Away",
      home_species: "Pikachu",
      away_species: "Charmander",
      region: "kanto",
      league: "regular",
    },
    initial_state: {
      round: 1,
      battle_over: false,
      combatants: [
        { id: "home-a", name: "Pikachu", species: "Pikachu", team: "career-home", hp: 40, max_hp: 40, active: true, moves: [{ name: "Thunderbolt", type: "Electric", category: "Special" }] },
        { id: "away-a", name: "Charmander", species: "Charmander", team: "career-away", hp: 40, max_hp: 40, active: true, abilities: ["Blaze"], moves: [{ name: "Ember", type: "Fire", category: "Special" }, { name: "Scratch", type: "Normal", category: "Physical" }] },
        { id: "away-b", name: "Ekans", species: "Ekans", team: "career-away", hp: 44, max_hp: 44, active: false, abilities: ["Intimidate"], moves: [{ name: "Bite", type: "Dark", category: "Physical" }] },
      ],
    },
    final_state: { round: 2, battle_over: true, combatants: [] },
    events: [
      { type: "round_start", round: 1 },
      { type: "move", round: 1, actor: "away-a", target: "home-a", move: "Ember" },
      { type: "switch", round: 2, outgoing: "away-a", target: "away-b" },
      { type: "ability", round: 2, actor: "away-b", ability: "Intimidate" },
    ],
  };
}

describe("opponent knowledge boundary", () => {
  it("starts with only the opponent Pokémon already visible on the field", () => {
    const knowledge = opponentKnowledgeAtEvent(transcript(), 0);
    expect([...knowledge.seenCombatantIds]).toEqual(["away-a"]);
    expect(opponentMoveIsRevealed(knowledge, "away-a", "Ember")).toBe(false);
    expect(opponentAbilityIsRevealed(knowledge, "away-a", "Blaze")).toBe(false);
  });

  it("reveals a move only when its authoritative move event is reached", () => {
    const knowledge = opponentKnowledgeAtEvent(transcript(), 1);
    expect(opponentMoveIsRevealed(knowledge, "away-a", "Ember")).toBe(true);
    expect(opponentMoveIsRevealed(knowledge, "away-a", "Scratch")).toBe(false);
  });

  it("reveals a bench Pokémon on switch without leaking its build", () => {
    const knowledge = opponentKnowledgeAtEvent(transcript(), 2);
    expect(knowledge.seenCombatantIds.has("away-b")).toBe(true);
    expect(opponentMoveIsRevealed(knowledge, "away-b", "Bite")).toBe(false);
    expect(opponentAbilityIsRevealed(knowledge, "away-b", "Intimidate")).toBe(false);
  });

  it("reveals an ability only after an authoritative ability event", () => {
    const knowledge = opponentKnowledgeAtEvent(transcript(), 3);
    expect(opponentAbilityIsRevealed(knowledge, "away-b", "Intimidate")).toBe(true);
  });

  it("fails closed for malformed indexes and unrelated actor ids", () => {
    const battle = transcript();
    battle.events.unshift({ type: "move", actor: "ghost", move: "Private Move" });
    const knowledge = opponentKnowledgeAtEvent(battle, Number.NaN);
    expect([...knowledge.seenCombatantIds]).toEqual(["away-a"]);
    expect(opponentMoveIsRevealed(knowledge, "ghost", "Private Move")).toBe(false);
  });

  it("fails closed when legacy transcript collections are malformed", () => {
    const battle = transcript();
    (battle.initial_state as unknown as { combatants: unknown }).combatants = null;
    (battle as unknown as { events: unknown }).events = null;

    expect(() => opponentKnowledgeAtEvent(battle, 5)).not.toThrow();
    const knowledge = opponentKnowledgeAtEvent(battle, 5);
    expect([...knowledge.seenCombatantIds]).toEqual([]);
    expect([...knowledge.revealedMoves]).toEqual([]);
    expect([...knowledge.revealedAbilities]).toEqual([]);
  });
});
