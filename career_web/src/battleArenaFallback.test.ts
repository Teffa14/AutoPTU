import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const battleArena = readFileSync(
  fileURLToPath(new URL("./components/BattleArena.tsx", import.meta.url)),
  "utf8",
);

describe("battle renderer fallback", () => {
  it("degrades a failed full renderer to light mode before giving up", () => {
    const initStart = battleArena.indexOf("async function start()");
    const initEnd = battleArena.indexOf("void start();", initStart);
    const initBlock = battleArena.slice(initStart, initEnd);

    expect(initStart).toBeGreaterThan(-1);
    expect(initBlock).toContain("catch");
    expect(initBlock).toContain('effectiveQuality === "full"');
    expect(initBlock).toContain('persistBattleVisualQuality("light")');
    expect(initBlock).toContain('setQuality("light")');
  });

  it("surfaces a readable fallback if even light renderer initialization fails", () => {
    expect(battleArena).toContain("battle-arena-fallback");
    expect(battleArena).toContain("rendererFailed");
  });
});
