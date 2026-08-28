import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const trainerPortrait = readFileSync(fileURLToPath(new URL("./components/TrainerPortrait.tsx", import.meta.url)), "utf8");
const profile = readFileSync(fileURLToPath(new URL("./components/ProfileScreen.tsx", import.meta.url)), "utf8");
const season = readFileSync(fileURLToPath(new URL("./components/SeasonScreen.tsx", import.meta.url)), "utf8");

describe("career UI storage resilience", () => {
  it("routes render and training-plan storage through the guarded browser boundary", () => {
    for (const source of [trainerPortrait, profile, season]) {
      expect(source).not.toMatch(/(?:window\.)?localStorage\.(?:getItem|setItem)\(/);
    }

    expect(trainerPortrait).toContain('readLocalStorage(`career-trainer-sprite:${name.trim().toLocaleLowerCase()}`)');
    expect(profile).toContain('writeLocalStorage(trainingStorageKey(run.id), trainingPlan)');
    expect(profile).toContain('readLocalStorage(trainingStorageKey(runId))');
    expect(season).toContain('writeLocalStorage(trainingStorageKey(run.id), trainingPlan)');
    expect(season).toContain('readLocalStorage(trainingStorageKey(runId))');
  });
});
