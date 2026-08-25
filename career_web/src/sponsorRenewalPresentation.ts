import type { Locale } from "./types";

interface SponsorRenewalOffer {
  name: string;
  renewal?: boolean;
}

export interface SponsorRenewalContext {
  resultLabel: string;
  relationshipLabel: string;
}

function safeNonnegativeInteger(value: unknown): number | null {
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) return null;
  return Math.trunc(parsed);
}

export function sponsorRenewalContext(
  offer: SponsorRenewalOffer,
  timeline: Record<string, unknown>[],
  seasonNumber: number,
  locale: Locale,
): SponsorRenewalContext | null {
  if (!offer.renewal) return null;
  const sponsorName = offer.name.trim();
  if (!sponsorName) return null;

  const outcome = [...timeline].reverse().find((entry) => {
    if (entry.type !== "sponsor.completed") return false;
    if (String(entry.name ?? "").trim() !== sponsorName) return false;
    const season = safeNonnegativeInteger(entry.season);
    return season !== null && season < seasonNumber;
  });
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
