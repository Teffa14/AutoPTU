const INVALID_VISIBLE_NAMES = new Set(["", "none", "null", "nan", "undefined", "infinity"]);

function visibleName(value: unknown): string {
  if (typeof value !== "string" && typeof value !== "number") return "";
  const normalized = String(value).trim().split(/\s+/).filter(Boolean).join(" ");
  return INVALID_VISIBLE_NAMES.has(normalized.toLocaleLowerCase()) ? "" : normalized;
}

function isLeaderboardEntry(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function leaderboardEntries(value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value)) return [];
  return value.filter(isLeaderboardEntry);
}

export function leaderboardTrainerName(entry: unknown): string {
  if (!isLeaderboardEntry(entry)) return "Trainer";
  return visibleName(entry.trainer_name) || visibleName(entry.handle) || "Trainer";
}
