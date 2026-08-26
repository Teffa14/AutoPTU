import { beforeEach, describe, expect, it, vi } from "vitest";
import { loadBattleCheckpoint, loadLastLocalRunId, loadLocalRun } from "./localCareer";
import type { CareerRun } from "./types";

class MemoryStorage {
  private readonly values = new Map<string, string>();
  getItem(key: string): string | null { return this.values.get(key) ?? null; }
  setItem(key: string, value: string): void { this.values.set(key, String(value)); }
  removeItem(key: string): void { this.values.delete(key); }
  clear(): void { this.values.clear(); }
}

function validRun(id = "run-1"): CareerRun {
  return {
    id,
    mode: "simple",
    locale: "es",
    age: 18,
    season_number: 1,
    status: "active",
    ranked: false,
    build: { name: "Test", region: "kanto", starter: "Pikachu", classes: [], pokeballs: 0 },
    roster: [],
    pokemon: [],
    active_roster: [],
    totals: { wins: 0, losses: 0, draws: 0, titles: 0 },
    timeline: [],
  } as CareerRun;
}

describe("local career recovery guards", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", new MemoryStorage());
  });

  it.each([
    null,
    [],
    { id: "run-1" },
    { ...validRun(), timeline: null },
    { ...validRun(), pokemon: "broken" },
    { ...validRun(), season: [] },
  ])("rejects truncated local saves before they reach the UI", (payload) => {
    localStorage.setItem("autoptu-career-run:run-1", JSON.stringify(payload));
    expect(loadLocalRun("run-1")).toBeNull();
  });

  it("keeps a structurally complete legacy-compatible local save loadable", () => {
    const run = validRun();
    localStorage.setItem("autoptu-career-run:run-1", JSON.stringify(run));
    expect(loadLocalRun("run-1")?.id).toBe("run-1");
  });

  it("clears a stale last-run pointer when the stored save is truncated", () => {
    localStorage.setItem("career-last-run", "run-1");
    localStorage.setItem("autoptu-career-run:run-1", JSON.stringify({ id: "run-1" }));
    expect(loadLastLocalRunId()).toBeNull();
    expect(localStorage.getItem("career-last-run")).toBeNull();
  });

  it("rejects malformed battle checkpoints instead of restoring them", () => {
    localStorage.setItem("autoptu-career-battle-checkpoint:run-1", JSON.stringify({ id: "run-1", status: "active" }));
    expect(loadBattleCheckpoint("run-1")).toBeNull();
  });
});
