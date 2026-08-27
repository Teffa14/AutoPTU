import { describe, expect, it } from "vitest";

import { DEFAULT_TRAINER_SPRITE, trainerSpriteForRun, trainerSpriteOptions, trainerSpriteStorageEntry, withTrainerSpriteSelection } from "./trainerSprites";
import type { CareerRun } from "./types";

describe("trainer sprite persistence", () => {
  it("exposes a broad Showdown archive without depending on the compact API catalog", () => {
    const options = trainerSpriteOptions(null);
    expect(options.length).toBeGreaterThan(400);
    expect(options.some((entry) => entry.id === "aaron")).toBe(true);
    expect(options.some((entry) => entry.id === "juliana-s")).toBe(true);
    expect(options.some((entry) => entry.id === "victor")).toBe(true);
  });

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

  it("repairs a creation response that lost the selected appearance before it reaches the run", () => {
    const run = {
      build: { name: "QA Trainer" },
      season_number: 1,
      age: 12,
      timeline: [{ type: "trainer.appearance_selected", trainer_sprite: "red" }],
    } as unknown as CareerRun;
    const repaired = withTrainerSpriteSelection(run, "hilda");
    expect(trainerSpriteForRun(repaired)).toBe("hilda");
    expect(repaired.timeline.filter((entry) => entry.type === "trainer.appearance_selected")).toEqual([
      expect.objectContaining({ trainer_sprite: "hilda" }),
    ]);
  });

  it("does not create a persistence key when legacy trainer identity metadata is missing", () => {
    expect(trainerSpriteStorageEntry({ timeline: [] } as unknown as CareerRun)).toBeNull();
    expect(trainerSpriteStorageEntry({ build: { name: "   " }, timeline: [] } as unknown as CareerRun)).toBeNull();
  });

  it("normalizes a valid trainer identity and preserves the selected sprite", () => {
    const run = {
      build: { name: "  QA Trainer  " },
      timeline: [{ type: "trainer.appearance_selected", trainer_sprite: " hilda " }],
    } as unknown as CareerRun;
    expect(trainerSpriteStorageEntry(run)).toEqual({
      key: "career-trainer-sprite:qa trainer",
      sprite: "hilda",
    });
  });
});
