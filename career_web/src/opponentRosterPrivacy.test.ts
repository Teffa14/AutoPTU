import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

const battleScreenSource = readFileSync(new URL("./components/BattleScreen.tsx", import.meta.url), "utf8");

describe("opponent roster privacy", () => {
  it("does not publish the total private opponent roster size before it is observed", () => {
    expect(battleScreenSource).not.toContain('`${revealedTeamCount} / ${team.length} ${locale === "es" ? "Pokémon rivales revelados" : "opponent Pokémon revealed"}`');
  });

  it("does not render placeholder slots for unrevealed opponent Pokémon", () => {
    expect(battleScreenSource).toContain("const visibleTeam = side === \"away\" && knowledge");
    expect(battleScreenSource).toContain("{visibleTeam.map((entry) =>");
    expect(battleScreenSource).not.toContain("Unrevealed opponent Pokémon");
  });
});
