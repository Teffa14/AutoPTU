import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

const battleScreenSource = readFileSync(new URL("./components/BattleScreen.tsx", import.meta.url), "utf8");

describe("opponent roster privacy", () => {
  it("does not publish the total private opponent roster size before it is observed", () => {
    expect(battleScreenSource).not.toContain("${revealedTeamCount} / ${team.length}");
  });
});
