import { describe, expect, it } from "vitest";

import battleScreen from "./components/BattleScreen.tsx?raw";
import preparingComponent from "./components/BattlePreparing.tsx?raw";


describe("battle loading recovery", () => {
  it("does not leave a stalled battle on an endless preparing screen", () => {
    expect(preparingComponent).toContain("SLOW_BATTLE_WARNING_MS = 12000");
    expect(preparingComponent).toContain("setSlow(true)");
    expect(preparingComponent).toContain('className="battle-loading-recovery"');
    expect(preparingComponent).toContain("onClick={onRetry}");
  });

  it("retries the transcript request in place instead of reloading the whole career", () => {
    expect(preparingComponent).not.toContain("window.location.reload()");
    expect(battleScreen).toContain("const [retryAttempt, setRetryAttempt] = useState(0)");
    expect(battleScreen).toContain("[runId, battleId, retryAttempt]");
    expect(battleScreen).toContain("setRetryAttempt((current) => current + 1)");
    expect(battleScreen).toContain("onRetry={retryBattleLoading}");
  });

  it("makes clear that a technical retry does not count as a defeat", () => {
    expect(preparingComponent).toContain("sin registrar una derrota");
    expect(preparingComponent).toContain("without recording a loss");
  });
});
