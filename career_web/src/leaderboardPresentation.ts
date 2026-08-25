export function leaderboardTrainerName(entry: Record<string, unknown>): string {
  return String(entry.trainer_name ?? entry.handle);
}
