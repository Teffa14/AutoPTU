import { navigate } from "../App";
import type { CareerRun, Locale } from "../types";

export function TimelineScreen({ run, locale }: { run: CareerRun; locale: Locale }) {
  const battles = JSON.parse(sessionStorage.getItem(`career-battles:${run.id}`) || "[]") as string[];
  return (
    <section className="timeline-scene">
      <header><p className="eyebrow">{run.build.name} · career archive</p><h1>{locale === "es" ? "Cada temporada dejó una marca" : "Every season left a mark"}</h1></header>
      <div className="timeline-track">
        {run.timeline.map((entry, index) => (
          <article key={`${String(entry.type)}-${index}`}>
            <div className="timeline-age"><b>{String(entry.age ?? run.age)}</b><small>{locale === "es" ? "años" : "years"}</small></div>
            <div><span>{String(entry.type).replace(".", " / ")}</span><h2>{String(entry.label ?? entry.club ?? entry.reason ?? "Season recorded")}</h2>
              {entry.record ? <p>{String(entry.league)} · {String(entry.record)} · score {Number(entry.score_delta ?? 0) >= 0 ? "+" : ""}{String(entry.score_delta)}</p> : null}</div>
          </article>
        ))}
      </div>
      {battles.length ? <div className="replay-shelf"><h2>{locale === "es" ? "Replays de la última temporada" : "Latest season replays"}</h2>{battles.map((battleId, index) => <button key={battleId} onClick={() => navigate(`battle/${run.id}/${battleId}`)}>Match {index + 1}<small>{battleId.slice(-8)}</small></button>)}</div> : null}
    </section>
  );
}
