import type { CareerRun } from "./types";

export type RecordedDecisionMemory = {
  season: number;
  optionId: string;
  label: string;
};

export type DecisionMemory = {
  prior?: RecordedDecisionMemory;
  contactBond: number;
};

function finitePersistedNumber(value: unknown): number | undefined {
  if (typeof value === "number") return Number.isFinite(value) ? value : undefined;
  if (typeof value !== "string") return undefined;
  const normalized = value.trim();
  if (!normalized) return undefined;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function decisionMemory(run: CareerRun, family: string, npcName = ""): DecisionMemory {
  const current = findInDecisionList(run.season?.decision_history ?? [], family, run.season_number);
  if (current) return { prior: current, contactBond: recordedBond(run, npcName) };

  const timeline = Array.isArray(run.timeline) ? run.timeline : [];
  for (const entry of [...timeline].reverse()) {
    if (entry.type !== "season.completed") continue;
    const season = finitePersistedNumber(entry.season);
    if (season === undefined) continue;
    const decisions = Array.isArray(entry.decisions) ? entry.decisions : [];
    const found = findInDecisionList(decisions, family, season);
    if (found) return { prior: found, contactBond: recordedBond(run, npcName) };
  }

  return { contactBond: recordedBond(run, npcName) };
}

function findInDecisionList(values: unknown[], family: string, season: number): RecordedDecisionMemory | undefined {
  for (const value of [...values].reverse()) {
    if (!value || typeof value !== "object") continue;
    const record = value as Record<string, unknown>;
    const optionId = typeof record.option_id === "string" ? record.option_id : "";
    if (!optionId.startsWith(`${family}:`)) continue;
    const label = typeof record.label === "string" ? record.label.trim() : "";
    if (!label) continue;
    return { season, optionId, label };
  }
  return undefined;
}

function recordedBond(run: CareerRun, npcName: string): number {
  if (!npcName) return 0;
  return finitePersistedNumber(run.relationships?.[npcName] ?? 0) ?? 0;
}
