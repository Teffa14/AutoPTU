import { describe, expect, it } from "vitest";

import { decisionPresentation, effectRule, transparencyLabel } from "./decisionPresentation";
import type { CareerDecision, CareerRun } from "./types";

describe("decision information labels", () => {
  it("omits the redundant full-information label", () => {
    expect(transparencyLabel("full", "es")).toBe("");
    expect(transparencyLabel("full", "en")).toBe("");
  });

  it("keeps uncertainty labels and explains immediate debt", () => {
    expect(transparencyLabel("estimated", "es")).toContain("Probabilidad");
    expect(transparencyLabel("hidden", "es")).toContain("ocultas");
    expect(effectRule("finances", "es")).toContain("Cada punto de deuda resta 1");
  });

  it("localizes decisions from an existing Spanish save when English is selected", () => {
    const decision = {
      id: "stored-es", family: "contest", title: "La invitación del escenario", body: "Un concurso regional.", npc_name: "Brock",
      options: ["Observar", "Preparar", "Apostar"].map((label, index) => ({
        id: `option-${index}`, label, description: "Texto guardado en español", risk: (["safe", "calculated", "gamble"] as const)[index],
        transparency: index === 2 ? "estimated" as const : "full" as const, guaranteed: {}, rewards: [],
      })),
    } as CareerDecision;
    const run = { build: { starter: "Rattata" } } as CareerRun;
    const english = decisionPresentation(decision, run, "en");
    expect(english.title).toBe("An invitation to perform");
    expect(english.options[0].label).toBe("Watch from outside");
    expect(english.body).not.toContain("concurso");
  });
});
