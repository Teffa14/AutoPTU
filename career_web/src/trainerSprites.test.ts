import { describe, expect, it } from "vitest";

import { DEFAULT_TRAINER_SPRITE, trainerSpriteForRun } from "./trainerSprites";
import type { CareerRun } from "./types";

describe("trainer sprite persistence", () => {
  it("falls back safely when a legacy save has no usable timeline", () => {
    const run = { timeline: null } as unknown as CareerRun;
    expect(trainerSpriteForRun(run)).toBe(DEFAULT_TRAINER_SPRITE);
  });

  it("ignores malformed timeline entries and preserves the latest valid appearance", () => {
    const run = {
      timeline: [
        null,
        { type: "trainer.appearance_selected", trainer_sprite: "hilda" },
        { type: "trainer.appearance_selected", trainer_sprite: "" },
      ],
    } as unknown as CareerRun;
    expect(trainerSpriteForRun(run)).toBe("hilda");
  });
});
