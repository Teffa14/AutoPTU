import { describe, expect, it } from "vitest";

import { eventTitle, seasonPostbattleReview, timelineSeasonDecisions } from "./components/TimelineScreen";

describe("timeline season decisions", () => {
  it("reads the complete decision ledger for an advanced season", () => {
    expect(timelineSeasonDecisions({
      type: "season.completed",
      decisions: [
        { label: "Protect the partner", effects: { health: 2 } },
        { label: "Scout the rival", effects: { scouting: 2, finances: -1 } },
      ],
    })).toEqual([
      { label: "Protect the partner", effects: { health: 2 } },
      { label: "Scout the rival", effects: { scouting: 2, finances: -1 } },
    ]);
  });

  it("keeps old careers readable from their single saved decision", () => {
    expect(timelineSeasonDecisions({ decision: "Train carefully", decision_effects: { development: 2 } })).toEqual([
      { label: "Train carefully", effects: { development: 2 } },
    ]);
  });
});

describe("postbattle review", () => {
  it("turns authoritative season data into a bilingual video-room prompt", () => {
    const entry = {
      type: "season.completed",
      featured_opponent: "Cerulean Current",
      record: "4-2-0",
    };
    expect(seasonPostbattleReview(entry, "es")).toEqual({
      title: "Sala de video · Cerulean Current · 4-2-0",
      prompt: "Compará el plan previo con lo que ocurrió en los combates. Elegí una decisión para repetir y una para corregir.",
    });
    expect(seasonPostbattleReview(entry, "en")?.title).toBe("Video room · Cerulean Current · 4-2-0");
  });

  it("does not invent a review when the authoritative season record is incomplete", () => {
    expect(seasonPostbattleReview({ type: "season.completed", featured_opponent: "Cerulean Current" }, "es")).toBeNull();
    expect(seasonPostbattleReview({ type: "pokemon.captured", featured_opponent: "Cerulean Current", record: "4-2-0" }, "es")).toBeNull();
  });
});

describe("timeline event copy", () => {
  it("uses the correct singular for one gained level", () => {
    expect(eventTitle({ type: "pokemon.trained", species: "Rattata", levels: 1 }, "es")).toBe("Rattata ganó 1 nivel");
  });

  it("explains trainer class effects in the selected language", () => {
    expect(eventTitle({
      type: "class.effect_applied",
      classes: ["Ace Trainer"],
      season_effects: { partner_levels: 1 },
    }, "es")).toBe("Ace Trainer dio +1 nivel al compañero");
  });
});
