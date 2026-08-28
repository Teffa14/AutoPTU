import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const trainerPortrait = readFileSync(fileURLToPath(new URL("./components/TrainerPortrait.tsx", import.meta.url)), "utf8");
const profileScreen = readFileSync(fileURLToPath(new URL("./components/ProfileScreen.tsx", import.meta.url)), "utf8");

describe("career UI storage resilience", () => {
  it("routes trainer portrait storage through the guarded browser boundary", () => {
    expect(trainerPortrait).not.toMatch(/(?:window\.)?localStorage\.getItem\(/);
    expect(trainerPortrait).toContain('readLocalStorage(`career-trainer-sprite:${name.trim().toLocaleLowerCase()}`)');
  });

  it("routes profile training-plan preferences through the guarded browser boundary", () => {
    expect(profileScreen).not.toMatch(/(?:window\.)?localStorage\.(?:getItem|setItem)\(/);
    expect(profileScreen).toContain("readLocalStorage(trainingStorageKey(runId))");
    expect(profileScreen).toContain("writeLocalStorage(trainingStorageKey(run.id), trainingPlan)");
  });
});
