import { describe, expect, it } from "vitest";

import { eventTitle, seasonPostbattleReview, timelineRenderState, timelineSeasonDecisions } from "./components/TimelineScreen";

describe("timeline legacy save resilience", () => {
  it("fails closed when the career-book collections are malformed", () => {
    expect(timelineRenderState({
      build: null,
      timeline: null,
      pokemon: null,
      achievements: null,
      totals: null,
    })).toEqual({
      trainerName: "",
      starter: "",
      timeline: [],
      pokemonCount: 0,
      evolutions: 0,
      achievements: [],
      totals: { wins: 0, losses: 0, draws: 0, titles: 0 },
    });
  });

  it("keeps valid career history while dropping corrupt entries", () => {
    expect(timelineRenderState({
      build: { name: "  Red Campo  ", starter: " Pikachu " },
      timeline: [null, { type: "season.completed", club: "Pewter Forge" }, "broken"],
      pokemon: [
        null,
        { species: "Pikachu", evolution_history: ["Pichu>Pikachu"] },
        { species: "Eevee", evolution_history: null },
      ],
      achievements: [" First Win ", "", null],
      totals: { wins: 8, losses: "3", draws: Number.NaN, titles: Number.POSITIVE_INFINITY },
    })).toEqual({
      trainerName: "Red Campo",
      starter: "Pikachu",
      timeline: [{ type: "season.completed", club: "Pewter Forge" }],
      pokemonCount: 2,
      evolutions: 1,
      achievements: ["First Win"],
      totals: { wins: 8, losses: 3, draws: 0, titles: 0 },
    });
  });

  it("rejects coercible narrative labels instead of inventing career-book facts", () => {
    const state = timelineRenderState({
      build: {
        name: { toString: () => "Fake Trainer" },
        starter: true,
      },
      achievements: [
        " Real title ",
        null,
        true,
        { toString: () => "Invented title" },
      ],
    });
    expect(state.trainerName).toBe("");
    expect(state.starter).toBe("");
    expect(state.achievements).toEqual(["Real title"]);
  });

  it("rejects coercible non-numeric totals instead of inventing career results", () => {
    expect(timelineRenderState({
      totals: {
        wins: true,
        losses: false,
        draws: { valueOf: () => 4 },
        titles: "2",
      },
    }).totals).toEqual({ wins: 0, losses: 0, draws: 0, titles: 2 });
  });
});

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

  it("drops malformed decision labels instead of coercing them into history", () => {
    expect(timelineSeasonDecisions({
      decisions: [
        { label: "Keep pressure", effects: { scouting: 1 } },
        { label: true, effects: { finances: 2 } },
        { label: { toString: () => "Invented choice" }, effects: { health: 3 } },
      ],
    })).toEqual([
      { label: "Keep pressure", effects: { scouting: 1 } },
    ]);
    expect(timelineSeasonDecisions({
      decision: { toString: () => "Invented legacy choice" },
      decision_effects: { development: 2 },
    })).toEqual([]);
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

  it("does not turn booleans or coercible objects into recorded numeric effects", () => {
    expect(eventTitle({
      type: "relationship.changed",
      name: "Mara · rival",
      amount: true,
    }, "es")).toBe("El vínculo con Mara cambió +0");
    expect(eventTitle({
      type: "class.effect_applied",
      classes: ["Ace Trainer"],
      season_effects: { partner_levels: { valueOf: () => 2 } },
    }, "en")).not.toContain("+2 levels");
  });
});
