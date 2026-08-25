import { describe, expect, it } from "vitest";

import { clubTransitionQuestionText, latestClubTransition } from "./clubTransitionPresentation";
import type { CareerRun } from "./types";

function runWithTimeline(timeline: Record<string, unknown>[], seasonNumber = 3): CareerRun {
  return {
    id: "run-1",
    mode: "advanced",
    locale: "es",
    age: 18,
    league: "regular",
    season_number: seasonNumber,
    health: 100,
    score: 0,
    reputation: 8,
    development: 0,
    scouting: 0,
    finances: 0,
    career_earnings: 0,
    money: 0,
    pokedex_level: 0,
    license_status: "active",
    seasons_without_contract: 0,
    relationships: {},
    relationship_effects: {},
    inventory: {},
    status: "active",
    revision: 1,
    build: { name: "Tefa", region: "kanto", starter: "Bulbasaur", classes: ["Ace Trainer"], pokeballs: 5 },
    contract: { club_name: "Celadon Comets", region: "kanto", league: "regular", salary: 420, loan_slots: 2, seasons_remaining: 1 },
    roster: [],
    pokemon: [],
    active_roster: [],
    totals: { wins: 0, losses: 0, draws: 0, titles: 0 },
    achievements: [],
    class_effects: { adapters: [], battle: {}, season: {} },
    timeline,
    season: {
      number: seasonNumber,
      age: 18,
      league: "regular",
      club_name: "Celadon Comets",
      status: "decision",
      battle_ids: [],
      decisions_required: 3,
      decisions_completed: 0,
      decision_history: [],
      training_completed: false,
      training_method: "",
      training_completed_ids: [],
    },
  };
}

describe("latestClubTransition", () => {
  it("builds a factual transfer brief from authoritative timeline events", () => {
    const run = runWithTimeline([
      { type: "club.offer_signed", season: 1, club: "Pewter Onix", salary: 180, seasons: 1 },
      { type: "season.completed", season: 2, record: "2-4-0" },
      {
        type: "club.loans_returned",
        season: 3,
        club: "Pewter Onix",
        pokemon: [
          { id: "loan-1", species: "Machoke", active: true },
          { id: "loan-2", species: "Graveler", active: false },
        ],
      },
      {
        type: "club.offer_signed",
        season: 3,
        club: "Celadon Comets",
        salary: 420,
        seasons: 1,
        renewal: false,
        loan_species: ["Ivysaur", "Kadabra"],
        gift_species: "Scyther",
        perk: { label: "Regional scouting network" },
      },
    ]);

    const brief = latestClubTransition(run);
    expect(brief).toEqual({
      season: 3,
      previousClub: "Pewter Onix",
      newClub: "Celadon Comets",
      renewal: false,
      salary: 420,
      seasons: 1,
      returnedLoans: ["Machoke", "Graveler"],
      incomingLoans: ["Ivysaur", "Kadabra"],
      giftSpecies: "Scyther",
      perkLabel: "Regional scouting network",
      record: "2-4-0",
      questions: ["rebuild", "recovery", "contract"],
    });
    expect(clubTransitionQuestionText(brief!.questions[0], brief!, "es")).toContain("2 Pokémon cedidos");
  });

  it("aggregates every authoritative loan-return event before a transfer", () => {
    const run = runWithTimeline([
      { type: "club.offer_signed", season: 1, club: "Pewter Onix", salary: 180, seasons: 1 },
      { type: "season.completed", season: 2, record: "3-3-0" },
      {
        type: "club.loans_returned",
        season: 3,
        club: "Pewter Onix",
        pokemon: [{ id: "loan-1", species: "Machoke", active: true }],
      },
      {
        type: "club.loans_returned",
        season: 3,
        club: "Pewter Onix",
        pokemon: [{ id: "loan-2", species: "Graveler", active: false }],
      },
      {
        type: "club.offer_signed",
        season: 3,
        club: "Celadon Comets",
        salary: 420,
        seasons: 1,
        renewal: false,
      },
    ]);

    const brief = latestClubTransition(run);
    expect(brief?.returnedLoans).toEqual(["Machoke", "Graveler"]);
    expect(brief?.questions[0]).toBe("rebuild");
  });

  it("treats a renewal as continuity and never invents loan returns", () => {
    const run = runWithTimeline([
      { type: "season.completed", season: 2, record: "5-1-0" },
      {
        type: "club.offer_signed",
        season: 3,
        club: "Celadon Comets",
        salary: 460,
        seasons: 2,
        renewal: true,
        loan_species: ["Kadabra"],
        returned_loan_ids: ["corrupt-should-not-surface"],
        perk: { label: "Medical staff" },
      },
    ]);

    const brief = latestClubTransition(run);
    expect(brief?.previousClub).toBe("Celadon Comets");
    expect(brief?.returnedLoans).toEqual([]);
    expect(brief?.questions).toEqual(["momentum", "continuity", "contract"]);
  });

  it("returns null when no current-season signing exists", () => {
    expect(latestClubTransition(runWithTimeline([{ type: "club.offer_signed", season: 2, club: "Old Club" }]))).toBeNull();
  });
});
