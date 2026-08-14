import { useEffect, useMemo, useState } from "react";

import { careerApi } from "../api";
import type { CareerPokemon, CareerRun, Locale } from "../types";
import { achievementLabel } from "../achievementPresentation";
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
  const [itemTarget, setItemTarget] = useState(run.pokemon.find((pokemon) => pokemon.is_partner)?.id ?? run.pokemon[0]?.id ?? "");
  const [itemStat, setItemStat] = useState("hp");
  const [trainingTarget, setTrainingTarget] = useState(run.pokemon.find((pokemon) => pokemon.is_partner)?.id ?? run.pokemon[0]?.id ?? "");
  const [trainingMethod, setTrainingMethod] = useState("conditioning");
  const pokemonById = useMemo(() => new Map(run.pokemon.map((pokemon) => [pokemon.id, pokemon])), [run.pokemon]);
  const selectedSet = useMemo(() => new Set(selected), [selected]);
  const active = selected.map((id) => pokemonById.get(id)).filter(isPokemon);
  const pc = run.pokemon.filter((pokemon) => !selectedSet.has(pokemon.id));
  const requiredLineup = Math.min(6, run.pokemon.length);

  useEffect(() => setSelected(run.active_roster), [run.active_roster]);

  function toggle(pokemon: CareerPokemon) {
    setMessage("");
    setError("");
    setSelected((current) => {
      if (current.includes(pokemon.id)) return current.filter((id) => id !== pokemon.id);
      return current.length < requiredLineup ? [...current, pokemon.id] : current;
    });
  }

  function chooseBestSix() {
    const partner = run.pokemon.find((pokemon) => pokemon.is_partner);
    const ranked = [...run.pokemon]
      .filter((pokemon) => pokemon.id !== partner?.id)
      .sort((left, right) => right.level - left.level || right.matches - left.matches || left.species.localeCompare(right.species));
    setSelected([...(partner ? [partner.id] : []), ...ranked.map((pokemon) => pokemon.id)].slice(0, requiredLineup));
    setMessage("");
  }

  async function saveLineup() {
    if (selected.length !== requiredLineup) return;
    setBusy(true);
    setError("");
    try {
      const updated = await careerApi.lineup(run, selected);
      onRun(updated);
      setMessage(locale === "es" ? "Equipo registrado. Todos jugarán el próximo calendario." : "Team registered. Everyone will play the next schedule.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function useInventoryItem(item: string) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const updated = await careerApi.useItem(run, item, itemTarget, itemStat);
      onRun(updated);
      setMessage(locale === "es" ? `${item} usado. El efecto ya está aplicado.` : `${item} used. Its effect is now applied.`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function completeTraining() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const updated = await careerApi.train(run, trainingMethod, trainingTarget);
      onRun(updated);
      setMessage(locale === "es" ? "Sesión terminada. La mejora es permanente y se usa en combate." : "Session complete. The permanent improvement is used in battle.");
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
            <div><p className="eyebrow">{locale === "es" ? "Vestuario del club" : "Club locker room"}</p><h2 id="active-squad-title">{locale === "es" ? "Equipo activo" : "Active team"}</h2></div>
            <span className={selected.length === requiredLineup ? "lineup-count ready" : "lineup-count"}>{selected.length}/{requiredLineup}</span>
          </header>
          <p className="roster-instruction">{locale === "es" ? "El combate usa todo este equipo y cambia de Pokémon al caer uno. Al capturar más de seis, el resto quedará en la PC." : "Battles use this full team and switch when one faints. Once you catch more than six, the rest stay in the PC."}</p>
          <div className="active-six">
            {active.map((pokemon, index) => <PokemonCard key={pokemon.id} pokemon={pokemon} slot={index + 1} active onClick={() => toggle(pokemon)} locale={locale} />)}
            {Array.from({ length: Math.max(0, 6 - active.length) }, (_, index) => <div className="empty-roster-slot" key={`empty-${index}`}>{run.pokemon.length > active.length ? (locale === "es" ? "Elegí desde la PC" : "Choose from PC") : (locale === "es" ? "Se desbloquea al capturar" : "Unlocked by catching")}</div>)}
          </div>
          <div className="lineup-actions">
            <button type="button" onClick={chooseBestSix}>{locale === "es" ? "Elegir mejores seis" : "Choose best six"}</button>
            <button type="button" className="primary-action" onClick={saveLineup} disabled={busy || selected.length !== requiredLineup}>{busy ? (locale === "es" ? "Guardando…" : "Saving…") : (locale === "es" ? "Guardar equipo" : "Save team")}</button>
          </div>
          {message ? <p className="lineup-success" role="status">{message}</p> : null}
          {error ? <p className="form-error" role="alert">{error}</p> : null}
        </section>

        <section className="pc-storage" aria-labelledby="pc-title">
          <header><div><p className="eyebrow">PC regional</p><h2 id="pc-title">{locale === "es" ? "Pokémon disponibles" : "Available Pokémon"}</h2></div><b>{pc.length}</b></header>
          <p className="roster-instruction">{locale === "es" ? "Los Pokémon en la PC siguen entrenando lentamente. Toca uno para subirlo al equipo." : "Pokémon in the PC keep training slowly. Select one to add it to the team."}</p>
          <div className="pc-grid">
            {pc.map((pokemon) => <PokemonCard key={pokemon.id} pokemon={pokemon} onClick={() => toggle(pokemon)} locale={locale} disabled={selected.length >= requiredLineup} />)}
          </div>
        </section>

        <section><h2>{locale === "es" ? "Clases de entrenador" : "Trainer classes"}</h2><div className="class-stamps">{run.class_effects?.adapters?.map((entry) => <span key={entry.class_name}><b>{entry.class_name}</b><small>{locale === "es" ? entry.description_es : entry.description_en}</small></span>)}</div></section>
        <section className="contract-office">
          <h2>{locale === "es" ? "Contrato e ingresos" : "Contract and earnings"}</h2>
          <div className="contract-ledger">
            <span><small>{locale === "es" ? "Club" : "Club"}</small><b>{run.contract?.club_name ?? (locale === "es" ? "Sin contrato" : "No contract")}</b></span>
            <span><small>{locale === "es" ? "Salario por temporada" : "Salary per season"}</small><b>₽ {run.contract?.salary ?? 0}</b></span>
            <span><small>{locale === "es" ? "Ganado en la carrera" : "Career earnings"}</small><b>₽ {run.career_earnings ?? 0}</b></span>
            <span><small>{locale === "es" ? "Temporadas firmadas" : "Seasons secured"}</small><b>{run.contract?.seasons_remaining ?? 0}</b></span>
          </div>
          <p>{locale === "es" ? "El salario se acredita al cerrar cada calendario y también mejora tus recursos. Dos temporadas consecutivas sin contrato cierran la carrera; una mala temporada muestra primero esta advertencia y un Club Voucher puede extender el vínculo." : "Salary is paid after each calendar and also improves your resources. Two consecutive seasons without a contract end the career; a poor season first shows this warning and a Club Voucher can extend the deal."}</p>
          <div className={run.seasons_without_contract ? "career-warning active" : "career-warning"}>{locale === "es" ? `Advertencias sin contrato: ${run.seasons_without_contract}/2` : `No-contract warnings: ${run.seasons_without_contract}/2`} · {locale === "es" ? `Licencia ${run.license_status}` : `License ${run.license_status}`}</div>
        </section>

        <section className="training-room">
          <h2>{locale === "es" ? "Entrenamiento de temporada" : "Season training"}</h2>
          <p>{locale === "es" ? "Elegí un método y un Pokémon. Se permite una sesión antes de cerrar el calendario; los stats quedan guardados y entran al cálculo real del combate." : "Choose a method and a Pokémon. One session is available before the calendar locks; its stats persist and enter the real battle calculation."}</p>
          <div className="training-controls">
            <select value={trainingTarget} onChange={(event) => setTrainingTarget(event.target.value)}>{run.pokemon.map((pokemon) => <option key={pokemon.id} value={pokemon.id}>{pokemon.species} · LV {pokemon.level}</option>)}</select>
            <select value={trainingMethod} onChange={(event) => setTrainingMethod(event.target.value)}>{Object.entries(TRAINING_METHODS).map(([id, details]) => <option key={id} value={id}>{details[locale === "es" ? 0 : 1]}</option>)}</select>
            <button type="button" className="primary-action" onClick={completeTraining} disabled={busy || run.season?.training_completed || run.season?.status !== "decision"}>{run.season?.training_completed ? (locale === "es" ? "Sesión completada" : "Session complete") : (locale === "es" ? "Entrenar" : "Train")}</button>
          </div>
          <small>{trainingDescription(trainingMethod, locale)}</small>
        </section>

        <section className="bag-room"><h2>{locale === "es" ? "Mochila" : "Bag"}</h2><div className="world-rewards"><span>Poké Ball × {run.build.pokeballs}</span><span>{locale === "es" ? "Escáner Pokédex" : "Pokédex scanner"} LV {run.pokedex_level ?? 0}</span></div>
          {Object.keys(run.inventory ?? {}).length ? <div className="item-targeting"><label>{locale === "es" ? "Pokémon objetivo" : "Target Pokémon"}<select value={itemTarget} onChange={(event) => setItemTarget(event.target.value)}>{run.pokemon.map((pokemon) => <option key={pokemon.id} value={pokemon.id}>{pokemon.species} · LV {pokemon.level}</option>)}</select></label><label>{locale === "es" ? "Stat para Training Kit" : "Training Kit stat"}<select value={itemStat} onChange={(event) => setItemStat(event.target.value)}>{["hp", "atk", "def", "spatk", "spdef", "spd"].map((stat) => <option key={stat} value={stat}>{pokemonStatLabel(stat, locale)}</option>)}</select></label></div> : null}
          <div className="bag-grid">{Object.entries(run.inventory ?? {}).map(([item, quantity]) => <article key={item}><header><b>{item}</b><span>× {quantity}</span></header><p>{itemDescription(item, locale)}</p><button type="button" onClick={() => useInventoryItem(item)} disabled={busy}>{locale === "es" ? "Usar" : "Use"}</button></article>)}</div>
        </section>
        <section className="relationship-section"><h2>{locale === "es" ? "Relaciones" : "Relationships"}</h2>{run.relationship_effects?.best_contact ? <div className="relationship-benefits"><b>{locale === "es" ? "Red activa" : "Active network"}</b><span>+{run.relationship_effects.home_level_bonus ?? 0} LV {locale === "es" ? "en combate" : "in battle"}</span><span>+{run.relationship_effects.season_recovery ?? 0} {locale === "es" ? "salud/temporada" : "health/season"}</span>{run.relationship_effects.contract_guard ? <span>{locale === "es" ? "Seguro de contrato disponible" : "Contract protection available"}</span> : null}</div> : null}
          <div className="relationship-cards">{run.relationship_effects?.contact_effects?.length ? run.relationship_effects.contact_effects.map((contact) => (
            <article key={contact.name} className={`relationship-card role-${contact.role}`}>
              <header><div><small>{relationshipRole(contact.role, locale)}</small><b>{contact.name.split(" · ")[0]}</b></div><strong>{contact.bond}/6</strong></header>
              <div className="bond-track"><i style={{ width: `${Math.min(100, contact.bond / 6 * 100)}%` }} /></div>
              <p>{relationshipBenefit(contact.benefit, contact.amount, locale)}</p>
              <small>{contact.next_unlock ? (locale === "es" ? `Próximo beneficio al vínculo ${contact.next_unlock}` : `Next benefit at bond ${contact.next_unlock}`) : (locale === "es" ? "Vínculo máximo" : "Maximum bond")}</small>
            </article>
          )) : <p className="empty-copy">{locale === "es" ? "Todavía no hay vínculos registrados." : "No relationships recorded yet."}</p>}</div>
        </section>
        <section><h2>{locale === "es" ? "Logros" : "Achievements"}</h2>{run.achievements.length ? <ul>{run.achievements.map((entry) => <li key={entry}>{achievementLabel(entry, locale)}</li>)}</ul> : <p className="empty-copy">{locale === "es" ? "La primera placa todavía está vacía." : "The first plaque is still empty."}</p>}</section>
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
      <small>{pokemon.nature || "—"} · {(pokemon.abilities ?? []).join(" / ") || "—"}</small>
      <small>{pokemon.matches} {locale === "es" ? "partidos" : "matches"} · {pokemon.wins} W</small>
      {Object.entries(pokemon.stat_training ?? {}).some(([, value]) => Number(value) > 0) ? <div className="pokemon-training">{Object.entries(pokemon.stat_training).filter(([, value]) => Number(value) > 0).map(([stat, value]) => <b key={stat}>{pokemonStatLabel(stat, locale)} +{value}</b>)}</div> : null}
      {pokemon.taught_moves?.length ? <em>{pokemon.taught_moves.join(" · ")}</em> : null}
      {lastEvolution ? <em>{lastEvolution.from} → {lastEvolution.to}</em> : null}
    </button>
  );
}

function isPokemon(value: CareerPokemon | undefined): value is CareerPokemon { return Boolean(value); }

function relationshipRole(role: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = { mentor: ["Mentor", "Mentor"], rival: ["Rival", "Rival"], owner: ["Dirección del club", "Club owner"], contact: ["Contacto", "Contact"] };
  return labels[role]?.[locale === "es" ? 0 : 1] ?? role;
}

function relationshipBenefit(benefit: string, amount: number, locale: Locale): string {
  if (benefit === "partner_training") return locale === "es" ? `Entrenamiento guiado: +${amount} al desarrollo del compañero.` : `Guided training: +${amount} partner development.`;
  if (benefit === "rival_read") return locale === "es" ? `Lectura del rival: reduce ${amount} nivel${amount === 1 ? "" : "es"} de preparación enemiga.` : `Opponent read: reduces enemy preparation by ${amount}.`;
  if (benefit === "club_protection") return locale === "es" ? `Respaldo del club: +${amount} recuperación y protección contractual.` : `Club backing: +${amount} recovery and contract protection.`;
  return locale === "es" ? `Apoyo de preparación: +${amount}.` : `Preparation support: +${amount}.`;
}

function pokemonStatLabel(stat: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = { hp: ["PS", "HP"], atk: ["ATQ", "ATK"], def: ["DEF", "DEF"], spatk: ["AT.ESP", "SP.ATK"], spdef: ["DF.ESP", "SP.DEF"], spd: ["VEL", "SPD"] };
  return labels[stat]?.[locale === "es" ? 0 : 1] ?? stat.toUpperCase();
}

const TRAINING_METHODS: Record<string, [string, string, string, string]> = {
  conditioning: ["Fondo físico", "Conditioning", "+2 PS permanentes.", "+2 permanent HP."],
  power: ["Potencia mixta", "Mixed power", "+1 Ataque y +1 Ataque Especial permanentes.", "+1 permanent Attack and Special Attack."],
  guard: ["Bloque defensivo", "Defensive block", "+1 Defensa y +1 Defensa Especial permanentes.", "+1 permanent Defense and Special Defense."],
  agility: ["Agilidad", "Agility", "+2 Velocidad permanentes.", "+2 permanent Speed."],
};

function trainingDescription(method: string, locale: Locale): string {
  const details = TRAINING_METHODS[method] ?? TRAINING_METHODS.conditioning;
  return details[locale === "es" ? 2 : 3];
}

function itemDescription(item: string, locale: Locale): string {
  const descriptions: Record<string, [string, string]> = {
    "Training Kit": ["+2 permanentes al stat elegido del Pokémon objetivo.", "+2 permanent points to the target Pokémon's chosen stat."],
    "Exp. Share": ["+3 niveles al objetivo; evoluciona automáticamente al alcanzar el nivel.", "+3 levels to the target; it evolves automatically at the required level."],
    "Super Potion": ["Recupera 12 de salud de carrera.", "Restores 12 career health."],
    "Pokédex Upgrade": ["Desplaza 3% de encuentros comunes hacia la rareza más alta disponible.", "Shifts 3% of common encounters toward the highest available rarity."],
    "Club Voucher": ["Extiende el contrato y elimina una advertencia sin club.", "Extends the contract and clears a no-club warning."],
    "Press Pass": ["+2 reputación.", "+2 reputation."],
    "Facility Pass": ["+2 desarrollo.", "+2 development."],
    "Choice Scarf": ["+3 Velocidad permanentes al objetivo.", "+3 permanent Speed to the target."],
    "Ranger Kit": ["+2 scouting y 2 Poké Balls.", "+2 scouting and 2 Poké Balls."],
    "Evidence File": ["Protege la licencia y concede +1 reputación.", "Protects the license and grants +1 reputation."],
    "Contest Ribbon": ["+2 reputación.", "+2 reputation."],
    "Egg Incubator": ["+2 niveles al objetivo.", "+2 levels to the target."],
    "Premier Ball": ["Se suma a tus Poké Balls disponibles.", "Adds one available Poké Ball."],
  };
  if (item.endsWith(" Charm")) return locale === "es" ? "+1 nivel de escáner Pokédex y +1 scouting." : "+1 Pokédex scanner level and +1 scouting.";
  return descriptions[item]?.[locale === "es" ? 0 : 1] ?? (locale === "es" ? "Objeto utilizable de carrera." : "Usable career item.");
}
