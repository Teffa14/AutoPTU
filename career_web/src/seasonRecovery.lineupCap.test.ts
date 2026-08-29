import { describe, expect, it } from "vitest";

import { normalizeSeasonRosterState, normalizedActiveLineup } from "./seasonRecovery";
import type { CareerRun } from "./types";

function oversizedRosterRun(): CareerRun {
  const pokemon = Array.from({ length: 8 }, (_, index) => ({
    id: `pokemon-${index + 1}`,
    species: `Species ${index + 1}`,
    level: 10,
  }));
  return {
    active_roster: pokemon.map((entry) => entry.id),
    pokemon,
  } as unknown as CareerRun;
}

describe("season roster recovery lineup cap", () => {
  it("repairs persisted lineups larger than the six-Pokemon active-team limit", () => {
    const run = oversizedRosterRun();

    expect(normalizedActiveLineup(run).map((entry) => entry.id)).toEqual([
      "pokemon-1",
      "pokemon-2",
      "pokemon-3",
      "pokemon-4",
      "pokemon-5",
      "pokemon-6",
    ]);

    const normalized = normalizeSeasonRosterState(run);
    expect(normalized.active_roster).toEqual([
      "pokemon-1",
      "pokemon-2",
      "pokemon-3",
      "pokemon-4",
      "pokemon-5",
      "pokemon-6",
    ]);
    expect(normalized.pokemon).toHaveLength(8);
  });
});
