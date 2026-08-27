import { afterEach, describe, expect, it, vi } from "vitest";

import { BATTLE_FULL_RENDER_PIXEL_BUDGET, battleEstimatedRenderPixels, battleOutcomeVisualState, battleRenderFrameFactors, battleRenderMaxFps, chooseBattleVisualQuality, constrainRequestedBattleVisualQuality, detectBattleVisualQuality } from "./battleQuality";

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

  it("automatically selects light mode when full-resolution raster work exceeds the browser budget", () => {
    expect(chooseBattleVisualQuality({
      hardwareConcurrency: 12,
      deviceMemory: 16,
      viewportWidth: 2560,
      viewportHeight: 1440,
      devicePixelRatio: 2,
    })).toBe("light");
  });

  it("keeps full mode for a common high-density 1080p viewport", () => {
    expect(chooseBattleVisualQuality({
      hardwareConcurrency: 12,
      deviceMemory: 16,
      viewportWidth: 1920,
      viewportHeight: 1080,
      devicePixelRatio: 2,
    })).toBe("full");
  });

  it("forces light mode above the raster safety budget even when full was saved", () => {
    expect(chooseBattleVisualQuality({
      storedPreference: "full",
      hardwareConcurrency: 12,
      deviceMemory: 16,
      viewportWidth: 3840,
      viewportHeight: 2160,
      devicePixelRatio: 2,
    })).toBe("light");
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

describe("manual battle quality requests", () => {
  it("rejects a manual full-mode request when the current viewport exceeds the raster safety budget", () => {
    expect(constrainRequestedBattleVisualQuality("full", {
      viewportWidth: 3840,
      viewportHeight: 2160,
      devicePixelRatio: 2,
    })).toBe("light");
  });

  it("keeps manual full mode available below the hard safety limit", () => {
    expect(constrainRequestedBattleVisualQuality("full", {
      viewportWidth: 1920,
      viewportHeight: 1080,
      devicePixelRatio: 2,
    })).toBe("full");
  });
});

describe("battle raster budget", () => {
  it("matches the capped Pixi resolution used by full mode", () => {
    expect(battleEstimatedRenderPixels({ viewportWidth: 1920, viewportHeight: 1080, devicePixelRatio: 3 })).toBe(8_294_400);
    expect(battleEstimatedRenderPixels({ viewportWidth: 2560, viewportHeight: 1440, devicePixelRatio: 2 })).toBe(14_745_600);
    expect(battleEstimatedRenderPixels({ viewportWidth: 3840, viewportHeight: 2160, devicePixelRatio: 2 })).toBe(33_177_600);
    expect(BATTLE_FULL_RENDER_PIXEL_BUDGET).toBe(12_000_000);
  });

  it("ignores malformed raster signals instead of coercing host objects", () => {
    const hostileSignal = {
      valueOf: () => {
        throw new Error("raster host coercion should not run");
      },
    } as unknown as number;
    expect(() => battleEstimatedRenderPixels({ viewportWidth: hostileSignal, viewportHeight: 720, devicePixelRatio: 2 })).not.toThrow();
    expect(battleEstimatedRenderPixels({ viewportWidth: hostileSignal, viewportHeight: 720, devicePixelRatio: 2 })).toBeNull();
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
      devicePixelRatio: 1,
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
      devicePixelRatio: 1,
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
