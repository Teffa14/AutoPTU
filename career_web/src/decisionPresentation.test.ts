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

  it("guards dynamic prose that promises unsupported permanent world changes", () => {
    const decision = {
      id: "conservation-es", family: "conservation", title: "El nuevo campo invade una ruta de migración", body: "Seguir cambia el hábitat para siempre.", npc_name: "Erika · owner · Kanto",
      options: [
        { id: "conservation:2:0:0", label: "Detener las obras", description: "legacy", risk: "safe", transparency: "full", guaranteed: { scouting: 1 }, rewards: [] },
        { id: "conservation:2:0:1", label: "Rediseñar", description: "legacy", risk: "calculated", transparency: "full", guaranteed: { scouting: 2, finances: -1 }, rewards: [] },
        { id: "conservation:2:0:2", label: "Seguir", description: "legacy", risk: "gamble", transparency: "estimated", guaranteed: { scouting: 3 }, rewards: [], gamble: { chance: 0.55, success: { reputation: 6 }, failure: { health: -8 } } },
      ],
    } as CareerDecision;
    const run = {
      locale: "es",
      contract: { club_name: "Saffron Comets", salary: 10, seasons_remaining: 1 },
      relationships: {},
      build: { starter: "Rattata" },
    } as CareerRun;
    const view = decisionPresentation(decision, run, "es");
    expect(view.title).toContain("ruta de migración");
    expect(view.body).toContain("Saffron Comets");
    expect(view.body).toContain("todavía no está resuelta");
    expect(view.body).not.toContain("para siempre");
  });

  it("ignores non-finite relationship values when summarizing friendship context", () => {
    const decision = {
      id: "friendship-es", family: "friendship", title: "Un contacto pide tiempo", body: "Texto guardado.", npc_name: "Misty · mentor · Kanto",
      options: [
        { id: "friendship:3:0:0", label: "Escuchar", description: "legacy", risk: "safe", transparency: "full", guaranteed: {}, rewards: [] },
        { id: "friendship:3:0:1", label: "Trabajar juntos", description: "legacy", risk: "calculated", transparency: "full", guaranteed: {}, rewards: [] },
        { id: "friendship:3:0:2", label: "Exigir", description: "legacy", risk: "gamble", transparency: "estimated", guaranteed: {}, rewards: [] },
      ],
    } as CareerDecision;
    const run = {
      locale: "es",
      contract: { club_name: "Saffron Comets", salary: 10, seasons_remaining: 1 },
      relationships: {
        "Misty · mentor · Kanto": Number.NaN,
        "Brock · scout · Kanto": Number.POSITIVE_INFINITY,
        "Erika · owner · Kanto": 7,
      },
      build: { starter: "Rattata" },
    } as CareerRun;

    const view = decisionPresentation(decision, run, "es");
    expect(view.body).toContain("vínculo registrado más alto de tu carrera es 7");
    expect(view.body).not.toContain("NaN");
    expect(view.body).not.toContain("Infinity");
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
