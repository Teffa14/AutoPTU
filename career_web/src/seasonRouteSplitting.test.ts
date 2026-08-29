import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const season = readFileSync(fileURLToPath(new URL("./components/SeasonScreen.tsx", import.meta.url)), "utf8");
const seasonHub = readFileSync(fileURLToPath(new URL("./components/SeasonHub.tsx", import.meta.url)), "utf8");

describe("season route bundle splitting", () => {
  it("keeps the optional economy market out of the synchronous season graph", () => {
    expect(season).not.toContain('import { EconomyShop } from "./EconomyShop";');
    expect(season).toContain('import("./EconomyShop")');
  });

  it("warms the economy market only after spend-money intent", () => {
    expect(season).toContain('onPointerEnter={warmEconomyShop}');
    expect(season).toContain('onFocus={warmEconomyShop}');
    expect(season).not.toContain('useEffect(() => {\n    warmEconomyShop');
  });

  it("keeps the preseason market out of the synchronous returning-season graph", () => {
    expect(seasonHub).not.toContain('import { PreseasonMarket } from "./PreseasonMarket";');
    expect(seasonHub).toContain('import("./PreseasonMarket")');
    expect(seasonHub).toContain('<Suspense fallback=');
  });

  it("keeps decision outcome presentation out of the normal season hub graph", () => {
    expect(seasonHub).not.toContain('import { DecisionOutcomePanel } from "./DecisionOutcomePanel";');
    expect(seasonHub).toContain('import("./DecisionOutcomePanel")');
  });
});
