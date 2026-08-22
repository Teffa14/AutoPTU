import { describe, expect, it } from "vitest";

import preparingComponent from "./components/BattlePreparing.tsx?raw";


describe("battle loading recovery", () => {
  it("does not leave a stalled battle on an endless preparing screen", () => {
    expect(preparingComponent).toContain("SLOW_BATTLE_WARNING_MS = 12000");
    expect(preparingComponent).toContain("setSlow(true)");
    expect(preparingComponent).toContain('className="battle-loading-recovery"');
    expect(preparingComponent).toContain("window.location.reload()");
  });

  it("makes clear that a technical retry does not count as a defeat", () => {
    expect(preparingComponent).toContain("sin registrar una derrota");
    expect(preparingComponent).toContain("without recording a loss");
  });
});
