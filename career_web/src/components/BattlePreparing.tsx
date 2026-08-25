import { useEffect, useState } from "react";

import type { CareerRun, Locale } from "../types";
import { PokemonSprite } from "./PokemonSprite";

const SLOW_BATTLE_WARNING_MS = 12000;

export function BattlePreparing({ run, locale, onRetry, attempt = 0 }: {
  run?: CareerRun | null;
  locale: Locale;
  onRetry?: () => void;
  attempt?: number;
}) {
  const [slow, setSlow] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const activeRoster = Array.isArray(run?.active_roster) ? run.active_roster : [];
  const pokemon = Array.isArray(run?.pokemon) ? run.pokemon : [];
  const lineup = activeRoster.map((id) => pokemon.find((entry) => entry.id === id))
    .filter((entry) => entry !== undefined);

  useEffect(() => {
    setSlow(false);
    setRetrying(false);
    const timer = window.setTimeout(() => setSlow(true), SLOW_BATTLE_WARNING_MS);
    return () => window.clearTimeout(timer);
  }, [attempt]);

  const retry = () => {
    if (retrying || !onRetry) return;
    setRetrying(true);
    onRetry();
  };

  return (
    <section className="battle-preparing" role="status">
      <header><span>{run?.build.region ?? (locale === "es" ? "Liga" : "League")} · {run?.league ?? "league"}</span><b>{run?.contract?.club_name ?? (locale === "es" ? "Tu equipo" : "Your team")}</b></header>
      <div className="preparing-field">
        <div className="field-grid" aria-hidden="true" />
        <div className="team-entry">{lineup.map((pokemon) => <PokemonSprite key={pokemon.id} name={pokemon.species} className="entry-sprite" />)}</div>
        <div className="tunnel-light" aria-hidden="true" />
      </div>
      <div className="preparing-copy"><i /><div><h1>{locale === "es" ? "El equipo ya entra al campo" : "The team is entering the field"}</h1><p>{locale === "es" ? "El motor táctico está cerrando alineaciones y la estrategia rival." : "The tactical engine is locking lineups and opponent strategy."}</p></div></div>
      {slow && onRetry ? (
        <div className="battle-loading-recovery" role="alert">
          <p>{locale === "es" ? "El combate está tardando más de lo normal. Podés reintentar la carga sin registrar una derrota ni recargar toda la carrera." : "The battle is taking longer than expected. You can retry loading without recording a loss or reloading the whole career."}</p>
          <button type="button" onClick={retry} disabled={retrying}>
            {retrying
              ? (locale === "es" ? "Reintentando..." : "Retrying...")
              : (locale === "es" ? "Reintentar carga" : "Retry loading")}
          </button>
        </div>
      ) : null}
    </section>
  );
}
