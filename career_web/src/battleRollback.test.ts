import { beforeEach, describe, expect, it, vi } from "vitest";

import { loadBattleCheckpoint, loadLocalRun, restoreBattleCheckpoint, saveLocalRun } from "./localCareer";
import type { CareerRun } from "./types";

function runWithSeason(status: string, revision: number, decisionsCompleted?: number): CareerRun {
  return {
    id: "rollback-run",
    ranked: false,
    status: "active",
    revision,
    season_number: 4,
    build: { name: "Rollback QA", region: "kanto", starter: "Bulbasaur", classes: [], pokeballs: 10 },
    season: {
      number: 4,
      age: 15,
      league: "junior",
      club_name: "Saffron Comets",
      status,
      battle_ids: status === "battle" ? ["rollback-run-s4-featured"] : [],
      decisions_required: 3,
      decisions_completed: decisionsCompleted ?? (status === "decision" ? 2 : 3),
      decision_history: [],
      training_completed: true,
      training_method: "conditioning",
      training_completed_ids: [],
    },
  } as unknown as CareerRun;
}

class MemoryStorage {
  private data = new Map<string, string>();
  failWritesFor: string | null = null;

  getItem(key: string) { return this.data.get(key) ?? null; }
  setItem(key: string, value: string) {
    if (key === this.failWritesFor) throw new DOMException("Storage quota exceeded", "QuotaExceededError");
    this.data.set(key, String(value));
  }
  removeItem(key: string) { this.data.delete(key); }
  clear() { this.data.clear(); }
  key(index: number) { return [...this.data.keys()][index] ?? null; }
  get length() { return this.data.size; }
}

describe("pre-battle rollback checkpoint", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", new MemoryStorage());
  });

  it("preserves the last decision state when the career enters battle", () => {
    const safe = runWithSeason("decision", 17);
    const battle = runWithSeason("battle", 18);

    saveLocalRun(safe);
    saveLocalRun(battle);

    expect(loadBattleCheckpoint(safe.id)?.revision).toBe(17);
    expect(loadLocalRun(safe.id)?.revision).toBe(18);
  });

  it("checkpoints the last safe decision when the season exhausts without entering battle", () => {
    const safe = runWithSeason("decision", 17, 2);
    const stuck = runWithSeason("decision", 18, 3);

    saveLocalRun(safe);
    saveLocalRun(stuck);

    expect(loadBattleCheckpoint(safe.id)?.revision).toBe(17);
    expect(loadBattleCheckpoint(safe.id)?.season?.decisions_completed).toBe(2);
    expect(loadLocalRun(safe.id)?.revision).toBe(18);
  });

  it("keeps the safe checkpoint when an exhausted phase is later repaired into battle", () => {
    const safe = runWithSeason("decision", 17, 2);
    const stuck = runWithSeason("decision", 18, 3);
    const repaired = runWithSeason("battle", 19, 3);

    saveLocalRun(safe);
    saveLocalRun(stuck);
    saveLocalRun(repaired);

    expect(loadBattleCheckpoint(safe.id)?.revision).toBe(17);
    expect(loadBattleCheckpoint(safe.id)?.season?.decisions_completed).toBe(2);
  });

  it("does not overwrite the pre-battle checkpoint with later battle saves", () => {
    const safe = runWithSeason("decision", 17);
    const battle = runWithSeason("battle", 18);
    const laterBattle = runWithSeason("battle", 19);

    saveLocalRun(safe);
    saveLocalRun(battle);
    saveLocalRun(laterBattle);

    expect(loadBattleCheckpoint(safe.id)?.revision).toBe(17);
  });

  it("restores the safe state and consumes the checkpoint", () => {
    const safe = runWithSeason("decision", 17);
    const battle = runWithSeason("battle", 18);

    saveLocalRun(safe);
    saveLocalRun(battle);
    const restored = restoreBattleCheckpoint(safe.id);

    expect(restored?.season?.status).toBe("decision");
    expect(loadLocalRun(safe.id)?.revision).toBe(17);
    expect(loadBattleCheckpoint(safe.id)).toBeNull();
  });

  it("keeps the checkpoint when browser storage rejects the restored career", () => {
    const storage = localStorage as MemoryStorage;
    const safe = runWithSeason("decision", 17);
    const battle = runWithSeason("battle", 18);

    saveLocalRun(safe);
    saveLocalRun(battle);
    storage.failWritesFor = "autoptu-career-run:rollback-run";

    expect(restoreBattleCheckpoint(safe.id)).toBeNull();
    expect(loadLocalRun(safe.id)?.revision).toBe(18);
    expect(loadBattleCheckpoint(safe.id)?.revision).toBe(17);
  });

  it("rejects a truncated browser save before it reaches the career UI", () => {
    localStorage.setItem("autoptu-career-run:rollback-run", JSON.stringify({ id: "rollback-run" }));

    expect(loadLocalRun("rollback-run")).toBeNull();
  });

  it("rejects corrupted collection fields while preserving legacy-compatible sparse saves", () => {
    const sparse = runWithSeason("decision", 17);
    localStorage.setItem("autoptu-career-run:rollback-run", JSON.stringify({ ...sparse, timeline: "broken" }));

    expect(loadLocalRun("rollback-run")).toBeNull();

    localStorage.setItem("autoptu-career-run:rollback-run", JSON.stringify(sparse));
    expect(loadLocalRun("rollback-run")?.revision).toBe(17);
  });
});
