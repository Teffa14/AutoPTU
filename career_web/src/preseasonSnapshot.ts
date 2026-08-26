import type { PreseasonSnapshot } from "./api";

function invalid(): never {
  throw new Error("Invalid preseason response");
}

export function normalizePreseasonSnapshot(value: unknown): PreseasonSnapshot {
  if (!value || typeof value !== "object" || Array.isArray(value)) invalid();
  const snapshot = value as Partial<PreseasonSnapshot>;
  if (!Number.isFinite(snapshot.season)) invalid();
  if (typeof snapshot.club_completed !== "boolean") invalid();
  if (typeof snapshot.sponsor_completed !== "boolean") invalid();
  if (typeof snapshot.capture_completed !== "boolean") invalid();
  if (!Array.isArray(snapshot.club_offers)) invalid();
  if (!Array.isArray(snapshot.sponsor_offers)) invalid();
  if (!Array.isArray(snapshot.capture_candidates)) invalid();
  return snapshot as PreseasonSnapshot;
}
