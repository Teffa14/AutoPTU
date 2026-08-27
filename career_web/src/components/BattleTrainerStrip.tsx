import { battleTrainerPresentation } from "../battleTrainerPresentation";
import { loadLocalRun } from "../localCareer";
import { trainerSpriteUrl } from "../trainerSprites";
import type { BattleTranscript, CareerRun, Locale } from "../types";

export function BattleTrainerStrip({ transcript, run, locale, complete }: {
  transcript: BattleTranscript;
  run?: CareerRun | null;
  locale: Locale;
  complete: boolean;
}) {
  const presentationRun = run ?? localRunForBattle(transcript.battle_id);
  const presentation = battleTrainerPresentation(locale, transcript, presentationRun, complete);
  return (
    <section className="battle-trainer-strip" aria-label={locale === "es" ? "Entrenadores del combate" : "Battle trainers"}>
      <TrainerSide
        align="left"
        club={transcript.spec.home_club}
        name={presentation.home.name}
        sprite={presentation.home.sprite}
      />
      <div className="battle-trainer-center">
        <small>{presentation.meetingLabel}</small>
      </div>
      <TrainerSide
        align="right"
        club={transcript.spec.away_club}
        name={presentation.away.name}
        sprite={presentation.away.sprite}
        progression={presentation.away.progression}
      />
    </section>
  );
}

function localRunForBattle(battleId: string): CareerRun | null {
  if (typeof battleId !== "string") return null;
  const match = battleId.match(/^(.*)-s\d+-m\d+$/);
  const runId = match?.[1]?.trim() ?? "";
  return runId ? loadLocalRun(runId) : null;
}

function TrainerSide({ align, club, name, sprite, progression }: {
  align: "left" | "right";
  club: string;
  name: string;
  sprite: string;
  progression?: string;
}) {
  return (
    <div className={`battle-trainer-side ${align}`}>
      <div className="battle-trainer-sprite-frame">
        <img
          src={trainerSpriteUrl(sprite)}
          alt={name}
          className="battle-trainer-sprite"
          loading="eager"
          decoding="async"
        />
      </div>
      <div className="battle-trainer-copy">
        <small>{club}</small>
        <strong>{name}</strong>
        {progression ? <small className="battle-trainer-progression">{progression}</small> : null}
      </div>
    </div>
  );
}
