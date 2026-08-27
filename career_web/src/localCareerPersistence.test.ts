import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { loadBattleCheckpoint, loadLastLocalRunId, removeLocalRun, saveLocalRun } from "./localCareer";
import localCareerSource from "./localCareer.ts?raw";
import homeScreenSource from "./components/HomeScreen.tsx?raw";

let storage: Map<string, string>;

beforeEach(() => {
  storage = new Map<string, string>();
  const localStorageStub = {
    get length() { return storage.size; },
    clear: () => storage.clear(),
    getItem: (key: string) => storage.get(key) ?? null,
    key: (index: number) => [...storage.keys()][index] ?? null,
    removeItem: (key: string) => { storage.delete(key); },
    setItem: (key: string, value: string) => { storage.set(key, String(value)); },
  } satisfies Storage;
  Object.defineProperty(globalThis, "localStorage", { configurable: true, value: localStorageStub });
});

afterEach(() => {
  Reflect.deleteProperty(globalThis, "localStorage");
});

describe("local career persistence boundaries", () => {
  it("returns before ranked runs can mutate browser training state", () => {
    const rankedGuard = localCareerSource.indexOf("if (run.ranked) return;");
    const trainingRead = localCareerSource.indexOf("localStorage.getItem(trainingKey)");
    const trainingWrite = localCareerSource.indexOf('localStorage.setItem(trainingKey, "conditioning")');
    const runWrite = localCareerSource.indexOf("JSON.stringify(run)");

    expect(rankedGuard).toBeGreaterThan(-1);
    expect(trainingRead).toBeGreaterThan(rankedGuard);
    expect(trainingWrite).toBeGreaterThan(rankedGuard);
    expect(runWrite).toBeGreaterThan(rankedGuard);
  });

  it("removes a stale resume pointer instead of sending the home screen to a missing career", () => {
    localStorage.setItem("career-last-run", "missing-run");

    expect(loadLastLocalRunId()).toBeNull();
    expect(localStorage.getItem("career-last-run")).toBeNull();
    expect(homeScreenSource).toContain("loadLastLocalRunId()");
  });

  it("keeps the resume pointer when the referenced casual career has a render-safe shape", () => {
    localStorage.setItem("career-last-run", "run-1");
    localStorage.setItem("autoptu-career-run:run-1", JSON.stringify({
      id: "run-1",
      ranked: false,
      status: "active",
      season_number: 1,
      build: {},
    }));

    expect(loadLastLocalRunId()).toBe("run-1");
    expect(localStorage.getItem("career-last-run")).toBe("run-1");
  });

  it("clears the resume pointer when the referenced save is truncated", () => {
    localStorage.setItem("career-last-run", "truncated-run");
    localStorage.setItem("autoptu-career-run:truncated-run", JSON.stringify({ id: "truncated-run", ranked: false }));

    expect(loadLastLocalRunId()).toBeNull();
    expect(localStorage.getItem("career-last-run")).toBeNull();
  });

  it("rejects a ranked residue from the local resume pointer", () => {
    localStorage.setItem("career-last-run", "ranked-1");
    localStorage.setItem("autoptu-career-run:ranked-1", JSON.stringify({ id: "ranked-1", ranked: true }));

    expect(loadLastLocalRunId()).toBeNull();
    expect(localStorage.getItem("career-last-run")).toBeNull();
  });

  it("does not let coercible decision counters suppress a battle rollback checkpoint", () => {
    const runId = "run-corrupt-decisions";
    const previous = {
      id: runId,
      ranked: false,
      status: "active",
      season_number: 1,
      build: {},
      season: {
        status: "decision",
        decisions_required: [1],
        decisions_completed: [1],
      },
    };
    localStorage.setItem(`autoptu-career-run:${runId}`, JSON.stringify(previous));

    saveLocalRun({
      ...previous,
      season: {
        status: "battle",
        decisions_required: 1,
        decisions_completed: 1,
      },
    } as never);

    expect(loadBattleCheckpoint(runId)?.season?.status).toBe("decision");
  });

  it("releases the pre-battle rollback checkpoint after a successful post-battle save", () => {
    const runId = "run-finished-battle";
    const decisionRun = {
      id: runId,
      ranked: false,
      status: "active",
      season_number: 3,
      build: {},
      season: {
        status: "decision",
        decisions_required: 1,
        decisions_completed: 0,
      },
    };
    localStorage.setItem(`autoptu-career-run:${runId}`, JSON.stringify(decisionRun));

    saveLocalRun({
      ...decisionRun,
      season: {
        status: "battle",
        decisions_required: 1,
        decisions_completed: 1,
      },
    } as never);
    expect(loadBattleCheckpoint(runId)?.season?.status).toBe("decision");

    saveLocalRun({
      ...decisionRun,
      season_number: 4,
      season: {
        status: "decision",
        decisions_required: 1,
        decisions_completed: 0,
      },
    } as never);

    expect(loadBattleCheckpoint(runId)).toBeNull();
  });

  it("removes the run, its automatic training plan, and matching resume pointer together", () => {
    localStorage.setItem("career-last-run", "run-2");
    localStorage.setItem("autoptu-career-run:run-2", JSON.stringify({ id: "run-2", ranked: false }));
    localStorage.setItem("autoptu-career-training-plan:run-2", "power");

    removeLocalRun("run-2");

    expect(localStorage.getItem("autoptu-career-run:run-2")).toBeNull();
    expect(localStorage.getItem("autoptu-career-training-plan:run-2")).toBeNull();
    expect(localStorage.getItem("career-last-run")).toBeNull();
  });
});