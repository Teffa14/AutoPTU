import type { CareerRun } from "./types";

const RUN_PREFIX = "autoptu-career-run:";
const TRAINING_PREFIX = "autoptu-career-training-plan:";
const LAST_RUN_KEY = "career-last-run";
const AUTOMATIC_TRAINING = new Set(["conditioning", "power", "guard", "agility"]);

export function saveLocalRun(run: CareerRun): void {
  try {
    if (run.ranked) return;
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
    if (localStorage.getItem(LAST_RUN_KEY) === runId) {
      localStorage.removeItem(LAST_RUN_KEY);
    }
  } catch {
    // Ignore unavailable storage.
  }
}
