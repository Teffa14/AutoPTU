import { describe, expect, it } from "vitest";

import { chooseBattleVisualQuality } from "./battleQuality";

describe("battle quality save-data regression", () => {
  it("selects light mode automatically when the browser asks to save data", () => {
    expect(chooseBattleVisualQuality({
      saveData: true,
      hardwareConcurrency: 8,
      deviceMemory: 8,
    })).toBe("light");
  });

  it("still respects an explicit full preference when motion is allowed", () => {
    expect(chooseBattleVisualQuality({
      storedPreference: "full",
      saveData: true,
      hardwareConcurrency: 8,
      deviceMemory: 8,
    })).toBe("full");
  });
});
