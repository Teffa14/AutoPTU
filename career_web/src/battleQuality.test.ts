import { describe, expect, it } from "vitest";

import { battleRenderMaxFps, chooseBattleVisualQuality } from "./battleQuality";

describe("chooseBattleVisualQuality", () => {
  it("forces light mode for reduced motion", () => {
    expect(chooseBattleVisualQuality({ storedPreference: "full", reducedMotion: true, hardwareConcurrency: 12, deviceMemory: 16 })).toBe("light");
  });

  it("respects an explicit saved preference when motion is allowed", () => {
    expect(chooseBattleVisualQuality({ storedPreference: "light", hardwareConcurrency: 12, deviceMemory: 16 })).toBe("light");
    expect(chooseBattleVisualQuality({ storedPreference: "full", hardwareConcurrency: 2, deviceMemory: 2 })).toBe("full");
  });

  it("automatically selects light mode on low-core hardware", () => {
    expect(chooseBattleVisualQuality({ hardwareConcurrency: 4, deviceMemory: 8 })).toBe("light");
  });

  it("automatically selects light mode on memory-constrained hardware", () => {
    expect(chooseBattleVisualQuality({ hardwareConcurrency: 8, deviceMemory: 4 })).toBe("light");
  });

  it("keeps full mode on capable hardware when no preference exists", () => {
    expect(chooseBattleVisualQuality({ hardwareConcurrency: 8, deviceMemory: 8 })).toBe("full");
  });
});

describe("battleRenderMaxFps", () => {
  it("cuts continuous Pixi render work in light mode without changing replay timing", () => {
    expect(battleRenderMaxFps("light")).toBe(30);
    expect(battleRenderMaxFps("full")).toBe(60);
  });
});
