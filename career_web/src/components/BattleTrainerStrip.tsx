import type { CSSProperties } from "react";

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
    <section style={STRIP_STYLE} aria-label={locale === "es" ? "Entrenadores del combate" : "Battle trainers"}>
      <TrainerSide
        align="left"
        club={transcript.spec.home_club}
        name={presentation.home.name}
        sprite={presentation.home.sprite}
        line={presentation.home.line}
      />
      <div style={CENTER_STYLE}>
        <small style={KICKER_STYLE}>{presentation.meetingLabel}</small>
        <strong style={VS_STYLE}>VS</strong>
        <span style={MEETING_STYLE}>{locale === "es" ? "historial formal" : "formal record"}</span>
      </div>
      <TrainerSide
        align="right"
        club={transcript.spec.away_club}
        name={presentation.away.name}
        sprite={presentation.away.sprite}
        line={presentation.away.line}
      />
    </section>
  );
}

function TrainerSide({ align, club, name, sprite, line }: {
  align: "left" | "right";
  club: string;
  name: string;
  sprite: string;
  line: string;
}) {
  const reverse = align === "right";
  return (
    <div style={{ ...SIDE_STYLE, flexDirection: reverse ? "row-reverse" : "row", textAlign: reverse ? "right" : "left" }}>
      <div style={SPRITE_FRAME_STYLE}>
        <img
          src={trainerSpriteUrl(sprite)}
          alt={name}
          style={SPRITE_STYLE}
          loading="eager"
          decoding="async"
        />
      </div>
      <div style={COPY_STYLE}>
        <small style={CLUB_STYLE}>{club}</small>
        <strong style={NAME_STYLE}>{name}</strong>
        <q style={QUOTE_STYLE}>{line}</q>
      </div>
    </div>
  );
}

const STRIP_STYLE: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "minmax(0, 1fr) auto minmax(0, 1fr)",
  alignItems: "stretch",
  gap: 12,
  marginBottom: 10,
};

const SIDE_STYLE: CSSProperties = {
  minWidth: 0,
  display: "flex",
  alignItems: "center",
  gap: 10,
  padding: "8px 12px",
  border: "1px solid rgba(245, 226, 168, 0.22)",
  borderRadius: 14,
  background: "linear-gradient(180deg, rgba(10, 25, 21, 0.94), rgba(5, 13, 11, 0.9))",
};

const SPRITE_FRAME_STYLE: CSSProperties = {
  width: 68,
  height: 68,
  flex: "0 0 68px",
  display: "grid",
  placeItems: "end center",
  overflow: "hidden",
  borderRadius: 10,
  background: "radial-gradient(circle at 50% 85%, rgba(239, 198, 96, 0.2), transparent 62%)",
};

const SPRITE_STYLE: CSSProperties = {
  width: "100%",
  height: "100%",
  objectFit: "contain",
  objectPosition: "center bottom",
  imageRendering: "pixelated",
};

const COPY_STYLE: CSSProperties = {
  minWidth: 0,
  display: "grid",
  gap: 2,
};

const CLUB_STYLE: CSSProperties = {
  color: "rgba(238, 232, 211, 0.66)",
  fontSize: 10,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
};

const NAME_STYLE: CSSProperties = {
  color: "#fff3cf",
  fontSize: 16,
  lineHeight: 1.05,
};

const QUOTE_STYLE: CSSProperties = {
  margin: 0,
  color: "rgba(246, 244, 235, 0.86)",
  fontSize: 12,
  lineHeight: 1.25,
  textDecoration: "none",
};

const CENTER_STYLE: CSSProperties = {
  minWidth: 78,
  display: "grid",
  alignContent: "center",
  justifyItems: "center",
  gap: 1,
  padding: "6px 8px",
};

const KICKER_STYLE: CSSProperties = {
  color: "#e5c267",
  fontSize: 9,
  fontWeight: 800,
  letterSpacing: "0.1em",
};

const VS_STYLE: CSSProperties = {
  color: "#fff4d3",
  fontSize: 23,
  lineHeight: 1,
};

const MEETING_STYLE: CSSProperties = {
  color: "rgba(236, 231, 212, 0.48)",
  fontSize: 8,
  textTransform: "uppercase",
  letterSpacing: "0.08em",
};
