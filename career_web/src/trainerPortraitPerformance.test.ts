import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const source = readFileSync(fileURLToPath(new URL("./components/TrainerPortrait.tsx", import.meta.url)), "utf8");

describe("trainer portrait loading", () => {
  it("does not pull the multi-megabyte generated portrait sheet into the Career bundle", () => {
    expect(source).not.toContain("trainer-portraits-v1.png");
    expect(source).toContain("trainerSpriteUrl(sprite)");
  });

  it("defers off-screen trainer sprite image work", () => {
    expect(source).toContain('loading="lazy"');
    expect(source).toContain('decoding="async"');
  });

  it("keeps deterministic role-specific NPC sprite pools", () => {
    expect(source).toContain("ROLE_SPRITES");
    expect(source).toContain('rival: ["acetrainer", "acetrainerf", "benga", "hugh"]');
    expect(source).toContain("stableIndex(name, options.length)");
  });
});
