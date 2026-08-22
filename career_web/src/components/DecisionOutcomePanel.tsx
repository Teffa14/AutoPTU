import type { CSSProperties } from "react";

import { decisionOutcomeView, type DecisionHistoryEntry } from "../decisionOutcome";
import type { Locale } from "../types";

export function DecisionOutcomePanel({ entry, locale, onContinue }: {
  entry: DecisionHistoryEntry;
  locale: Locale;
  onContinue: () => void;
}) {
  const view = decisionOutcomeView(entry, locale);
  return (
    <section style={SHELL_STYLE} aria-live="polite" aria-labelledby="decision-outcome-title">
      <div style={CARD_STYLE}>
        <p style={EYEBROW_STYLE}>{locale === "es" ? "CONSECUENCIA" : "CONSEQUENCE"}</p>
        <h1 id="decision-outcome-title" style={TITLE_STYLE}>{view.headline}</h1>
        <p style={CHOICE_STYLE}><span>{locale === "es" ? "Elegiste" : "You chose"}</span><strong>{view.choice}</strong></p>
        <p style={BODY_STYLE}>{view.body}</p>
        {view.changes.length ? (
          <div style={CHANGES_STYLE} aria-label={locale === "es" ? "Cambios aplicados" : "Applied changes"}>
            <small style={CHANGE_LABEL_STYLE}>{locale === "es" ? "AHORA ES VERDAD EN TU CARRERA" : "NOW TRUE IN YOUR CAREER"}</small>
            <div style={CHIP_ROW_STYLE}>{view.changes.map((change) => <b key={change} style={CHIP_STYLE}>{change}</b>)}</div>
          </div>
        ) : null}
        <button type="button" className="primary-action" onClick={onContinue} style={BUTTON_STYLE}>
          {locale === "es" ? "Seguir con la temporada" : "Continue the season"}
        </button>
        <small style={FOOTNOTE_STYLE}>{locale === "es" ? "La elección queda guardada en el registro de esta temporada." : "The choice remains in this season's record."}</small>
      </div>
    </section>
  );
}

const SHELL_STYLE: CSSProperties = {
  minHeight: "52vh",
  display: "grid",
  placeItems: "center",
  padding: "28px 18px",
};

const CARD_STYLE: CSSProperties = {
  width: "min(720px, 100%)",
  display: "grid",
  gap: 16,
  padding: "26px",
  border: "1px solid rgba(245, 226, 168, 0.28)",
  borderRadius: 18,
  background: "linear-gradient(180deg, rgba(12, 30, 25, 0.97), rgba(5, 15, 13, 0.98))",
  boxShadow: "0 24px 80px rgba(0, 0, 0, 0.32)",
};

const EYEBROW_STYLE: CSSProperties = {
  margin: 0,
  color: "#e5c267",
  fontSize: 11,
  fontWeight: 800,
  letterSpacing: "0.14em",
};

const TITLE_STYLE: CSSProperties = {
  margin: 0,
  color: "#fff3cf",
  fontSize: "clamp(28px, 5vw, 46px)",
  lineHeight: 1,
};

const CHOICE_STYLE: CSSProperties = {
  margin: 0,
  display: "grid",
  gap: 4,
  color: "rgba(241, 237, 221, 0.7)",
};

const BODY_STYLE: CSSProperties = {
  margin: 0,
  maxWidth: 620,
  color: "rgba(247, 244, 233, 0.9)",
  fontSize: 16,
  lineHeight: 1.5,
};

const CHANGES_STYLE: CSSProperties = {
  display: "grid",
  gap: 8,
  padding: "14px 0 4px",
};

const CHANGE_LABEL_STYLE: CSSProperties = {
  color: "rgba(239, 226, 184, 0.62)",
  fontWeight: 800,
  letterSpacing: "0.1em",
};

const CHIP_ROW_STYLE: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
};

const CHIP_STYLE: CSSProperties = {
  padding: "7px 10px",
  borderRadius: 999,
  border: "1px solid rgba(229, 194, 103, 0.28)",
  background: "rgba(229, 194, 103, 0.08)",
  color: "#fff0be",
  fontSize: 12,
};

const BUTTON_STYLE: CSSProperties = {
  justifySelf: "start",
  marginTop: 4,
};

const FOOTNOTE_STYLE: CSSProperties = {
  color: "rgba(238, 232, 211, 0.5)",
};
