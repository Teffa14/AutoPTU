import type { CareerRun } from "./types";

const RUN_PREFIX = "autoptu-career-run:";
const TRAINING_PREFIX = "autoptu-career-training-plan:";
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
    localStorage.setItem("career-last-run", run.id);
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

export function removeLocalRun(runId: string): void {
  try {
    localStorage.removeItem(`${RUN_PREFIX}${runId}`);
  } catch {
    // Ignore unavailable storage.
  }
}
