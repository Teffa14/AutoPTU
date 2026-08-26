import type { Locale } from "./types";

interface SponsorRenewalOffer {
  name: string;
  renewal?: boolean;
}

export interface SponsorRenewalContext {
  resultLabel: string;
  relationshipLabel: string;
}

function recordEntry(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function safeNonnegativeInteger(value: unknown): number | null {
  if (typeof value === "string" && !value.trim()) return null;
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) return null;
  return Math.trunc(parsed);
}

export function sponsorRenewalContext(
  offer: SponsorRenewalOffer,
  timeline: unknown,
  seasonNumber: number,
  locale: Locale,
): SponsorRenewalContext | null {
  if (!offer.renewal) return null;
  const sponsorName = offer.name.trim();
  if (!sponsorName) return null;

  const entries = Array.isArray(timeline) ? timeline.filter(recordEntry) : [];
  let outcome: Record<string, unknown> | null = null;
  for (let index = entries.length - 1; index >= 0; index -= 1) {
    const entry = entries[index];
    if (entry.type !== "sponsor.completed") continue;
    if (String(entry.name ?? "").trim() !== sponsorName) continue;
    const season = safeNonnegativeInteger(entry.season);
    if (season !== null && season < seasonNumber) {
      outcome = entry;
      break;
    }
  }
  if (!outcome) return null;

  const wins = safeNonnegativeInteger(outcome.wins);
  const target = safeNonnegativeInteger(outcome.target);
  if (wins === null || target === null || target === 0) return null;

  return locale === "es"
    ? {
        relationshipLabel: "RELACIÓN CONTINUA",
        resultLabel: `Objetivo anterior verificado: ${wins}/${target} victorias`,
      }
    : {
        relationshipLabel: "CONTINUING RELATIONSHIP",
        resultLabel: `Verified previous objective: ${wins}/${target} wins`,
      };
}
