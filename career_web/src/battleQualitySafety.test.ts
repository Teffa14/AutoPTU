import { describe, expect, it } from "vitest";

import { constrainRequestedBattleVisualQuality } from "./battleQuality";

describe("battle raster hard safety gate", () => {
  it("fails closed when a manual full-mode request cannot prove its raster size is safe", () => {
    const hostileSignal = {
      valueOf: () => {
        throw new Error("host raster coercion should not run");
      },
    } as unknown as number;

    expect(() => constrainRequestedBattleVisualQuality("full", {
      viewportWidth: hostileSignal,
      viewportHeight: 1080,
      devicePixelRatio: 2,
    })).not.toThrow();
    expect(constrainRequestedBattleVisualQuality("full", {
      viewportWidth: hostileSignal,
      viewportHeight: 1080,
      devicePixelRatio: 2,
    })).toBe("light");
    expect(constrainRequestedBattleVisualQuality("full", {
      viewportWidth: 0,
      viewportHeight: 2160,
      devicePixelRatio: 2,
    })).toBe("light");
    expect(constrainRequestedBattleVisualQuality("full", {
      viewportWidth: 1920,
      viewportHeight: Number.NaN,
      devicePixelRatio: 2,
    })).toBe("light");
  });
});
