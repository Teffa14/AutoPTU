import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const dailyScreen = readFileSync(
  fileURLToPath(new URL("./components/DailyScreen.tsx", import.meta.url)),
  "utf8",
);

describe("daily screen request races", () => {
  it("invalidates an older daily load before it can overwrite a newer mode or locale", () => {
    const loadEffectStart = dailyScreen.indexOf("Promise.all([careerApi.daily(day)");
    const accountEffectStart = dailyScreen.indexOf("async function refreshAccount");
    const loadEffect = dailyScreen.slice(Math.max(0, loadEffectStart - 120), accountEffectStart);

    expect(loadEffectStart).toBeGreaterThan(-1);
    expect(loadEffect).toContain("let active = true;");
    expect(loadEffect).toContain("if (!active) return;");
    expect(loadEffect).toContain("return () => { active = false; };");
  });
});
