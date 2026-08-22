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

export function decisionMemory(run: CareerRun, family: string, npcName = ""): DecisionMemory {
  const current = findInDecisionList(run.season?.decision_history ?? [], family, run.season_number);
  if (current) return { prior: current, contactBond: recordedBond(run, npcName) };

  for (const entry of [...run.timeline].reverse()) {
    if (entry.type !== "season.completed") continue;
    const season = Number(entry.season ?? 0);
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
    const optionId = String(record.option_id ?? "");
    if (!optionId.startsWith(`${family}:`)) continue;
    const label = String(record.label ?? "").trim();
    if (!label) continue;
    return { season, optionId, label };
  }
  return undefined;
}

function recordedBond(run: CareerRun, npcName: string): number {
  if (!npcName) return 0;
  return Number(run.relationships?.[npcName] ?? 0);
}
