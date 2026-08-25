import { describe, expect, it } from "vitest";

import battleScreen from "./components/BattleScreen.tsx?raw";
import preparingComponent from "./components/BattlePreparing.tsx?raw";


describe("battle loading recovery", () => {
  it("does not leave a stalled battle on an endless preparing screen", () => {
    expect(preparingComponent).toContain("SLOW_BATTLE_WARNING_MS = 12000");
    expect(preparingComponent).toContain("setSlow(true)");
    expect(preparingComponent).toContain('className="battle-loading-recovery"');
    expect(preparingComponent).toContain("onClick={retry}");
  });

  it("retries the transcript request in place instead of reloading the whole career", () => {
    expect(preparingComponent).not.toContain("window.location.reload()");
    expect(battleScreen).toContain("const [retryAttempt, setRetryAttempt] = useState(0)");
    expect(battleScreen).toContain("[runId, battleId, retryAttempt]");
    expect(battleScreen).toContain("setRetryAttempt((current) => current + 1)");
    expect(battleScreen).toContain("onRetry={retryBattleLoading}");
  });

  it("guards a stalled attempt against repeated retry clicks", () => {
    expect(preparingComponent).toContain("const [retrying, setRetrying] = useState(false)");
    expect(preparingComponent).toContain("if (retrying || !onRetry) return");
    expect(preparingComponent).toContain("disabled={retrying}");
    expect(preparingComponent).toContain("setRetrying(false)");
    expect(preparingComponent).toContain("Reintentando...");
    expect(preparingComponent).toContain("Retrying...");
  });

  it("makes clear that a technical retry does not count as a defeat", () => {
    expect(preparingComponent).toContain("sin registrar una derrota");
    expect(preparingComponent).toContain("without recording a loss");
  });

  it("fails closed on malformed legacy lineup arrays instead of crashing the loading screen", () => {
    expect(preparingComponent).toContain("const activeRoster = Array.isArray(run?.active_roster) ? run.active_roster : []");
    expect(preparingComponent).toContain("const pokemon = Array.isArray(run?.pokemon) ? run.pokemon : []");
    expect(preparingComponent).toContain("activeRoster.map");
    expect(preparingComponent).toContain("pokemon.find");
  });

  it("fails closed when legacy prebattle metadata contains missing build or null pokemon entries", () => {
    expect(preparingComponent).toContain("run?.build?.region");
    expect(preparingComponent).toContain("entry && typeof entry === \"object\" && entry.id === id");
  });
});
