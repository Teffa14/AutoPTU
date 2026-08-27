import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const arena = readFileSync(
  fileURLToPath(new URL("./components/BattleArena.tsx", import.meta.url)),
  "utf8",
);
const visibilityCss = readFileSync(
  fileURLToPath(new URL("./components/battle-arena-visibility.css", import.meta.url)),
  "utf8",
);
const main = readFileSync(
  fileURLToPath(new URL("./main.tsx", import.meta.url)),
  "utf8",
);

describe("battle arena visibility", () => {
  it("anchors the renderer wrapper to the full arena instead of a zero-height flow box", () => {
    expect(visibilityCss).toMatch(/\.arena-wrap\s*\{[^}]*position:\s*relative/);
    expect(visibilityCss).toContain(".arena-wrap > div:has(> .arena-canvas-shell)");
    expect(visibilityCss).toMatch(/position:\s*absolute\s*!important/);
    expect(visibilityCss).toMatch(/inset:\s*0/);
    expect(main).toContain('import "./components/battle-arena-visibility.css"');
  });

  it("keeps the animated Pokemon layer inside the same bounded arena surface", () => {
    expect(arena).toContain('className="arena-canvas-shell"');
    expect(arena).toContain('className="field-pokemon-layer"');
    expect(visibilityCss).toContain("> .arena-canvas-shell");
    expect(visibilityCss).toMatch(/\.arena-wrap > div:has\(> \.arena-canvas-shell\) > \.arena-canvas-shell\s*\{[^}]*position:\s*absolute[^}]*inset:\s*0/);
  });
});
