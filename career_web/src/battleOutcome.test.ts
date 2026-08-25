import { describe, expect, it } from "vitest";

import { battleCommentary, deriveBattleView } from "./battlePresentation";
import type { BattleTranscript } from "./types";

function drawTranscript(winnerTeam?: string): BattleTranscript {
  return {
    battle_id: "draw-battle",
    rounds: 6,
    sha256: "drawhash",
    ...(winnerTeam === undefined ? {} : { winner_team: winnerTeam }),
    spec: {
      home_club: "Pewter Forge",
      away_club: "Cerulean Current",
      home_species: "Machoke",
      away_species: "Graveler",
      region: "kanto",
      league: "regular",
    },
    initial_state: {
      round: 1,
      battle_over: false,
      combatants: [
        { id: "career-home-1", name: "Machoke", species: "Machoke", team: "career-home", hp: 70, max_hp: 70 },
        { id: "career-away-1", name: "Graveler", species: "Graveler", team: "career-away", hp: 68, max_hp: 68 },
      ],
    },
    final_state: {
      round: 6,
      battle_over: true,
      ...(winnerTeam === undefined ? {} : { winner_team: winnerTeam }),
      combatants: [
        { id: "career-home-1", name: "Machoke", species: "Machoke", team: "career-home", hp: 12, max_hp: 70 },
        { id: "career-away-1", name: "Graveler", species: "Graveler", team: "career-away", hp: 9, max_hp: 68 },
      ],
    },
    events: [{ type: "round_start", round: 1 }],
  };
}

describe("battle outcome presentation", () => {
  it("does not announce a fabricated victory when the authoritative transcript is a draw", () => {
    const transcript = drawTranscript();
    const complete = deriveBattleView(transcript, transcript.events.length);

    expect(battleCommentary("es", transcript, complete)).toBe("El combate termina en empate después de 6 rondas.");
    expect(battleCommentary("en", transcript, complete)).toBe("The battle ends in a draw after 6 rounds.");
  });
});
