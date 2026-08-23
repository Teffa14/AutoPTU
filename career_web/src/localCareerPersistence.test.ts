import { describe, expect, it } from "vitest";

import localCareerSource from "./localCareer.ts?raw";


describe("local career persistence boundaries", () => {
  it("returns before ranked runs can mutate browser training state", () => {
    const rankedGuard = localCareerSource.indexOf("if (run.ranked) return;");
    const trainingRead = localCareerSource.indexOf("localStorage.getItem(trainingKey)");
    const trainingWrite = localCareerSource.indexOf('localStorage.setItem(trainingKey, "conditioning")');
    const runWrite = localCareerSource.indexOf("JSON.stringify(run)");

    expect(rankedGuard).toBeGreaterThan(-1);
    expect(trainingRead).toBeGreaterThan(rankedGuard);
    expect(trainingWrite).toBeGreaterThan(rankedGuard);
    expect(runWrite).toBeGreaterThan(rankedGuard);
  });
});
