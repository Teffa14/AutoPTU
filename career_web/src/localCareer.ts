import type { CareerRun } from "./types";

const RUN_PREFIX = "autoptu-career-run:";
const TRAINING_PREFIX = "autoptu-career-training-plan:";
const BATTLE_CHECKPOINT_PREFIX = "autoptu-career-battle-checkpoint:";
const LAST_RUN_KEY = "career-last-run";
const AUTOMATIC_TRAINING = new Set(["conditioning", "power", "guard", "agility"]);

function battleCheckpointKey(runId: string): string {
  return `${BATTLE_CHECKPOINT_PREFIX}${runId}`;
}

function isStoredCareerRun(value: unknown, runId: string, activeOnly = false): value is CareerRun {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const run = value as Partial<CareerRun>;
  if (run.id !== runId || run.ranked) return false;
  if (run.status !== "active" && run.status !== "retired") return false;
  if (activeOnly && run.status !== "active") return false;
  if (!Number.isFinite(run.season_number)) return false;
  if (!run.build || typeof run.build !== "object" || Array.isArray(run.build)) return false;
  if (run.mode !== undefined && run.mode !== "simple" && run.mode !== "advanced") return false;
  if (run.locale !== undefined && run.locale !== "es" && run.locale !== "en") return false;
  if (run.age !== undefined && !Number.isFinite(run.age)) return false;
  if (run.roster !== undefined && !Array.isArray(run.roster)) return false;
  if (run.pokemon !== undefined && !Array.isArray(run.pokemon)) return false;
  if (run.active_roster !== undefined && !Array.isArray(run.active_roster)) return false;
  if (run.totals !== undefined && (!run.totals || typeof run.totals !== "object" || Array.isArray(run.totals))) return false;
  if (run.timeline !== undefined && !Array.isArray(run.timeline)) return false;
  if (run.season !== undefined && (!run.season || typeof run.season !== "object" || Array.isArray(run.season))) return false;
  return true;
}

function isExhaustedDecisionPhase(run: CareerRun): boolean {
  if (run.status !== "active" || run.season?.status !== "decision") return false;
  const required = run.season.decisions_required ?? 0;
  const completed = run.season.decisions_completed ?? 0;
  return required > 0 && completed >= required;
}

function shouldCreateBattleCheckpoint(previous: CareerRun | null, next: CareerRun): previous is CareerRun {
  if (!previous || previous.id !== next.id || previous.ranked || next.ranked) return false;
  if (previous.status !== "active" || next.status !== "active") return false;
  if (!previous.season || !next.season) return false;
  if (previous.season_number !== next.season_number || previous.season.status !== "decision") return false;
  if (isExhaustedDecisionPhase(previous)) return false;
  return next.season.status === "battle" || isExhaustedDecisionPhase(next);
}

function persistLocalRun(run: CareerRun): boolean {
  try {
    if (run.ranked) return false;
    const existingRaw = localStorage.getItem(`${RUN_PREFIX}${run.id}`);
    let existing: CareerRun | null = null;
    if (existingRaw) {
      try {
        const parsed = JSON.parse(existingRaw) as unknown;
        existing = isStoredCareerRun(parsed, run.id) ? parsed : null;
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
    return true;
  } catch {
    // Storage can be unavailable in private/restricted browser contexts.
    return false;
  }
}

export function saveLocalRun(run: CareerRun): void {
  if (run.ranked) return;
  persistLocalRun(run);
}

export function loadLocalRun(runId: string): CareerRun | null {
  try {
    const raw = localStorage.getItem(`${RUN_PREFIX}${runId}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as unknown;
    return isStoredCareerRun(parsed, runId) ? parsed : null;
  } catch {
    return null;
  }
}

export function loadBattleCheckpoint(runId: string): CareerRun | null {
  try {
    const raw = localStorage.getItem(battleCheckpointKey(runId));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as unknown;
    return isStoredCareerRun(parsed, runId, true) ? parsed : null;
  } catch {
    return null;
  }
}

export function restoreBattleCheckpoint(runId: string): CareerRun | null {
  const checkpoint = loadBattleCheckpoint(runId);
  if (!checkpoint) return null;
  if (!persistLocalRun(checkpoint)) return null;
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
