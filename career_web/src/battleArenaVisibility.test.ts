import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const arena = readFileSync(
  fileURLToPath(new URL("./components/BattleArena.tsx", import.meta.url)),
  "utf8",
);
const styles = readFileSync(
  fileURLToPath(new URL("./styles.css", import.meta.url)),
  "utf8",
);

describe("battle arena visibility", () => {
  it("gives the renderer a real surface instead of an absolute child inside a zero-height wrapper", () => {
    expect(arena).toContain('className="battle-arena-root"');
    expect(styles).toMatch(/\.arena-wrap\{[^}]*position:relative/);
    expect(styles).toMatch(/\.battle-arena-root\{[^}]*position:absolute[^}]*inset:0/);
  });

  it("keeps the animated Pokemon layer inside the same bounded arena surface", () => {
    expect(arena).toContain('className="field-pokemon-layer"');
    expect(styles).toMatch(/\.arena-canvas-shell\{[^}]*position:absolute[^}]*inset:0/);
  });
});
