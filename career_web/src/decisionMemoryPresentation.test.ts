import { describe, expect, it } from "vitest";

import { decisionPresentation } from "./decisionPresentation";
import type { CareerDecision, CareerRun } from "./types";

function option(id: string, label: string) {
  return { id, label, description: "stored", risk: "safe" as const, transparency: "full" as const, guaranteed: {}, rewards: [] };
}

function runBase(): CareerRun {
  return {
    id: "memory-scene",
    locale: "es",
    season_number: 4,
    relationships: {},
    timeline: [],
    build: { name: "Ari", region: "kanto", starter: "Rattata", classes: ["Ace Trainer"], pokeballs: 10 },
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
  } as unknown as CareerRun;
}

describe("decision scene callbacks", () => {
  it("brings back a recorded similar choice and an exact known contact", () => {
    const npc = "Misty · mentor · Kanto";
    const run = runBase();
    run.relationships[npc] = 2;
    run.season!.decision_history = [
      { option_id: "health:4:0:1", label: "Recuperación activa", effects: { health: 3 } },
    ];
    const decision = {
      id: "decision:health:4:1",
      family: "health",
      title: "El parte médico vuelve a la mesa",
      body: "Tu salud exige otra decisión.",
      npc_name: npc,
      options: [option("health:4:1:0", "Descanso"), option("health:4:1:1", "Carga reducida"), option("health:4:1:2", "Competir")],
    } as CareerDecision;

    const view = decisionPresentation(decision, run, "es");
    expect(view.body).toContain("temporada 4");
    expect(view.body).toContain("Recuperación activa");
    expect(view.body).toContain("Misty");
    expect(view.body).toContain("vínculo +2");
  });

  it("localizes a remembered option when the UI language changes", () => {
    const run = runBase();
    run.timeline = [
      { type: "season.completed", season: 3, decisions: [{ option_id: "capture:3:0:1", label: "Cambiar la zona de búsqueda" }] },
    ];
    const decision = {
      id: "decision:capture:4:0",
      family: "capture",
      title: "Una pista nueva",
      body: "Hay otra salida disponible.",
      npc_name: "Brock · scout · Kanto",
      options: [option("capture:4:0:0", "Seguir las huellas"), option("capture:4:0:1", "Cambiar la zona de búsqueda"), option("capture:4:0:2", "Ir por la pista difícil")],
    } as CareerDecision;

    const view = decisionPresentation(decision, run, "en");
    expect(view.body).toContain("season 3");
    expect(view.body).toContain("Change the search zone");
    expect(view.body).not.toContain("Cambiar la zona de búsqueda");
  });
});
