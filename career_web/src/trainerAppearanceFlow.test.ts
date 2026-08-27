import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const createScreen = readFileSync(fileURLToPath(new URL("./components/CreateScreen.tsx", import.meta.url)), "utf8");
const app = readFileSync(fileURLToPath(new URL("./App.tsx", import.meta.url)), "utf8");
const trainerPortrait = readFileSync(fileURLToPath(new URL("./components/TrainerPortrait.tsx", import.meta.url)), "utf8");

describe("trainer appearance flow", () => {
  it("repairs the returned run with the selected appearance before entering the career", () => {
    expect(createScreen).toContain("withTrainerSpriteSelection(created, trainerSprite)");
    expect(createScreen).toContain("onCreated(selectedRun)");
  });

  it("lets the repaired run keep the same selected sprite in the profile compatibility cache", () => {
    expect(app).toContain("trainerSpriteStorageEntry(run)");
    expect(trainerPortrait).toContain("career-trainer-sprite:");
    expect(trainerPortrait).toContain("trainerSpriteUrl(playerSprite)");
  });
});
