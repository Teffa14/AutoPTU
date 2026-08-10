import type { CareerRun, Locale } from "../types";
import { PokemonSprite } from "./PokemonSprite";

export function ProfileScreen({ run, locale }: { run: CareerRun; locale: Locale }) {
  return (
    <section className="profile-scene">
      <div className="profile-portrait">
        <span className="trainer-silhouette" aria-hidden="true">♙</span>
        <PokemonSprite name={run.build.starter} className="profile-sprite" />
        <small>{run.build.region}</small>
      </div>
      <article className="trainer-dossier">
        <p className="eyebrow">League identity · {run.id.slice(-8)}</p>
        <h1>{run.build.name}</h1><p>{run.contract?.club_name ?? "Independent"} · {run.league} · {locale === "es" ? "edad" : "age"} {run.age}</p>
        <div className="dossier-stats"><span><b>{run.score}</b> competitive</span><span><b>{run.health}</b> health</span><span><b>{run.totals.titles}</b> titles</span><span><b>{run.totals.wins}</b> wins</span></div>
        <section><h2>{locale === "es" ? "Clases PTU" : "PTU classes"}</h2><div className="class-stamps">{run.build.classes.map((name) => <span key={name}>{name}</span>)}</div></section>
        <section><h2>{locale === "es" ? "Plantilla personal" : "Personal roster"}</h2><div className="roster-line">{run.roster.map((species) => <figure key={species}><PokemonSprite name={species} className="roster-sprite" /><figcaption>{species}</figcaption></figure>)}</div></section>
        <section><h2>{locale === "es" ? "Logros" : "Achievements"}</h2>{run.achievements.length ? <ul>{run.achievements.map((entry) => <li key={entry}>{entry}</li>)}</ul> : <p className="empty-copy">{locale === "es" ? "La primera placa todavía está vacía." : "The first plaque is still empty."}</p>}</section>
      </article>
    </section>
  );
}
