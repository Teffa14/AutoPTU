import { describe, expect, it } from "vitest";

import { decisionOutcomeView, isGambleHistoryEntry, normalizedDecisionHistory } from "./decisionOutcome";

describe("decision outcome presentation", () => {
  it("reports only effects and rewards that were actually applied", () => {
    const view = decisionOutcomeView({
      option_id: "capture:2:0:1",
      label: "Cambiar la zona de búsqueda",
      effects: {
        scouting: 2,
        finances: -1,
        rewards: [{ type: "pokemon", species: "Growlithe", rarity: "rare" }],
      },
    }, "es");

    expect(view.choice).toBe("Cambiar la zona de búsqueda");
    expect(view.changes).toContain("Scouting +2");
    expect(view.changes).toContain("Recursos -1");
    expect(view.changes).toContain("Se sumó Growlithe");
    expect(view.changes.join(" ")).not.toContain("hábitat");
  });

  it("distinguishes a failed gamble without inventing a reward", () => {
    const entry = {
      option_id: "training:3:1:2",
      label: "Doblar las sesiones",
      effects: { development: 3, health: -8, reputation: -3, gamble_success: false },
    };
    const view = decisionOutcomeView(entry, "es");

    expect(isGambleHistoryEntry(entry)).toBe(true);
    expect(view.gamble).toBe(true);
    expect(view.headline).toContain("no rindió");
    expect(view.changes).toContain("Desarrollo +3");
    expect(view.changes).toContain("Salud -8");
  });

  it("fails closed when a legacy decision history container is malformed", () => {
    expect(normalizedDecisionHistory(null)).toEqual([]);
    expect(normalizedDecisionHistory("decision:legacy")).toEqual([]);
    expect(normalizedDecisionHistory({ option_id: "training:legacy" })).toEqual([]);
  });

  it("keeps valid decision records while dropping malformed legacy entries", () => {
    const valid = { option_id: "training:3:1:2", label: "Doblar las sesiones", effects: { development: 3 } };
    expect(normalizedDecisionHistory([null, "junk", [], valid])).toEqual([valid]);
  });

  it("does not coerce hostile decision identity fields into visible history", () => {
    const hostile = {
      toString() {
        throw new Error("decision identity coercion should not run");
      },
    };

    expect(() => decisionOutcomeView({
      option_id: hostile as unknown as string,
      label: hostile as unknown as string,
      effects: {},
    }, "es")).not.toThrow();

    const view = decisionOutcomeView({
      option_id: hostile as unknown as string,
      label: hostile as unknown as string,
      effects: {},
    }, "es");
    expect(view.family).toBe("decision");
    expect(view.choice).toBe("Decisión registrada");
  });

  it("ignores malformed rewards instead of rendering or crashing on them", () => {
    expect(() => decisionOutcomeView({
      option_id: "capture:2:0:1",
      label: "Ruta segura",
      effects: {
        scouting: 1,
        rewards: [null, true, { type: "pokemon", species: { name: "Fake" } }],
      },
    }, "es")).not.toThrow();

    const view = decisionOutcomeView({
      option_id: "capture:2:0:1",
      label: "Ruta segura",
      effects: {
        scouting: 1,
        rewards: [null, true, { type: "pokemon", species: { name: "Fake" } }],
      },
    }, "es");
    expect(view.changes).toEqual(["Scouting +1"]);
  });
});
