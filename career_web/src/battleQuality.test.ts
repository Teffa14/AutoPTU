import { afterEach, describe, expect, it, vi } from "vitest";

import { battleOutcomeVisualState, battleRenderFrameFactors, battleRenderMaxFps, chooseBattleVisualQuality, detectBattleVisualQuality } from "./battleQuality";

afterEach(() => {
  vi.unstubAllGlobals();
});

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

  it("automatically selects light mode on compact touch devices", () => {
    expect(chooseBattleVisualQuality({ compactTouch: true, hardwareConcurrency: 8, deviceMemory: 8 })).toBe("light");
  });

  it("keeps an explicit full preference on compact touch devices", () => {
    expect(chooseBattleVisualQuality({ storedPreference: "full", compactTouch: true, hardwareConcurrency: 8, deviceMemory: 8 })).toBe("full");
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

  it("fails closed for malformed host hardware signals without invoking coercion", () => {
    const hostileSignal = {
      valueOf: () => {
        throw new Error("host coercion should not run");
      },
    } as unknown as number;

    expect(() => chooseBattleVisualQuality({ hardwareConcurrency: hostileSignal, deviceMemory: 8 })).not.toThrow();
    expect(chooseBattleVisualQuality({ hardwareConcurrency: true as unknown as number, deviceMemory: 8 })).toBe("full");
    expect(chooseBattleVisualQuality({ hardwareConcurrency: 8, deviceMemory: hostileSignal })).toBe("full");
  });
});

describe("battle quality host resilience", () => {
  it("does not crash battle startup when matchMedia throws in a restricted browser", () => {
    vi.stubGlobal("window", {
      localStorage: { getItem: () => null, setItem: () => undefined },
      navigator: { hardwareConcurrency: 8, deviceMemory: 8, maxTouchPoints: 0, connection: {} },
      matchMedia: () => { throw new Error("media queries blocked"); },
      innerWidth: 1280,
      innerHeight: 720,
    });

    expect(() => detectBattleVisualQuality()).not.toThrow();
    expect(detectBattleVisualQuality()).toBe("full");
  });

  it("does not coerce malformed compact-touch host signals during battle startup", () => {
    const hostileSignal = {
      valueOf: () => {
        throw new Error("compact-touch host coercion should not run");
      },
    };
    vi.stubGlobal("window", {
      localStorage: { getItem: () => null, setItem: () => undefined },
      navigator: { hardwareConcurrency: 8, deviceMemory: 8, maxTouchPoints: hostileSignal, connection: {} },
      matchMedia: () => ({ matches: false }),
      innerWidth: hostileSignal,
      innerHeight: 720,
    });

    expect(() => detectBattleVisualQuality()).not.toThrow();
    expect(detectBattleVisualQuality()).toBe("full");
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

describe("battle outcome feedback", () => {
  it("keeps decisive winner and loser readability available to light mode", () => {
    expect(battleOutcomeVisualState("career-home", "career-home")).toEqual({ alpha: 1, scale: 1.08 });
    expect(battleOutcomeVisualState("career-away", "career-home")).toEqual({ alpha: 0.38, scale: 0.86 });
  });

  it("fails closed when a transcript has no winner team", () => {
    expect(battleOutcomeVisualState("career-home", "")).toEqual({ alpha: 1, scale: 1 });
  });

  it("keeps both teams neutral when a legacy transcript has an unknown winner token", () => {
    expect(battleOutcomeVisualState("career-home", "undefined")).toEqual({ alpha: 1, scale: 1 });
    expect(battleOutcomeVisualState("career-away", "undefined")).toEqual({ alpha: 1, scale: 1 });
  });
});
