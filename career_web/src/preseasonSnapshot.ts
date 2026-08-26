import type { PreseasonSnapshot } from "./api";

function invalid(): never {
  throw new Error("Invalid preseason response");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function validClubOffer(value: unknown): boolean {
  if (!isRecord(value)) return false;
  if (typeof value.id !== "string" || typeof value.club_name !== "string") return false;
  if (!Number.isFinite(value.salary) || !Number.isFinite(value.seasons)) return false;
  if (!Array.isArray(value.loan_species) || !value.loan_species.every((entry) => typeof entry === "string")) return false;
  if (!isRecord(value.perk) || typeof value.perk.stat !== "string" || typeof value.perk.label !== "string" || !Number.isFinite(value.perk.amount)) return false;
  if (value.returning_loans !== undefined && !Array.isArray(value.returning_loans)) return false;
  return true;
}

function validSponsorOffer(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return typeof value.id === "string"
    && typeof value.name === "string"
    && typeof value.theme === "string"
    && Number.isFinite(value.upfront)
    && Number.isFinite(value.bonus)
    && typeof value.description_es === "string"
    && typeof value.description_en === "string";
}

function validCaptureCandidate(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return typeof value.id === "string"
    && typeof value.species === "string"
    && typeof value.rarity === "string"
    && Number.isFinite(value.ball_cost);
}

export function normalizePreseasonSnapshot(value: unknown): PreseasonSnapshot {
  if (!isRecord(value)) invalid();
  const snapshot = value as Partial<PreseasonSnapshot>;
  if (!Number.isFinite(snapshot.season)) invalid();
  if (typeof snapshot.club_completed !== "boolean") invalid();
  if (typeof snapshot.sponsor_completed !== "boolean") invalid();
  if (typeof snapshot.capture_completed !== "boolean") invalid();
  if (!Array.isArray(snapshot.club_offers) || !snapshot.club_offers.every(validClubOffer)) invalid();
  if (!Array.isArray(snapshot.sponsor_offers) || !snapshot.sponsor_offers.every(validSponsorOffer)) invalid();
  if (!Array.isArray(snapshot.capture_candidates) || !snapshot.capture_candidates.every(validCaptureCandidate)) invalid();
  return snapshot as PreseasonSnapshot;
}
