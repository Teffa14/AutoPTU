import { describe, expect, it } from "vitest";

import { sponsorRenewalContext } from "./sponsorRenewalPresentation";

const completed = {
  type: "sponsor.completed",
  season: 1,
  name: "Rotom Broadcast",
  wins: 5,
  target: 4,
};

describe("sponsorRenewalContext", () => {
  it("shows the verified previous result for a real renewal", () => {
    expect(sponsorRenewalContext(
      { name: "Rotom Broadcast", renewal: true },
      [completed],
      2,
      "es",
    )).toEqual({
      relationshipLabel: "RELACIÓN CONTINUA",
      resultLabel: "Objetivo anterior verificado: 5/4 victorias",
    });
  });

  it("does not leak another sponsor's history into a new relationship", () => {
    expect(sponsorRenewalContext(
      { name: "Porygon Systems", renewal: false },
      [completed],
      2,
      "en",
    )).toBeNull();
  });

  it("fails closed on malformed historical numbers", () => {
    expect(sponsorRenewalContext(
      { name: "Rotom Broadcast", renewal: true },
      [{ ...completed, wins: "NaN", target: Infinity }],
      2,
      "en",
    )).toBeNull();
    expect(sponsorRenewalContext(
      { name: "Rotom Broadcast", renewal: true },
      [{ ...completed, wins: " ", target: "4" }],
      2,
      "en",
    )).toBeNull();
  });
});
