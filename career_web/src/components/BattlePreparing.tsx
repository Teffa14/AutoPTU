import type { CareerRun, Locale } from "../types";
import { PokemonSprite } from "./PokemonSprite";

export function BattlePreparing({ run, locale }: { run?: CareerRun | null; locale: Locale }) {
  const lineup = run?.active_roster
    .map((id) => run.pokemon.find((pokemon) => pokemon.id === id))
    .filter((pokemon) => pokemon !== undefined) ?? [];

  return (
    <section className="battle-preparing" role="status">
      <header><span>{run?.build.region ?? "PTU"} · {run?.league ?? "league"}</span><b>{run?.contract?.club_name ?? (locale === "es" ? "Tu equipo" : "Your team")}</b></header>
      <div className="preparing-field">
        <div className="field-grid" aria-hidden="true" />
        <div className="team-entry">{lineup.map((pokemon) => <PokemonSprite key={pokemon.id} name={pokemon.species} className="entry-sprite" />)}</div>
        <div className="tunnel-light" aria-hidden="true" />
      </div>
      <div className="preparing-copy"><i /><div><h1>{locale === "es" ? "El equipo ya entra al campo" : "The team is entering the field"}</h1><p>{locale === "es" ? "El motor PTU está cerrando alineaciones y la IA rival." : "The PTU engine is locking lineups and opponent AI."}</p></div></div>
    </section>
  );
}
