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

  it("rejects non-object and partial payloads", () => {
    expect(() => normalizePreseasonSnapshot(null)).toThrow("Invalid preseason response");
    expect(() => normalizePreseasonSnapshot({ season: 3 })).toThrow("Invalid preseason response");
  });
});
