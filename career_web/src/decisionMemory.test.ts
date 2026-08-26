import { describe, expect, it } from "vitest";

import { decisionMemory } from "./decisionMemory";
import type { CareerRun } from "./types";

function runWith(overrides: Partial<CareerRun>): CareerRun {
  return {
    id: "memory-run",
    season_number: 4,
    relationships: {},
    timeline: [],
    season: {
      number: 4,
      age: 15,
      league: "rookie",
      club_name: "Saffron Comets",
      status: "decision",
      battle_ids: [],
      decisions_required: 3,
      decisions_completed: 1,
      decision_history: [],
      training_completed: false,
      training_method: "",
      training_completed_ids: [],
    },
    ...overrides,
  } as CareerRun;
}

describe("decision memory", () => {
  it("prefers an earlier matching choice from the current season", () => {
    const run = runWith({
      season: {
        ...runWith({}).season!,
        decision_history: [
          { option_id: "health:4:0:1", label: "Recuperación activa", effects: { health: 3 } },
          { option_id: "media:4:1:0", label: "Cerrar el vestuario", effects: { reputation: 1 } },
        ],
      },
    });

    expect(decisionMemory(run, "health").prior).toEqual({
      season: 4,
      optionId: "health:4:0:1",
      label: "Recuperación activa",
    });
  });

  it("recalls the latest matching choice from completed seasons", () => {
    const run = runWith({
      timeline: [
        { type: "season.completed", season: 2, decisions: [{ option_id: "capture:2:0:0", label: "Seguir las huellas" }] },
        { type: "season.completed", season: 3, decisions: [{ option_id: "capture:3:0:1", label: "Cambiar la zona de búsqueda" }] },
      ],
    });

    expect(decisionMemory(run, "capture").prior?.season).toBe(3);
    expect(decisionMemory(run, "capture").prior?.label).toBe("Cambiar la zona de búsqueda");
  });

  it("reports only the exact NPC bond already stored in career state", () => {
    const npc = "Misty · mentor · Kanto";
    const run = runWith({ relationships: { [npc]: 4, "Brock · mentor · Kanto": 6 } });

    expect(decisionMemory(run, "health", npc).contactBond).toBe(4);
    expect(decisionMemory(run, "health", "Erika · mentor · Kanto").contactBond).toBe(0);
  });

  it("does not surface corrupt persisted relationship values as NaN or Infinity", () => {
    const npc = "Misty · mentor · Kanto";
    const corrupt = runWith({ relationships: { [npc]: "not-a-number" } as unknown as CareerRun["relationships"] });
    const overflow = runWith({ relationships: { [npc]: Infinity } });

    expect(decisionMemory(corrupt, "health", npc).contactBond).toBe(0);
    expect(decisionMemory(overflow, "health", npc).contactBond).toBe(0);
  });

  it("does not coerce boolean or object relationship values into authoritative bonds", () => {
    const npc = "Misty · mentor · Kanto";
    const booleanBond = runWith({ relationships: { [npc]: true } as unknown as CareerRun["relationships"] });
    const objectBond = runWith({ relationships: { [npc]: { valueOf: () => 7 } } as unknown as CareerRun["relationships"] });

    expect(decisionMemory(booleanBond, "health", npc).contactBond).toBe(0);
    expect(decisionMemory(objectBond, "health", npc).contactBond).toBe(0);
  });

  it("ignores malformed completed-season decision records instead of manufacturing memories", () => {
    const run = runWith({
      timeline: [
        {
          type: "season.completed",
          season: true,
          decisions: [
            { option_id: { toString: () => "capture:1:0:0" }, label: "Fabricated option" },
            { option_id: "capture:1:0:1", label: { toString: () => "Fabricated label" } },
          ],
        },
      ] as unknown as CareerRun["timeline"],
    });

    expect(decisionMemory(run, "capture").prior).toBeUndefined();
  });
});
