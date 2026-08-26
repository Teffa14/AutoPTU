import type { CareerRun, Locale } from "./types";

export interface SponsorSeasonReview {
  season: number;
  status: "completed" | "failed" | "declined";
  name: string;
  objective: string;
  target: number;
  actual: number;
  upfront: number;
  bonusPaid: number;
}

function recordEntry(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function timelineEntries(run: CareerRun): Record<string, unknown>[] {
  return Array.isArray(run.timeline) ? run.timeline.filter(recordEntry) : [];
}

function seasonNumber(entry: unknown): number {
  if (!recordEntry(entry)) return 0;
  const value = Number(entry.season);
  return Number.isFinite(value) ? value : 0;
}

function finiteNonNegative(value: unknown): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
}

function visibleText(value: unknown): string {
  const text = typeof value === "string" ? value.trim() : "";
  return text && !["null", "undefined", "nan", "infinity"].includes(text.toLowerCase()) ? text : "";
}

export function sponsorSeasonReview(run: CareerRun, season?: number): SponsorSeasonReview | null {
  const timeline = timelineEntries(run);
  const targetSeason = season ?? [...timeline].reverse().map(seasonNumber).find((value) => value > 0) ?? run.season_number;
  const entries = timeline.filter((entry) => seasonNumber(entry) === targetSeason);
  const declined = entries.find((entry) => entry.type === "sponsor.declined");
  const signed = entries.find((entry) => entry.type === "sponsor.signed");
  const outcome = [...entries].reverse().find((entry) => entry.type === "sponsor.completed" || entry.type === "sponsor.failed");

  if (!signed) {
    return declined ? {
      season: targetSeason,
      status: "declined",
      name: "",
      objective: "",
      target: 0,
      actual: 0,
      upfront: 0,
      bonusPaid: 0,
    } : null;
  }

  if (!outcome) return null;
  const status = outcome.type === "sponsor.completed" ? "completed" : "failed";
  return {
    season: targetSeason,
    status,
    name: visibleText(signed.name) || visibleText(outcome.name) || "Sponsor",
    objective: visibleText(signed.objective) || "wins",
    target: finiteNonNegative(outcome.target ?? signed.target),
    actual: finiteNonNegative(outcome.wins),
    upfront: finiteNonNegative(signed.upfront),
    bonusPaid: finiteNonNegative(outcome.bonus),
  };
}

export function sponsorObjectiveLabel(review: SponsorSeasonReview, locale: Locale): string {
  if (review.status === "declined") return locale === "es" ? "Temporada sin sponsor" : "Sponsor-free season";
  if (review.objective === "wins") {
    return locale === "es"
      ? `${review.actual}/${review.target} victorias`
      : `${review.actual}/${review.target} wins`;
  }
  return `${review.actual}/${review.target}`;
}

export function sponsorStatusLabel(review: SponsorSeasonReview, locale: Locale): string {
  if (review.status === "declined") return locale === "es" ? "Sin acuerdo" : "No agreement";
  if (review.status === "completed") return locale === "es" ? "Objetivo cumplido" : "Objective completed";
  return locale === "es" ? "Objetivo no cumplido" : "Objective missed";
}
