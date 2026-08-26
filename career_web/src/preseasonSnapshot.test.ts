import { describe, expect, it } from "vitest";
import { normalizePreseasonSnapshot } from "./preseasonSnapshot";

describe("preseason snapshot boundary", () => {
  const valid = {
    season: 3,
    club_completed: true,
    sponsor_completed: false,
    capture_completed: false,
    club_offers: [],
    sponsor_offers: [],
    capture_candidates: [],
  };

  it("accepts a render-safe preseason snapshot", () => {
    expect(normalizePreseasonSnapshot(valid)).toEqual(valid);
  });

  it.each([
    ["club_offers", null],
    ["sponsor_offers", "broken"],
    ["capture_candidates", {}],
  ])("rejects malformed %s before React can call map", (field, value) => {
    expect(() => normalizePreseasonSnapshot({ ...valid, [field]: value })).toThrow("Invalid preseason response");
  });

  it("rejects malformed nested club collections before render", () => {
    const offer = {
      id: "club-1",
      club_id: "club-1",
      club_name: "Ouros FC",
      salary: 1000,
      seasons: 2,
      loan_slots: 2,
      loan_species: ["Pikachu"],
      renewal: false,
      perk: { stat: "development", amount: 1, label: "Development" },
    };
    expect(() => normalizePreseasonSnapshot({ ...valid, club_offers: [{ ...offer, loan_species: "broken" }] })).toThrow("Invalid preseason response");
    expect(() => normalizePreseasonSnapshot({ ...valid, club_offers: [{ ...offer, returning_loans: "broken" }] })).toThrow("Invalid preseason response");
  });

  it("rejects sponsor and capture records that would crash presentation", () => {
    expect(() => normalizePreseasonSnapshot({ ...valid, sponsor_offers: [{ id: "s1", name: "Sponsor", theme: null }] })).toThrow("Invalid preseason response");
    expect(() => normalizePreseasonSnapshot({ ...valid, capture_candidates: [{ id: "c1", species: "Eevee", rarity: "rare", ball_cost: "one" }] })).toThrow("Invalid preseason response");
  });

  it("rejects non-object and partial payloads", () => {
    expect(() => normalizePreseasonSnapshot(null)).toThrow("Invalid preseason response");
    expect(() => normalizePreseasonSnapshot({ season: 3 })).toThrow("Invalid preseason response");
  });
});
