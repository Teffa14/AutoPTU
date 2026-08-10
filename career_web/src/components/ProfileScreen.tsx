import { useEffect, useMemo, useState } from "react";

import { careerApi } from "../api";
import type { CareerPokemon, CareerRun, Locale } from "../types";
import { PokemonSprite } from "./PokemonSprite";

interface Props {
  run: CareerRun;
  locale: Locale;
  onRun: (run: CareerRun) => void;
}

export function ProfileScreen({ run, locale, onRun }: Props) {
  const [selected, setSelected] = useState<string[]>(run.active_roster);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const pokemonById = useMemo(() => new Map(run.pokemon.map((pokemon) => [pokemon.id, pokemon])), [run.pokemon]);
  const selectedSet = useMemo(() => new Set(selected), [selected]);
  const active = selected.map((id) => pokemonById.get(id)).filter(isPokemon);
  const pc = run.pokemon.filter((pokemon) => !selectedSet.has(pokemon.id));

  useEffect(() => setSelected(run.active_roster), [run.active_roster]);

  function toggle(pokemon: CareerPokemon) {
    setMessage("");
    setError("");
    setSelected((current) => {
      if (current.includes(pokemon.id)) return current.filter((id) => id !== pokemon.id);
      return current.length < 6 ? [...current, pokemon.id] : current;
    });
  }

  function chooseBestSix() {
    const partner = run.pokemon.find((pokemon) => pokemon.is_partner);
    const ranked = [...run.pokemon]
      .filter((pokemon) => pokemon.id !== partner?.id)
      .sort((left, right) => right.level - left.level || right.matches - left.matches || left.species.localeCompare(right.species));
    setSelected([...(partner ? [partner.id] : []), ...ranked.map((pokemon) => pokemon.id)].slice(0, 6));
    setMessage("");
  }

  async function saveLineup() {
    if (selected.length !== 6) return;
    setBusy(true);
    setError("");
    try {
      const updated = await careerApi.lineup(run, selected);
      onRun(updated);
      setMessage(locale === "es" ? "Alineación registrada. Estos seis jugarán el próximo calendario." : "Lineup registered. These six will play the next schedule.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="profile-scene">
      <aside className="profile-portrait">
        <span className="trainer-silhouette" aria-hidden="true">♟</span>
        <PokemonSprite name={run.build.starter} className="profile-sprite" />
        <div className="partner-plaque"><small>{locale === "es" ? "Compañero" : "Partner"}</small><b>{run.build.starter}</b></div>
      </aside>

      <article className="trainer-dossier">
        <p className="eyebrow">{locale === "es" ? "Licencia de entrenador" : "Trainer license"} · {run.id.slice(-8)}</p>
        <h1>{run.build.name}</h1>
        <p>{run.contract?.club_name ?? "Independent"} · {run.league} · {locale === "es" ? "edad" : "age"} {run.age}</p>
        <div className="dossier-stats">
          <span><b>{run.score}</b>{locale === "es" ? "competitivo" : "competitive"}</span>
          <span><b>{run.health}</b>{locale === "es" ? "salud" : "health"}</span>
          <span><b>{run.pokemon.length}</b>{locale === "es" ? "capturados" : "caught"}</span>
          <span><b>{run.pokemon.reduce((total, pokemon) => total + pokemon.evolution_history.length, 0)}</b>{locale === "es" ? "evoluciones" : "evolutions"}</span>
        </div>

        <section className="squad-room" aria-labelledby="active-squad-title">
          <header>
            <div><p className="eyebrow">{locale === "es" ? "Vestuario del club" : "Club locker room"}</p><h2 id="active-squad-title">{locale === "es" ? "Seis titulares" : "Starting six"}</h2></div>
            <span className={selected.length === 6 ? "lineup-count ready" : "lineup-count"}>{selected.length}/6</span>
          </header>
          <p className="roster-instruction">{locale === "es" ? "Cada titular juega por turnos durante la temporada. Toca uno para enviarlo a la PC." : "Each starter rotates through the season. Select one to send it to the PC."}</p>
          <div className="active-six">
            {active.map((pokemon, index) => <PokemonCard key={pokemon.id} pokemon={pokemon} slot={index + 1} active onClick={() => toggle(pokemon)} locale={locale} />)}
            {Array.from({ length: Math.max(0, 6 - active.length) }, (_, index) => <div className="empty-roster-slot" key={`empty-${index}`}>{locale === "es" ? "Elegí desde la PC" : "Choose from PC"}</div>)}
          </div>
          <div className="lineup-actions">
            <button type="button" onClick={chooseBestSix}>{locale === "es" ? "Elegir mejores seis" : "Choose best six"}</button>
            <button type="button" className="primary-action" onClick={saveLineup} disabled={busy || selected.length !== 6}>{busy ? (locale === "es" ? "Guardando…" : "Saving…") : (locale === "es" ? "Guardar alineación" : "Save lineup")}</button>
          </div>
          {message ? <p className="lineup-success" role="status">{message}</p> : null}
          {error ? <p className="form-error" role="alert">{error}</p> : null}
        </section>

        <section className="pc-storage" aria-labelledby="pc-title">
          <header><div><p className="eyebrow">PC regional</p><h2 id="pc-title">{locale === "es" ? "Pokémon disponibles" : "Available Pokémon"}</h2></div><b>{pc.length}</b></header>
          <p className="roster-instruction">{locale === "es" ? "Los Pokémon en la PC siguen entrenando lentamente. Toca uno para subirlo al equipo." : "Pokémon in the PC keep training slowly. Select one to add it to the team."}</p>
          <div className="pc-grid">
            {pc.map((pokemon) => <PokemonCard key={pokemon.id} pokemon={pokemon} onClick={() => toggle(pokemon)} locale={locale} disabled={selected.length >= 6} />)}
          </div>
        </section>

        <section><h2>{locale === "es" ? "Clases PTU" : "PTU classes"}</h2><div className="class-stamps">{run.build.classes.map((name) => <span key={name}>{name}</span>)}</div></section>
        <section><h2>{locale === "es" ? "Logros" : "Achievements"}</h2>{run.achievements.length ? <ul>{run.achievements.map((entry) => <li key={entry}>{entry}</li>)}</ul> : <p className="empty-copy">{locale === "es" ? "La primera placa todavía está vacía." : "The first plaque is still empty."}</p>}</section>
      </article>
    </section>
  );
}

function PokemonCard({ pokemon, active = false, slot, disabled = false, onClick, locale }: { pokemon: CareerPokemon; active?: boolean; slot?: number; disabled?: boolean; onClick: () => void; locale: Locale }) {
  const lastEvolution = pokemon.evolution_history.at(-1);
  return (
    <button type="button" className={`roster-card ${active ? "active" : "pc"} ${pokemon.is_partner ? "partner" : ""}`} onClick={onClick} disabled={disabled} aria-label={`${pokemon.species}, level ${pokemon.level}`}>
      {slot ? <span className="roster-slot">{slot}</span> : null}
      {pokemon.is_partner ? <span className="partner-pin">★</span> : null}
      <PokemonSprite name={pokemon.species} className="roster-sprite" />
      <strong>{pokemon.species}</strong>
      <span className="pokemon-level">LV {pokemon.level}</span>
      <small>{pokemon.matches} {locale === "es" ? "partidos" : "matches"} · {pokemon.wins} W</small>
      {lastEvolution ? <em>{lastEvolution.from} → {lastEvolution.to}</em> : null}
    </button>
  );
}

function isPokemon(value: CareerPokemon | undefined): value is CareerPokemon { return Boolean(value); }
