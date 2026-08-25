import { describe, expect, it } from "vitest";
import { automaticTrainingCandidates, canUseTrainingPlan } from "./trainingPlan";
import type { CareerPokemon, CareerRun } from "./types";

function pokemon(id: string, options: Partial<CareerPokemon> = {}): CareerPokemon {
  return {
    id,
    species: id,
    caught_species: id,
    level: 10,
    acquired_season: 1,
    acquired_age: 12,
    capture_region: "kanto",
    is_partner: false,
    status: "active",
    matches: 0,
    wins: 0,
    taught_moves: [],
    nature: "Hardy",
    abilities: [],
    stat_training: {},
    evolution_history: [],
    gimmicks: [],
    career_health: 100,
    training_wear: 0,
    retired_season: 0,
    retired_reason: "",
    ...options,
  };
}

function run(mode: "simple" | "advanced", pokemonList: CareerPokemon[], activeRoster: string[], completed: string[] = []): CareerRun {
  return {
    id: "run-1",
    mode,
    pokemon: pokemonList,
    active_roster: activeRoster,
    season: { training_completed_ids: completed },
  } as unknown as CareerRun;
}

describe("automatic training candidates", () => {
  it("uses the active partner in simple mode", () => {
    const partner = pokemon("partner", { is_partner: true });
    const reserve = pokemon("reserve");
    expect(automaticTrainingCandidates(run("simple", [partner, reserve], [partner.id, reserve.id]), "conditioning"))
      .toEqual([partner.id]);
  });

  it("falls back to the first active Pokemon when the original partner is retired", () => {
    const retiredPartner = pokemon("partner", { is_partner: true, status: "retired", career_health: 0 });
    const replacement = pokemon("replacement");
    const source = run("simple", [retiredPartner, replacement], [replacement.id]);
    expect(automaticTrainingCandidates(source, "power")).toEqual([replacement.id]);
  });

  it("trains every eligible active Pokemon in advanced mode", () => {
    const first = pokemon("first", { is_partner: true });
    const second = pokemon("second");
    expect(automaticTrainingCandidates(run("advanced", [first, second], [first.id, second.id]), "guard"))
      .toEqual([first.id, second.id]);
  });

  it("skips already completed and saturated Pokemon", () => {
    const completed = pokemon("completed", { is_partner: true });
    const saturated = pokemon("saturated", { stat_training: { spd: 12 } });
    const available = pokemon("available", { stat_training: { spd: 10 } });
    const source = run("advanced", [completed, saturated, available], [completed.id, saturated.id, available.id], [completed.id]);
    expect(automaticTrainingCandidates(source, "agility")).toEqual([available.id]);
  });

  it("allows mixed-stat plans while at least one target stat still has room", () => {
    expect(canUseTrainingPlan(pokemon("mixed", { stat_training: { atk: 12, spatk: 11 } }), "power")).toBe(true);
    expect(canUseTrainingPlan(pokemon("full", { stat_training: { atk: 12, spatk: 12 } }), "power")).toBe(false);
  });

  it("treats a malformed legacy active roster as empty instead of crashing season training", () => {
    const source = run("advanced", [pokemon("available")], ["available"]);
    (source as unknown as { active_roster: unknown }).active_roster = null;
    expect(automaticTrainingCandidates(source, "conditioning")).toEqual([]);
  });

  it("ignores null legacy Pokemon entries while preserving valid active candidates", () => {
    const available = pokemon("available");
    const source = run("advanced", [available], [available.id]);
    (source as unknown as { pokemon: unknown }).pokemon = [null, available];
    expect(automaticTrainingCandidates(source, "guard")).toEqual([available.id]);
  });
});
