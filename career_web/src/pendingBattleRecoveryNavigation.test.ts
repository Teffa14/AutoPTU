import { describe, expect, it } from "vitest";

import recoveryComponent from "./components/PendingBattleRecovery.tsx?raw";


describe("pending battle rollback navigation", () => {
  it("hydrates the restored checkpoint in-app instead of forcing a full browser reload", () => {
    expect(recoveryComponent).toContain("const restored = restoreBattleCheckpoint(run.id);");
    expect(recoveryComponent).toContain("onRun(restored);");
    expect(recoveryComponent).toContain("navigate(`run/${run.id}`);");
    expect(recoveryComponent).not.toContain("if (!restored) return;\n    window.location.reload();");
  });
});
