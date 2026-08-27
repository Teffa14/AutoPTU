import { battleTrainerPresentation } from "../battleTrainerPresentation";
import { trainerSpriteUrl } from "../trainerSprites";
import type { BattleTranscript, CareerRun, Locale } from "../types";

export function BattleTrainerStrip({ transcript, run, locale, complete }: {
  transcript: BattleTranscript;
  run?: CareerRun | null;
  locale: Locale;
  complete: boolean;
}) {
  const presentation = battleTrainerPresentation(locale, transcript, run, complete);
  return (
    <section className="battle-trainer-strip" aria-label={locale === "es" ? "Entrenadores del combate" : "Battle trainers"}>
      <TrainerSide
        align="left"
        club={transcript.spec.home_club}
        name={presentation.home.name}
        sprite={presentation.home.sprite}
      />
      <div className="battle-trainer-center" aria-hidden="true">
        <small>{presentation.meetingLabel}</small>
        <strong>VS</strong>
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
