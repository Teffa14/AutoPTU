import type { CareerRun } from "./types";

const RUN_PREFIX = "autoptu-career-run:";
const TRAINING_PREFIX = "autoptu-career-training-plan:";
const BATTLE_CHECKPOINT_PREFIX = "autoptu-career-battle-checkpoint:";
const LAST_RUN_KEY = "career-last-run";
const AUTOMATIC_TRAINING = new Set(["conditioning", "power", "guard", "agility"]);

function battleCheckpointKey(runId: string): string {
  return `${BATTLE_CHECKPOINT_PREFIX}${runId}`;
}

function shouldCreateBattleCheckpoint(previous: CareerRun | null, next: CareerRun): previous is CareerRun {
  if (!previous || previous.id !== next.id || previous.ranked || next.ranked) return false;
  if (previous.status !== "active" || next.status !== "active") return false;
  if (!previous.season || !next.season) return false;
  return previous.season_number === next.season_number
    && previous.season.status === "decision"
    && next.season.status === "battle";
}

export function saveLocalRun(run: CareerRun): void {
  try {
    if (run.ranked) return;
    const existingRaw = localStorage.getItem(`${RUN_PREFIX}${run.id}`);
    let existing: CareerRun | null = null;
    if (existingRaw) {
      try {
        existing = JSON.parse(existingRaw) as CareerRun;
      } catch {
        existing = null;
      }
    }
    if (shouldCreateBattleCheckpoint(existing, run)) {
      localStorage.setItem(battleCheckpointKey(run.id), JSON.stringify(existing));
    }

    const trainingKey = `${TRAINING_PREFIX}${run.id}`;
    const currentPlan = localStorage.getItem(trainingKey);
    if (!currentPlan || !AUTOMATIC_TRAINING.has(currentPlan)) {
      localStorage.setItem(trainingKey, "conditioning");
    }
    localStorage.setItem(`${RUN_PREFIX}${run.id}`, JSON.stringify(run));
    localStorage.setItem(LAST_RUN_KEY, run.id);
  } catch {
    // Storage can be unavailable in private/restricted browser contexts.
  }
}

export function loadLocalRun(runId: string): CareerRun | null {
  try {
    const raw = localStorage.getItem(`${RUN_PREFIX}${runId}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CareerRun;
    return parsed?.id === runId && !parsed.ranked ? parsed : null;
  } catch {
    return null;
  }
}

export function loadBattleCheckpoint(runId: string): CareerRun | null {
  try {
    const raw = localStorage.getItem(battleCheckpointKey(runId));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CareerRun;
    return parsed?.id === runId && !parsed.ranked && parsed.status === "active" ? parsed : null;
  } catch {
    return null;
  }
}

export function restoreBattleCheckpoint(runId: string): CareerRun | null {
  const checkpoint = loadBattleCheckpoint(runId);
  if (!checkpoint) return null;
  saveLocalRun(checkpoint);
  clearBattleCheckpoint(runId);
  return checkpoint;
}

export function clearBattleCheckpoint(runId: string): void {
  try {
    localStorage.removeItem(battleCheckpointKey(runId));
  } catch {
    // Ignore unavailable storage.
  }
}

export function loadLastLocalRunId(): string | null {
  try {
    const runId = localStorage.getItem(LAST_RUN_KEY);
    if (!runId) return null;
    if (loadLocalRun(runId)) return runId;
    localStorage.removeItem(LAST_RUN_KEY);
    return null;
  } catch {
    return null;
  }
}

export function removeLocalRun(runId: string): void {
  try {
    localStorage.removeItem(`${RUN_PREFIX}${runId}`);
    localStorage.removeItem(`${TRAINING_PREFIX}${runId}`);
    localStorage.removeItem(battleCheckpointKey(runId));
    if (localStorage.getItem(LAST_RUN_KEY) === runId) {
      localStorage.removeItem(LAST_RUN_KEY);
    }
  } catch {
    // Ignore unavailable storage.
  }
}
