import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const seasonHub = readFileSync(fileURLToPath(new URL("./components/SeasonHub.tsx", import.meta.url)), "utf8");
const preseasonMarket = readFileSync(fileURLToPath(new URL("./components/PreseasonMarket.tsx", import.meta.url)), "utf8");

describe("zero-roster career continuity", () => {
  it("does not expose season decisions while every Pokemon is unavailable", () => {
    expect(seasonHub).toContain("hasAvailablePokemon");
    expect(seasonHub).toContain("const seasonReady = clubReady && hasAvailablePokemon");
    expect(seasonHub).toContain("Necesitás al menos un Pokémon disponible");
  });

  it("keeps the preseason capture route open instead of allowing an empty squad to skip scouting", () => {
    expect(preseasonMarket).toContain("hasAvailablePokemon");
    expect(preseasonMarket).toContain('disabled={Boolean(busy) || !hasAvailablePokemon}');
    expect(preseasonMarket).toContain("Capturá un reemplazo para continuar");
  });
});
