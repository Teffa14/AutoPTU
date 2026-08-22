import { describe, expect, it } from "vitest";

import { battleRenderFrameFactors, battleRenderMaxFps, chooseBattleVisualQuality } from "./battleQuality";

describe("chooseBattleVisualQuality", () => {
  it("forces light mode for reduced motion", () => {
    expect(chooseBattleVisualQuality({ storedPreference: "full", reducedMotion: true, hardwareConcurrency: 12, deviceMemory: 16 })).toBe("light");
  });

  it("respects an explicit saved preference when motion is allowed", () => {
    expect(chooseBattleVisualQuality({ storedPreference: "light", hardwareConcurrency: 12, deviceMemory: 16 })).toBe("light");
    expect(chooseBattleVisualQuality({ storedPreference: "full", hardwareConcurrency: 2, deviceMemory: 2 })).toBe("full");
  });

  it("automatically selects light mode when the browser asks to save data", () => {
    expect(chooseBattleVisualQuality({ saveData: true, hardwareConcurrency: 8, deviceMemory: 8 })).toBe("light");
  });

  it("keeps an explicit full preference even when save-data is enabled", () => {
    expect(chooseBattleVisualQuality({ storedPreference: "full", saveData: true, hardwareConcurrency: 8, deviceMemory: 8 })).toBe("full");
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

describe("battle render budget", () => {
  it("cuts continuous Pixi render work in light mode without changing replay timing", () => {
    expect(battleRenderMaxFps("light")).toBe(30);
    expect(battleRenderMaxFps("full")).toBe(60);
  });

  it("keeps position smoothing and impulse decay stable across lower frame rates", () => {
    const oneFrame = battleRenderFrameFactors(1);
    expect(oneFrame.positionBlend).toBeCloseTo(0.2, 10);
    expect(oneFrame.impulseDecay).toBeCloseTo(0.78, 10);
    const twoFrames = battleRenderFrameFactors(2);
    expect(twoFrames.positionBlend).toBeCloseTo(0.36, 10);
    expect(twoFrames.impulseDecay).toBeCloseTo(0.6084, 10);
  });
});
