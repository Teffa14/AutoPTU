import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const trainerCss = readFileSync(
  fileURLToPath(new URL("./components/battle-trainer-strip.css", import.meta.url)),
  "utf8",
);
const trainerComponent = readFileSync(
  fileURLToPath(new URL("./components/BattleTrainerStrip.tsx", import.meta.url)),
  "utf8",
);


describe("battle trainer layout", () => {
  it("places trainers on arena-edge pads without reserving a broadcast lane", () => {
    expect(trainerComponent).toContain('className="battle-trainer-strip"');
    expect(trainerCss).toContain("pointer-events: none");
    expect(trainerCss).toContain("bottom: .5rem");
    expect(trainerCss).not.toContain(".battle-trainer-strip + div");
  });

  it("removes trainer battle quotes from the combat surface", () => {
    expect(trainerComponent).not.toContain("<q>");
    expect(trainerComponent).not.toContain("line={presentation.home.line}");
    expect(trainerComponent).not.toContain("line={presentation.away.line}");
  });

  it("keeps trainer identity and authoritative rival progression visible", () => {
    expect(trainerComponent).toContain('className="battle-trainer-progression"');
    expect(trainerCss).toContain(".battle-trainer-progression");
    expect(trainerCss).toContain(".battle-trainer-copy strong");
  });

  it("shrinks the arena-edge pads on phones and short landscape viewports", () => {
    expect(trainerCss).toContain("@media (max-width: 699px)");
    expect(trainerCss).toContain("@media (max-height: 500px)");
    expect(trainerCss).toContain("width: 2.35rem");
    expect(trainerCss).toContain("height: 2.85rem");
  });

  it("keeps trainer sprites bounded instead of allowing intrinsic image size", () => {
    expect(trainerCss).toContain("object-fit: contain");
    expect(trainerCss).toContain("image-rendering: pixelated");
  });
});
