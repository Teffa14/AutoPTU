import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const battleScreen = readFileSync(fileURLToPath(new URL("./components/BattleScreen.tsx", import.meta.url)), "utf8");

describe("opponent knowledge boundary", () => {
  it("does not render the complete hidden opponent build directly from BattleTranscript state", () => {
    expect(battleScreen).toContain("opponentKnowledgeAtEvent");
    expect(battleScreen).toContain("knowledge={awayKnowledge}");
    expect(battleScreen).not.toContain("{combatant.abilities?.map((ability)");
    expect(battleScreen).not.toContain("{combatant.moves.slice(0, 4).map((move)");
  });
});
