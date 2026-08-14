import { useMemo, useRef, useState } from "react";

import type { Locale } from "../types";
import { PokemonSprite } from "./PokemonSprite";

interface Props {
  starters: string[];
  underdogs: string[];
  value: string;
  locale: Locale;
  name?: string;
  onChange: (species: string) => void;
}

type Filter = "all" | "starter" | "underdog";

export function StarterPicker({ starters, underdogs, value, locale, name = "starter", onChange }: Props) {
  const strip = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const visible = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase();
    return [
      ...(filter !== "underdog" ? starters.map((species) => ({ species, kind: "starter" as const })) : []),
      ...(filter !== "starter" ? underdogs.map((species) => ({ species, kind: "underdog" as const })) : []),
    ].filter((entry) => !needle || entry.species.toLocaleLowerCase().includes(needle));
  }, [filter, query, starters, underdogs]);

  function move(direction: -1 | 1) {
    strip.current?.scrollBy({ left: direction * Math.max(240, strip.current.clientWidth * 0.72), behavior: "smooth" });
  }

  return (
    <div className="starter-picker-shell">
      <div className="starter-picker-tools">
        <div role="group" aria-label={locale === "es" ? "Filtrar compañeros" : "Filter partners"}>
          {(["all", "starter", "underdog"] as Filter[]).map((entry) => (
            <button type="button" key={entry} className={filter === entry ? "active" : ""} aria-pressed={filter === entry} onClick={() => setFilter(entry)}>
              {filterLabel(entry, locale)}
            </button>
          ))}
        </div>
        <label><span className="sr-only">{locale === "es" ? "Buscar Pokémon" : "Search Pokémon"}</span><input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={locale === "es" ? "Buscar por nombre…" : "Search by name…"} /></label>
        <small>{starters.length} starters · {underdogs.length} {locale === "es" ? "underdogs regionales" : "regional underdogs"}</small>
      </div>
      <div className="starter-carousel">
        <button type="button" className="starter-arrow previous" onClick={() => move(-1)} aria-label={locale === "es" ? "Ver Pokémon anteriores" : "See previous Pokémon"}>‹</button>
        <div className="starter-strip" ref={strip} tabIndex={0}>
          {visible.map((entry) => (
            <label key={`${entry.kind}:${entry.species}`} className={value === entry.species ? "starter-card selected" : "starter-card"}>
              <input type="radio" name={name} checked={value === entry.species} onChange={() => onChange(entry.species)} />
              <span className={`partner-kind ${entry.kind}`}>{entry.kind === "starter" ? (locale === "es" ? "Starter regional" : "Regional starter") : (locale === "es" ? "Underdog regional" : "Regional underdog")}</span>
              <PokemonSprite name={entry.species} className="starter-sprite" />
              <b>{entry.species}</b>
            </label>
          ))}
          {!visible.length ? <p className="starter-empty">{locale === "es" ? "No hay coincidencias." : "No matches."}</p> : null}
        </div>
        <button type="button" className="starter-arrow next" onClick={() => move(1)} aria-label={locale === "es" ? "Ver más Pokémon" : "See more Pokémon"}>›</button>
      </div>
    </div>
  );
}

function filterLabel(filter: Filter, locale: Locale) {
  if (filter === "all") return locale === "es" ? "Todos" : "All";
  if (filter === "starter") return "Starters";
  return "Underdogs";
}
