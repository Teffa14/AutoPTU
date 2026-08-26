import { describe, expect, it } from "vitest";

import { sponsorObjectiveLabel, sponsorSeasonReview, sponsorStatusLabel } from "./sponsorReviewPresentation";
import type { CareerRun } from "./types";

function runWithTimeline(timeline: Record<string, unknown>[]): CareerRun {
  return {
    id: "run-1",
    mode: "advanced",
    locale: "es",
    age: 18,
    league: "regular",
    season_number: 4,
    health: 100,
    score: 0,
    reputation: 5,
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
  };
}

describe("sponsorSeasonReview", () => {
  it("keeps guaranteed payment separate from a completed conditional bonus", () => {
    const review = sponsorSeasonReview(runWithTimeline([
      { type: "sponsor.signed", season: 3, name: "Rotom Broadcast", objective: "wins", target: 4, upfront: 120, bonus: 210 },
      { type: "sponsor.completed", season: 3, name: "Rotom Broadcast", wins: 5, target: 4, bonus: 210 },
      { type: "season.completed", season: 3, record: "5-1-0" },
    ]), 3);

    expect(review).toEqual({
      season: 3,
      status: "completed",
      name: "Rotom Broadcast",
      objective: "wins",
      target: 4,
      actual: 5,
      upfront: 120,
      bonusPaid: 210,
    });
    expect(sponsorObjectiveLabel(review!, "es")).toBe("5/4 victorias");
    expect(sponsorStatusLabel(review!, "en")).toBe("Objective completed");
  });

  it("shows a missed objective without retroactively removing guaranteed payment", () => {
    const review = sponsorSeasonReview(runWithTimeline([
      { type: "sponsor.signed", season: 2, name: "Evergreen Care", objective: "wins", target: 4, upfront: 100, bonus: 180 },
      { type: "sponsor.failed", season: 2, name: "Evergreen Care", wins: 2, target: 4, bonus: 0 },
      { type: "season.completed", season: 2, record: "2-4-0" },
    ]), 2);

    expect(review?.status).toBe("failed");
    expect(review?.upfront).toBe(100);
    expect(review?.bonusPaid).toBe(0);
    expect(sponsorStatusLabel(review!, "es")).toBe("Objetivo no cumplido");
  });

  it("preserves an explicit sponsor-free season", () => {
    const review = sponsorSeasonReview(runWithTimeline([
      { type: "sponsor.declined", season: 4 },
      { type: "season.completed", season: 4, record: "3-3-0" },
    ]), 4);

    expect(review?.status).toBe("declined");
    expect(sponsorObjectiveLabel(review!, "en")).toBe("Sponsor-free season");
    expect(review?.upfront).toBe(0);
    expect(review?.bonusPaid).toBe(0);
  });

  it("rejects malformed sponsor outcome numbers instead of surfacing NaN or Infinity", () => {
    const review = sponsorSeasonReview(runWithTimeline([
      { type: "sponsor.signed", season: 3, name: "  Porygon Systems  ", objective: "wins", target: "4", upfront: "NaN" },
      { type: "sponsor.completed", season: 3, wins: "Infinity", target: -2, bonus: "bad" },
      { type: "season.completed", season: 3 },
    ]), 3);

    expect(review).toMatchObject({ name: "Porygon Systems", target: 0, actual: 0, upfront: 0, bonusPaid: 0 });
    expect(JSON.stringify(review)).not.toMatch(/NaN|Infinity/);
  });

  it("returns null when a sponsor was signed but no authoritative outcome exists", () => {
    expect(sponsorSeasonReview(runWithTimeline([
      { type: "sponsor.signed", season: 3, name: "Northstar Labs", target: 4, upfront: 100 },
      { type: "season.completed", season: 3 },
    ]), 3)).toBeNull();
  });

  it("survives malformed legacy timeline containers and entries", () => {
    const missingTimeline = runWithTimeline([]);
    (missingTimeline as unknown as { timeline: unknown }).timeline = null;
    expect(sponsorSeasonReview(missingTimeline, 3)).toBeNull();

    const mixedTimeline = runWithTimeline([]);
    (mixedTimeline as unknown as { timeline: unknown }).timeline = [
      null,
      "legacy-junk",
      { type: "sponsor.signed", season: 3, name: "Rotom Broadcast", objective: "wins", target: 4, upfront: 120 },
      { type: "sponsor.completed", season: 3, name: "Rotom Broadcast", wins: 5, target: 4, bonus: 210 },
    ];

    expect(sponsorSeasonReview(mixedTimeline, 3)).toMatchObject({
      status: "completed",
      name: "Rotom Broadcast",
      actual: 5,
      target: 4,
    });
  });
});
