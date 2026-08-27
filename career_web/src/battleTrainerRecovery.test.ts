import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const trainerStrip = readFileSync(
  fileURLToPath(new URL("./components/BattleTrainerStrip.tsx", import.meta.url)),
  "utf8",
);

describe("battle trainer recovery", () => {
  it("recovers the persisted career before falling back to the default trainer", () => {
    expect(trainerStrip).toContain('import { loadLocalRun } from "../localCareer"');
    expect(trainerStrip).toContain("const presentationRun = run ?? localRunForBattle(transcript.battle_id)");
    expect(trainerStrip).toContain("return runId ? loadLocalRun(runId) : null");
  });

  it("extracts only the career prefix from canonical battle ids", () => {
    expect(trainerStrip).toContain("battleId.match(/^(.*)-s\\d+-m\\d+$/)");
  });
});
