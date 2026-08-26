import { describe, expect, it } from "vitest";

import { battleCommentary, battleOutcomePresentation, deriveBattleView } from "./battlePresentation";
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

  it("maps only the two authoritative team ids to victory and defeat", () => {
    const home = { ...drawTranscript("career-home"), winner_label: "Pewter Forge" };
    const away = { ...drawTranscript("career-away"), winner_label: "Cerulean Current" };

    expect(battleOutcomePresentation("es", home)).toMatchObject({ kind: "victory", title: "VICTORIA" });
    expect(battleOutcomePresentation("es", away)).toMatchObject({ kind: "defeat", title: "DERROTA" });
  });

  it("fails closed to a draw for unknown legacy winner tokens instead of fabricating a loss", () => {
    const malformed = drawTranscript("undefined");

    expect(battleOutcomePresentation("es", malformed)).toMatchObject({
      kind: "draw",
      title: "EMPATE",
      detail: "Pewter Forge vs Cerulean Current · 6 rondas",
    });
  });

  it("does not stringify malformed persisted winner labels into authoritative battle commentary", () => {
    const malformed = {
      ...drawTranscript("career-home"),
      winner_label: { club: "Injected Club" } as unknown as string,
    };

    expect(battleOutcomePresentation("es", malformed)).toMatchObject({
      kind: "victory",
      commentary: "Pewter Forge se lleva la victoria en 6 rondas.",
      detail: "Pewter Forge · 6 rondas",
    });
  });
});
