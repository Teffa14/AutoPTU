import { describe, expect, it } from "vitest";

import { battleTrainerPresentation } from "./battleTrainerPresentation";
import type { BattleTranscript } from "./types";

const baseTranscript = {
  battle_id: "battle-dialogue-outcome",
  winner_team: "career-home",
  winner_label: "Home",
  rounds: 4,
  sha256: "dialogue-outcome",
  spec: {
    home_club: "Saffron Comets",
    away_club: "Cerulean Current",
    home_species: "Bulbasaur",
    away_species: "Squirtle",
    region: "kanto",
    league: "junior",
    season: 2,
    level: 12,
    away_team_levels: [12],
    difficulty_label: "even",
  },
  events: [],
  initial_state: { round: 1, battle_over: false, combatants: [] },
  final_state: { round: 4, battle_over: true, combatants: [] },
} as BattleTranscript;

describe("battle trainer result dialogue", () => {
  it("keeps draw dialogue neutral instead of presenting the player as defeated", () => {
    const drawTranscript = { ...baseTranscript, winner_team: null } as unknown as BattleTranscript;
    const presentation = battleTrainerPresentation("es", drawTranscript, null, true);

    expect(presentation.home.line).toContain("empate");
    expect(presentation.away.line).toContain("empate");
    expect(presentation.home.line).not.toContain("nos abrió");
    expect(presentation.away.line).not.toContain("vas a tener que cambiar");
  });

  it("treats unknown legacy winner tokens as neutral presentation state", () => {
    const legacyTranscript = { ...baseTranscript, winner_team: "undefined" } as unknown as BattleTranscript;
    const presentation = battleTrainerPresentation("en", legacyTranscript, null, true);

    expect(presentation.home.line.toLowerCase()).toContain("draw");
    expect(presentation.away.line.toLowerCase()).toContain("draw");
    expect(presentation.home.line).not.toContain("opened us up");
    expect(presentation.away.line).not.toContain("you will have to change");
  });
});
