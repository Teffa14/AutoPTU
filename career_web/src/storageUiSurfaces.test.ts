import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const trainerPortrait = readFileSync(fileURLToPath(new URL("./components/TrainerPortrait.tsx", import.meta.url)), "utf8");
const profileScreen = readFileSync(fileURLToPath(new URL("./components/ProfileScreen.tsx", import.meta.url)), "utf8");
const seasonScreen = readFileSync(fileURLToPath(new URL("./components/SeasonScreen.tsx", import.meta.url)), "utf8");

describe("career UI storage resilience", () => {
  it("routes trainer portrait storage through the guarded browser boundary", () => {
    expect(trainerPortrait).not.toMatch(/(?:window\.)?localStorage\.getItem\(/);
    expect(trainerPortrait).toContain('readLocalStorage(`career-trainer-sprite:${name.trim().toLocaleLowerCase()}`)');
  });

  it("routes training-plan preferences through the guarded browser boundary", () => {
    for (const source of [profileScreen, seasonScreen]) {
      expect(source).not.toMatch(/(?:window\.)?localStorage\.(?:getItem|setItem)\(/);
      expect(source).toContain("readLocalStorage(trainingStorageKey(runId))");
      expect(source).toContain("writeLocalStorage(trainingStorageKey(run.id), trainingPlan)");
    }
  });
});
