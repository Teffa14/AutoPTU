import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const marketComponent = readFileSync(
  fileURLToPath(new URL("./components/PreseasonMarket.tsx", import.meta.url)),
  "utf8",
);
const marketCss = readFileSync(
  fileURLToPath(new URL("./components/preseason-market.css", import.meta.url)),
  "utf8",
);
const seasonCss = readFileSync(
  fileURLToPath(new URL("./components/career-ux-refresh.css", import.meta.url)),
  "utf8",
);
const trainerPicker = readFileSync(
  fileURLToPath(new URL("./components/TrainerSpritePicker.tsx", import.meta.url)),
  "utf8",
);


describe("career UX cohesion", () => {
  it("keeps sponsor and club offers on explicit high-contrast surfaces", () => {
    expect(marketCss).toContain("background:linear-gradient(155deg,#f7edd3,#e9ddbd);color:#1d2a24");
    expect(marketCss).toContain(".sponsor-card{color:#17241d;background:linear-gradient(155deg,#f4ead1,#dce9df)");
    expect(marketCss).toContain(".sponsor-card button{color:#fff7e4;background:#173c31}");
  });

  it("progressively reveals scouting tiers through league and scouting", () => {
    expect(marketComponent).toContain("const leagueCeiling: Record<string, number> = { junior: 0, rookie: 1, regular: 2, elite: 3 }");
    expect(marketComponent).toContain("Math.floor(safeScouting / 3)");
    expect(marketComponent).toContain("captureCandidatesForProgress(snapshot.capture_candidates, run.league, run.scouting)");
  });

  it("shows exact decision mechanics after selection instead of on every choice card", () => {
    expect(seasonCss).toContain(".decision-options .choice-effects");
    expect(seasonCss).toContain("display: none;");
    expect(seasonCss).toContain(".decision-confirmation");
    expect(seasonCss).toContain("grid-template-columns: minmax(0, 1fr) auto");
  });

  it("loads one trainer preview instead of rendering an image per archive entry", () => {
    expect(trainerPicker.match(/<img/g)?.length ?? 0).toBe(1);
    expect(trainerPicker).toContain("<select");
    expect(trainerPicker).toContain('type="search"');
  });
});
