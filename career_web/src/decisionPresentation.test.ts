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
    expect(transparencyLabel("hidden", "es")).toContain("reveladas");
    expect(effectRule("finances", "es")).toContain("Cada punto de deuda resta 1");
  });

  it("uses the authored run-specific scene when the save and UI language match", () => {
    const decision = {
      id: "dynamic-es", family: "health", title: "Misty cerró la puerta del consultorio", body: "Tu salud está en 41/100 y Saffron Comets tiene que cambiar la semana.", npc_name: "Misty",
      options: [
        { id: "health:1:0:0", label: "Parar cuatro días", description: "legacy", risk: "safe", transparency: "full", guaranteed: { health: 8 }, rewards: [] },
        { id: "health:1:0:1", label: "Trabajar con carga reducida", description: "legacy", risk: "calculated", transparency: "full", guaranteed: { health: 3, development: 2 }, rewards: [] },
        { id: "health:1:0:2", label: "Seguir igual", description: "legacy", risk: "gamble", transparency: "estimated", guaranteed: { health: -2 }, rewards: [], gamble: { chance: 0.55, success: { development: 4 }, failure: { health: -8, reputation: -3 } } },
      ],
    } as CareerDecision;
    const run = { locale: "es", build: { starter: "Rattata" } } as CareerRun;
    const view = decisionPresentation(decision, run, "es");
    expect(view.title).toBe("Misty cerró la puerta del consultorio");
    expect(view.body).toContain("41/100");
    expect(view.options[0].label).toBe("Parar cuatro días");
    expect(view.options[0].description).toContain("Salud +8");
    expect(view.options[2].description).toContain("55% de éxito");
    expect(view.options[2].description).toContain("Salud -8");
  });

  it("localizes decisions from an existing Spanish save when English is selected", () => {
    const decision = {
      id: "stored-es", family: "contest", title: "La invitación del escenario", body: "Un concurso regional.", npc_name: "Brock",
      options: ["Observar", "Preparar", "Apostar"].map((label, index) => ({
        id: `option-${index}`, label, description: "Texto guardado en español", risk: (["safe", "calculated", "gamble"] as const)[index],
        transparency: index === 2 ? "estimated" as const : "full" as const, guaranteed: {}, rewards: [],
      })),
    } as CareerDecision;
    const run = { locale: "es", build: { starter: "Rattata" } } as CareerRun;
    const english = decisionPresentation(decision, run, "en");
    expect(english.title).toBe("An invitation to perform");
    expect(english.options[0].label).toBe("Watch from outside");
    expect(english.body).not.toContain("concurso");
  });
});
