const INVALID_VISIBLE_NAMES = new Set(["", "none", "null", "nan", "undefined", "infinity"]);

function visibleName(value: unknown): string {
  if (typeof value !== "string" && typeof value !== "number") return "";
  const normalized = String(value).trim().split(/\s+/).filter(Boolean).join(" ");
  return INVALID_VISIBLE_NAMES.has(normalized.toLocaleLowerCase()) ? "" : normalized;
}

export function leaderboardTrainerName(entry: Record<string, unknown>): string {
  return visibleName(entry.trainer_name) || visibleName(entry.handle) || "Trainer";
}
