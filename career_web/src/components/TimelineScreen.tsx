import { navigate } from "../App";
import type { CareerRun, Locale } from "../types";

interface ReplaySeason {
  season: number;
  club: string;
  battleIds: string[];
}

export function timelineReplaySeasons(run: CareerRun): ReplaySeason[] {
  const archived = run.timeline.flatMap((entry) => {
    const battleIds = Array.isArray(entry.battle_ids)
      ? entry.battle_ids.filter((battleId): battleId is string => typeof battleId === "string" && battleId.length > 0)
      : [];
    if (!battleIds.length) return [];
    return [{
      season: Number(entry.season ?? 0),
      club: String(entry.club ?? entry.label ?? "League fixture"),
      battleIds,
    }];
  });

  if (archived.length) return archived;
  try {
    const cached = JSON.parse(sessionStorage.getItem(`career-battles:${run.id}`) || "[]") as unknown;
    if (!Array.isArray(cached)) return [];
    const battleIds = cached.filter((battleId): battleId is string => typeof battleId === "string" && battleId.length > 0);
    return battleIds.length ? [{
      season: Math.max(1, run.season_number - 1),
      club: run.contract?.club_name ?? "League fixture",
      battleIds,
    }] : [];
  } catch {
    return [];
  }
}

export function TimelineScreen({ run, locale }: { run: CareerRun; locale: Locale }) {
  const replaySeasons = timelineReplaySeasons(run);
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
      {replaySeasons.length ? (
        <section className="replay-archive" aria-labelledby="replay-archive-title">
          <h2 id="replay-archive-title">{locale === "es" ? "Archivo completo de combates" : "Complete battle archive"}</h2>
          {replaySeasons.map((season) => (
            <div className="replay-season" key={`${season.season}-${season.battleIds[0]}`}>
              <header><b>{locale === "es" ? `Temporada ${season.season}` : `Season ${season.season}`}</b><span>{season.club}</span></header>
              <div className="replay-shelf">
                {season.battleIds.map((battleId, index) => (
                  <button key={battleId} onClick={() => navigate(`battle/${run.id}/${battleId}`)}>
                    {locale === "es" ? `Partido ${index + 1}` : `Match ${index + 1}`}<small>{battleId.slice(-8)}</small>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </section>
      ) : null}
    </section>
  );
}
