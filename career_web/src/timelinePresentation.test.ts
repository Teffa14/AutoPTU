import { describe, expect, it } from "vitest";

import { timelineReplaySeasons } from "./components/TimelineScreen";
import type { CareerRun } from "./types";

describe("timeline replay archive", () => {
  it("restores every season from the persisted career timeline", () => {
    const run = {
      id: "run-1",
      season_number: 3,
      timeline: [
        { type: "career.started", season: 1 },
        { type: "season.completed", season: 1, club: "Pallet Juniors", battle_ids: ["run-1-s1-m1", "run-1-s1-m2"] },
        { type: "season.completed", season: 2, club: "Cerulean Rookies", battle_ids: ["run-1-s2-m1"] },
      ],
    } as unknown as CareerRun;

    expect(timelineReplaySeasons(run)).toEqual([
      { season: 1, club: "Pallet Juniors", battleIds: ["run-1-s1-m1", "run-1-s1-m2"] },
      { season: 2, club: "Cerulean Rookies", battleIds: ["run-1-s2-m1"] },
    ]);
  });
});
