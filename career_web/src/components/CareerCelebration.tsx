import { achievementLabel } from "../achievementPresentation";
import type { CareerRun, Locale } from "../types";

interface Props {
  run?: CareerRun | null;
  locale: Locale;
  season?: number;
}

export function CareerCelebration({ run, locale, season }: Props) {
  const completed = [...(run?.timeline ?? [])].reverse().find((entry) => (
    entry.type === "season.completed" && (!season || Number(entry.season) === season)
  ));
  if (!completed) return null;
  const achievements = Array.isArray(completed.new_achievements) ? completed.new_achievements.map(String) : [];
  const seasonEvolutions = (run?.timeline ?? []).flatMap((entry) => (
    entry.type === "pokemon.evolved" && Number(entry.season) === Number(completed.season)
      ? [entry]
      : []
  ));
  const rosterEvolutions = Array.isArray(completed.evolutions)
    ? completed.evolutions.flatMap((entry) => entry && typeof entry === "object" ? [entry as Record<string, unknown>] : [])
    : [];
  const evolutions = [...seasonEvolutions, ...rosterEvolutions].filter((entry, index, all) => (
    all.findIndex((candidate) => candidate.pokemon_id === entry.pokemon_id && candidate.to === entry.to) === index
  ));
  const title = completed.title === true;
  const promoted = completed.promoted === true;
  const score = Number(completed.score_delta ?? 0);
  const incident = completed.incident && typeof completed.incident === "object" ? completed.incident as Record<string, unknown> : null;
  const positive = title || promoted || achievements.length > 0 || evolutions.length > 0 || score > 0 || Boolean(incident);

  return (
    <section className={`career-celebration ${positive ? "positive" : "quiet"}`} aria-label={locale === "es" ? "Highlights de temporada" : "Season highlights"}>
      {positive ? <div className="victory-light-rig" aria-hidden="true"><i /><i /><i /><i /></div> : null}
      {positive ? <div className="victory-particles" aria-hidden="true">{Array.from({ length: 18 }, (_, index) => <i key={index} />)}</div> : null}
      <header><span>{locale === "es" ? "HIGHLIGHTS DE TEMPORADA" : "SEASON HIGHLIGHTS"}</span><b>{String(completed.record ?? "—")}</b></header>
      <div className="highlight-ribbon">
        {title ? <strong className="title-highlight">★ {locale === "es" ? "TÍTULO DE LIGA" : "LEAGUE TITLE"}</strong> : null}
        {promoted ? <strong>↑ {locale === "es" ? "ASCENSO" : "PROMOTION"}</strong> : null}
        {score !== 0 ? <strong className={score > 0 ? "score-positive" : "score-negative"}>{score > 0 ? "+" : ""}{score} score</strong> : null}
      </div>
      {evolutions.length ? <div className="evolution-highlights">{evolutions.map((entry, index) => <span key={`${String(entry.to)}-${index}`}><i>✦</i>{String(entry.from)} <b>→ {String(entry.to)}</b><small>LV {String(entry.level)}</small></span>)}</div> : null}
      {incident ? <div className="incident-highlight"><i>✦</i><div><small>{locale === "es" ? "IMPREVISTO" : "UNEXPECTED EVENT"}</small><b>{String(incident[locale === "es" ? "title_es" : "title_en"] ?? "")}</b><p>{String(incident[locale === "es" ? "detail_es" : "detail_en"] ?? "")}</p></div></div> : null}
      {achievements.length ? <div className="achievement-highlights">{achievements.map((entry) => <span key={entry}><i>◆</i><small>{locale === "es" ? "LOGRO" : "ACHIEVEMENT"}</small><b>{achievementLabel(entry, locale)}</b></span>)}</div> : null}
    </section>
  );
}
