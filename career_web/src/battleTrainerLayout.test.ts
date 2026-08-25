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
  it("keeps trainer presentation in a dedicated lane above the arena host", () => {
    expect(trainerComponent).toContain('className="battle-trainer-strip"');
    expect(trainerCss).toContain(".battle-trainer-strip + div");
    expect(trainerCss).toContain("inset: 5.35rem 0 0 !important");
  });

  it("compacts the trainer lane on phones without restoring overlap", () => {
    expect(trainerCss).toContain("@media (max-width: 699px)");
    expect(trainerCss).toContain("inset: 3.85rem 0 0 !important");
    expect(trainerCss).toContain(".battle-trainer-copy q,");
    expect(trainerCss).toContain("display: none");
  });

  it("keeps authoritative rival progression visible on compact battle layouts", () => {
    expect(trainerComponent).toContain('className="battle-trainer-progression"');
    expect(trainerCss).toContain(".battle-trainer-copy small:not(.battle-trainer-progression)");
    expect(trainerCss).toContain(".battle-trainer-progression {\n    display: block;");
    expect(trainerCss).toContain("@media (max-width: 430px)");
    expect(trainerCss).toContain("max-width: 5.25rem");
  });

  it("compacts the trainer lane on short landscape viewports", () => {
    expect(trainerCss).toContain("@media (max-height: 500px)");
    expect(trainerCss).toContain("height: 2.8rem");
    expect(trainerCss).toContain("inset: 3.35rem 0 0 !important");
    expect(trainerCss).toContain("width: 2.1rem");
    expect(trainerCss).toContain("height: 2.1rem");
  });

  it("keeps trainer sprites bounded instead of allowing intrinsic image size", () => {
    expect(trainerCss).toContain("width: 3.45rem");
    expect(trainerCss).toContain("height: 3.45rem");
    expect(trainerCss).toContain("object-fit: contain");
  });
});
