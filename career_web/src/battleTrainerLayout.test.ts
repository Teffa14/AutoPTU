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
  it("lays trainers over the arena instead of reserving a broadcast strip", () => {
    expect(trainerComponent).toContain('className="battle-trainer-strip"');
    expect(trainerCss).toContain("inset: 0;");
    expect(trainerCss).toContain("pointer-events: none");
    expect(trainerCss).not.toContain(".battle-trainer-strip + div");
  });

  it("anchors home and away trainers to opposite league-field platforms", () => {
    expect(trainerCss).toContain(".battle-trainer-side.left");
    expect(trainerCss).toContain("bottom: clamp(1.4rem, 8%, 4.8rem)");
    expect(trainerCss).toContain(".battle-trainer-side.right");
    expect(trainerCss).toContain("top: clamp(1.3rem, 8%, 4.6rem)");
    expect(trainerCss).toContain(".battle-trainer-sprite-frame::after");
    expect(trainerCss).toContain("rotateX(54deg)");
  });

  it("does not render scripted trainer quotes", () => {
    expect(trainerComponent).not.toContain("<q>");
    expect(trainerComponent).not.toContain("line={");
    expect(trainerCss).not.toContain("battle-trainer-copy q");
  });

  it("preserves formal rival progression while dropping secondary copy on compact screens", () => {
    expect(trainerComponent).toContain('className="battle-trainer-progression"');
    expect(trainerCss).toContain("@media (max-width: 699px)");
    expect(trainerCss).toContain(".battle-trainer-copy small:not(.battle-trainer-progression)");
    expect(trainerCss).toContain("@media (max-width: 430px)");
    expect(trainerCss).toContain(".battle-trainer-progression {\n    display: none;");
  });

  it("compacts trainer presence on short landscape viewports", () => {
    expect(trainerCss).toContain("@media (max-height: 500px)");
    expect(trainerCss).toContain("bottom: .35rem");
    expect(trainerCss).toContain("top: .35rem");
    expect(trainerCss).toContain("width: 2.8rem");
    expect(trainerCss).toContain("height: 3.4rem");
  });

  it("keeps trainer sprites bounded instead of allowing intrinsic image size", () => {
    expect(trainerCss).toContain("width: clamp(4.2rem, 9vw, 5.8rem)");
    expect(trainerCss).toContain("height: clamp(5.1rem, 11vw, 7rem)");
    expect(trainerCss).toContain("object-fit: contain");
  });
});
