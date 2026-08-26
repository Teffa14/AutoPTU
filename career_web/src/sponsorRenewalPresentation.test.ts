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

  it("preserves sponsor memory across harmless persisted name formatting drift", () => {
    expect(sponsorRenewalContext(
      { name: "  ROTOM   broadcast  ", renewal: true },
      [completed],
      2,
      "en",
    )).toEqual({
      relationshipLabel: "CONTINUING RELATIONSHIP",
      resultLabel: "Verified previous objective: 5/4 wins",
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

  it("does not merge distinct sponsors when only formatting is normalized", () => {
    expect(sponsorRenewalContext(
      { name: "Rotom Systems", renewal: true },
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

  it("survives malformed legacy timeline containers and entries", () => {
    expect(sponsorRenewalContext(
      { name: "Rotom Broadcast", renewal: true },
      null,
      2,
      "en",
    )).toBeNull();

    expect(sponsorRenewalContext(
      { name: "Rotom Broadcast", renewal: true },
      [null, "legacy-junk", 42, [], completed],
      2,
      "es",
    )).toEqual({
      relationshipLabel: "RELACIÓN CONTINUA",
      resultLabel: "Objetivo anterior verificado: 5/4 victorias",
    });
  });

  it("fails closed instead of crashing on malformed offer names", () => {
    expect(sponsorRenewalContext(
      { name: null as unknown as string, renewal: true },
      [completed],
      2,
      "en",
    )).toBeNull();
  });
});
