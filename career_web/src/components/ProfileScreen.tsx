import { useEffect, useMemo, useState } from "react";

import { careerApi } from "../api";
import { readLocalStorage, writeLocalStorage } from "../browserStorage";
import type { CareerPokemon, CareerRun, Locale } from "../types";
import { achievementDescription, achievementLabel } from "../achievementPresentation";
import { EconomyShop } from "./EconomyShop";
import { PokemonSprite } from "./PokemonSprite";
import { TrainerPortrait } from "./TrainerPortrait";

interface Props {
  run: CareerRun;
  locale: Locale;
  onRun: (run: CareerRun) => void;
}

type TrainingPlan = "conditioning" | "power" | "guard" | "agility";

export function ProfileScreen({ run, locale, onRun }: Props) {
  const eligiblePokemon = useMemo(() => run.pokemon.filter(isAvailable), [run.pokemon]);
  const retiredPokemon = useMemo(() => run.pokemon.filter((pokemon) => !isAvailable(pokemon)), [run.pokemon]);
  const defaultTarget = eligiblePokemon.find((pokemon) => pokemon.is_partner)?.id ?? eligiblePokemon[0]?.id ?? "";
  const [selected, setSelected] = useState<string[]>(run.active_roster.filter((id) => eligiblePokemon.some((pokemon) => pokemon.id === id)));
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [itemTarget, setItemTarget] = useState(defaultTarget);
  const [itemStat, setItemStat] = useState("hp");
  const [trainingPlan, setTrainingPlan] = useState<TrainingPlan>(() => storedTrainingPlan(run.id));
  const pokemonById = useMemo(() => new Map(run.pokemon.map((pokemon) => [pokemon.id, pokemon])), [run.pokemon]);
  const selectedSet = useMemo(() => new Set(selected), [selected]);
  const active = selected.map((id) => pokemonById.get(id)).filter(isPokemon).filter(isAvailable);
  const pc = eligiblePokemon.filter((pokemon) => !selectedSet.has(pokemon.id));
  const requiredLineup = Math.min(6, eligiblePokemon.length);
  const trainingCompletedIds = run.season?.training_completed_ids ?? [];
  const trainingCapacity = Math.max(1, run.active_roster.length);

  useEffect(() => setSelected(run.active_roster.filter((id) => eligiblePokemon.some((pokemon) => pokemon.id === id))), [eligiblePokemon, run.active_roster]);
  useEffect(() => {
    if (!eligiblePokemon.some((pokemon) => pokemon.id === itemTarget)) setItemTarget(defaultTarget);
  }, [defaultTarget, eligiblePokemon, itemTarget]);
  useEffect(() => {
    writeLocalStorage(trainingStorageKey(run.id), trainingPlan);
  }, [run.id, trainingPlan]);

  function toggle(pokemon: CareerPokemon) {
    if (!isAvailable(pokemon)) return;
    setMessage("");
    setError("");
    setSelected((current) => {
      if (current.includes(pokemon.id)) return current.filter((id) => id !== pokemon.id);
      return current.length < requiredLineup ? [...current, pokemon.id] : current;
    });
  }

  function chooseBestSix() {
    const partner = eligiblePokemon.find((pokemon) => pokemon.is_partner);
    const ranked = [...eligiblePokemon]
      .filter((pokemon) => pokemon.id !== partner?.id)
      .sort((left, right) => right.level - left.level || right.matches - left.matches || right.career_health - left.career_health || left.species.localeCompare(right.species));
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
      const target = updated.pokemon.find((pokemon) => pokemon.id === itemTarget);
      if (item === "Training Kit" && target) {
        setMessage(target.status === "retired"
          ? (locale === "es" ? `${target.species} llegó al límite de desgaste y se retiró de la competición.` : `${target.species} reached its wear limit and retired from competition.`)
          : (locale === "es" ? `Training Kit aplicado. Vida útil competitiva de ${target.species}: ${target.career_health}%.` : `Training Kit applied. ${target.species} career health: ${target.career_health}%.`));
      } else {
        setMessage(locale === "es" ? `${item} usado. El efecto ya está aplicado.` : `${item} used. Its effect is now applied.`);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="profile-scene">
      <aside className="profile-portrait">
        <TrainerPortrait name={run.build.name} role="scout" className="profile-trainer-portrait" />
        <PokemonSprite name={run.build.starter} className="profile-sprite" />
        <div className="partner-plaque"><small>{locale === "es" ? "Compañero" : "Partner"}</small><b>{run.build.starter}</b></div>
      </aside>

      <article className="trainer-dossier">
        <p className="eyebrow">{locale === "es" ? "Licencia de entrenador" : "Trainer license"} · {run.id.slice(-8)}</p>
        <h1>{run.build.name}</h1>
        <p>{run.contract?.club_name ?? (locale === "es" ? "Independiente" : "Independent")} · {locale === "es" ? `liga ${run.league}` : `${run.league} league`} · {locale === "es" ? "edad" : "age"} {run.age}</p>
        <div className="dossier-stats">
          <span><b>{run.score}</b>{locale === "es" ? "competitivo" : "competitive"}</span>
          <span><b>{run.health}</b>{locale === "es" ? "salud entrenador" : "trainer health"}</span>
          <span><b>{eligiblePokemon.length}</b>{locale === "es" ? "disponibles" : "available"}</span>
          <span><b>{retiredPokemon.length}</b>{locale === "es" ? "retirados" : "retired"}</span>
        </div>

        <section className="squad-room" aria-labelledby="active-squad-title">
          <header>
            <div><p className="eyebrow">{locale === "es" ? "Vestuario del club" : "Club locker room"}</p><h2 id="active-squad-title">{locale === "es" ? "Equipo activo" : "Active team"}</h2></div>
            <span className={selected.length === requiredLineup ? "lineup-count ready" : "lineup-count"}>{selected.length}/{requiredLineup}</span>
          </header>
          <p className="roster-instruction">{locale === "es" ? "El combate usa este equipo. Un Pokémon retirado por desgaste deja de ser elegible y su puesto se libera." : "Battles use this team. A Pokémon retired by wear becomes ineligible and its slot opens."}</p>
          <div className="active-six">
            {active.map((pokemon, index) => <PokemonCard key={pokemon.id} pokemon={pokemon} slot={index + 1} active onClick={() => toggle(pokemon)} locale={locale} />)}
            {Array.from({ length: Math.max(0, 6 - active.length) }, (_, index) => <div className="empty-roster-slot" key={`empty-${index}`}>{pc.length ? (locale === "es" ? "Elegí desde la PC" : "Choose from PC") : (locale === "es" ? "Sin reemplazo disponible" : "No replacement available")}</div>)}
          </div>
          <div className="lineup-actions">
            <button type="button" onClick={chooseBestSix} disabled={!eligiblePokemon.length}>{locale === "es" ? "Elegir mejores seis" : "Choose best six"}</button>
            <button type="button" className="primary-action" onClick={saveLineup} disabled={busy || selected.length !== requiredLineup || !requiredLineup}>{busy ? (locale === "es" ? "Guardando…" : "Saving…") : (locale === "es" ? "Guardar equipo" : "Save team")}</button>
          </div>
          {message ? <p className="lineup-success" role="status">{message}</p> : null}
          {error ? <p className="form-error" role="alert">{error}</p> : null}
        </section>

        <section className="pc-storage" aria-labelledby="pc-title">
          <header><div><p className="eyebrow">{locale === "es" ? "PC regional" : "Regional PC"}</p><h2 id="pc-title">{locale === "es" ? "Pokémon disponibles" : "Available Pokémon"}</h2></div><b>{pc.length}</b></header>
          <p className="roster-instruction">{locale === "es" ? "Los Pokémon en la PC siguen progresando lentamente. Tocá uno para sumarlo al equipo." : "Pokémon in the PC keep progressing slowly. Select one to add it to the team."}</p>
          <div className="pc-grid">{pc.map((pokemon) => <PokemonCard key={pokemon.id} pokemon={pokemon} onClick={() => toggle(pokemon)} locale={locale} disabled={selected.length >= requiredLineup} />)}</div>
        </section>

        {retiredPokemon.length ? <section className="pc-storage retired-storage" aria-label={locale === "es" ? "Pokémon retirados" : "Retired Pokémon"}>
          <header><div><p className="eyebrow">{locale === "es" ? "Archivo médico" : "Medical archive"}</p><h2>{locale === "es" ? "Retirados de competición" : "Retired from competition"}</h2></div><b>{retiredPokemon.length}</b></header>
          <p className="roster-instruction">{locale === "es" ? "Siguen siendo parte de tu carrera, pero ya no pueden entrenar ni competir." : "They remain part of your career history but can no longer train or compete."}</p>
          <div className="pc-grid">{retiredPokemon.map((pokemon) => <PokemonCard key={pokemon.id} pokemon={pokemon} onClick={() => undefined} locale={locale} disabled />)}</div>
        </section> : null}

        <section><h2>{locale === "es" ? "Clases de entrenador" : "Trainer classes"}</h2><div className="class-stamps">{run.class_effects?.adapters?.map((entry) => <span key={entry.class_name} title={locale === "es" ? entry.description_es : entry.description_en}><b>{entry.class_name}</b><small>{locale === "es" ? entry.description_es : entry.description_en}</small></span>)}</div></section>

        <section className="contract-office">
          <h2>{locale === "es" ? "Contrato e ingresos" : "Contract and earnings"}</h2>
          <div className="contract-ledger">
            <span><small>Club</small><b>{run.contract?.club_name ?? (locale === "es" ? "Sin contrato" : "No contract")}</b></span>
            <span><small>{locale === "es" ? "Salario por temporada" : "Salary per season"}</small><b>₽ {run.contract?.salary ?? 0}</b></span>
            <span><small>{locale === "es" ? "Ganado en la carrera" : "Career earnings"}</small><b>₽ {run.career_earnings ?? 0}</b></span>
            <span><small>{locale === "es" ? "Saldo disponible" : "Available balance"}</small><b>₽ {run.money ?? 0}</b></span>
            <span><small>{locale === "es" ? "Temporadas firmadas" : "Seasons secured"}</small><b>{run.contract?.seasons_remaining ?? 0}</b></span>
          </div>
          <p>{locale === "es" ? "Mientras el contrato tenga temporadas restantes seguís en el mismo club. Cuando vence, la pretemporada ofrece extensión si seguís en la misma liga o alternativas para cambiar." : "While the contract has seasons remaining you stay with the same club. When it expires, preseason offers an extension in the same league or alternatives to move."}</p>
          <EconomyShop run={run} locale={locale} onRun={onRun} />
          <div className={run.seasons_without_contract ? "career-warning active" : "career-warning"}>{locale === "es" ? `Advertencias sin contrato: ${run.seasons_without_contract}/2` : `No-contract warnings: ${run.seasons_without_contract}/2`} · {locale === "es" ? `Licencia ${run.license_status === "active" ? "activa" : run.license_status}` : `License ${run.license_status}`}</div>
        </section>

        <section className="training-room">
          <h2>{locale === "es" ? "Plan de entrenamiento automático" : "Automatic training plan"}</h2>
          <p>{locale === "es" ? "Al abrir cada temporada, el plan se aplica automáticamente una vez a cada Pokémon del equipo activo. No tenés que entrar a la mochila ni confirmar sesiones una por una." : "When each season opens, the plan automatically runs once for every active-team Pokémon. No bag visit or one-by-one confirmation is required."}</p>
          <div className="training-controls auto-training-controls">
            <label>{locale === "es" ? "Plan" : "Plan"}<select value={trainingPlan} onChange={(event) => setTrainingPlan(event.target.value as TrainingPlan)}>{Object.entries(TRAINING_METHODS).map(([id, details]) => <option key={id} value={id}>{details[locale === "es" ? 0 : 1]}</option>)}</select></label>
            <div><small>{trainingDescription(trainingPlan, locale)}</small><b>{locale === "es" ? `Progreso esta temporada: ${trainingCompletedIds.length}/${trainingCapacity}` : `This season: ${trainingCompletedIds.length}/${trainingCapacity}`}</b></div>
          </div>
          <small>{locale === "es" ? "El entrenamiento normal no consume vida útil. El Training Kit sí: es una mejora intensiva a cambio de desgaste competitivo permanente." : "Normal training does not consume career health. Training Kits do: they trade intensive gains for permanent competitive wear."}</small>
        </section>

        <section className="bag-room"><h2>{locale === "es" ? "Mochila" : "Bag"}</h2><div className="world-rewards"><span>Poké Ball × {run.build.pokeballs}</span><span>{locale === "es" ? "Escáner Pokédex" : "Pokédex scanner"} LV {run.pokedex_level ?? 0}</span></div>
          {Object.keys(run.inventory ?? {}).length && eligiblePokemon.length ? <div className="item-targeting"><label>{locale === "es" ? "Pokémon objetivo" : "Target Pokémon"}<select value={itemTarget} onChange={(event) => setItemTarget(event.target.value)}>{eligiblePokemon.map((pokemon) => <option key={pokemon.id} value={pokemon.id}>{pokemon.species} · LV {pokemon.level} · {locale === "es" ? "vida útil" : "career health"} {pokemon.career_health}%</option>)}</select></label><label>{locale === "es" ? "Stat para Training Kit" : "Training Kit stat"}<select value={itemStat} onChange={(event) => setItemStat(event.target.value)}>{["hp", "atk", "def", "spatk", "spdef", "spd"].map((stat) => <option key={stat} value={stat}>{pokemonStatLabel(stat, locale)}</option>)}</select></label></div> : null}
          <div className="bag-grid">{Object.entries(run.inventory ?? {}).map(([item, quantity]) => <article key={item} title={itemDescription(item, locale)}><header><b>{item}</b><span>× {quantity}</span></header><p>{itemDescription(item, locale)}</p><button type="button" onClick={() => useInventoryItem(item)} disabled={busy || (!eligiblePokemon.length && itemRequiresPokemon(item))}>{locale === "es" ? "Usar" : "Use"}</button></article>)}</div>
        </section>

        <section className="relationship-section"><h2>{locale === "es" ? "Relaciones" : "Relationships"}</h2>{run.relationship_effects?.best_contact ? <div className="relationship-benefits"><b>{locale === "es" ? "Red activa" : "Active network"}</b><span>+{run.relationship_effects.home_level_bonus ?? 0} LV {locale === "es" ? "en combate" : "in battle"}</span><span>+{run.relationship_effects.season_recovery ?? 0} {locale === "es" ? "salud/temporada" : "health/season"}</span>{run.relationship_effects.contract_guard ? <span>{locale === "es" ? "Seguro de contrato disponible" : "Contract protection available"}</span> : null}</div> : null}
          <div className="relationship-cards">{run.relationship_effects?.contact_effects?.length ? run.relationship_effects.contact_effects.map((contact) => (
            <article key={contact.name} className={`relationship-card role-${contact.role}`} title={relationshipBenefit(contact.benefit, contact.amount, locale)}>
              <TrainerPortrait name={contact.name.split(" · ")[0]} role={contact.role} className="relationship-portrait" />
              <header><div><small>{relationshipRole(contact.role, locale)}</small><b>{contact.name.split(" · ")[0]}</b></div><strong>{contact.bond}/6</strong></header>
              <div className="bond-track"><i style={{ width: `${Math.min(100, contact.bond / 6 * 100)}%` }} /></div>
              <p>{relationshipBenefit(contact.benefit, contact.amount, locale)}</p>
              <small>{contact.next_unlock ? (locale === "es" ? `Próximo beneficio al vínculo ${contact.next_unlock}` : `Next benefit at bond ${contact.next_unlock}`) : (locale === "es" ? "Vínculo máximo" : "Maximum bond")}</small>
            </article>
          )) : <p className="empty-copy">{locale === "es" ? "Todavía no hay vínculos registrados." : "No relationships recorded yet."}</p>}</div>
        </section>
        <section className="achievement-room"><h2>{locale === "es" ? "Logros" : "Achievements"}</h2>{run.achievements.length ? <ul>{run.achievements.map((entry) => <li key={entry} title={achievementDescription(entry, locale)} tabIndex={0}>{achievementLabel(entry, locale)}</li>)}</ul> : <p className="empty-copy">{locale === "es" ? "La primera placa todavía está vacía." : "The first plaque is still empty."}</p>}</section>
      </article>
    </section>
  );
}

function PokemonCard({ pokemon, active = false, slot, disabled = false, onClick, locale }: { pokemon: CareerPokemon; active?: boolean; slot?: number; disabled?: boolean; onClick: () => void; locale: Locale }) {
  const lastEvolution = pokemon.evolution_history.at(-1);
  const retired = !isAvailable(pokemon);
  return (
    <button type="button" className={`roster-card ${active ? "active" : "pc"} ${pokemon.is_partner ? "partner" : ""} ${retired ? "retired" : ""}`} onClick={onClick} disabled={disabled || retired} aria-label={`${pokemon.species}, level ${pokemon.level}`}>
      {slot ? <span className="roster-slot">{slot}</span> : null}
      {pokemon.is_partner ? <span className="partner-pin">★</span> : null}
      <PokemonSprite name={pokemon.species} className="roster-sprite" />
      <strong>{pokemon.species}</strong>
      <span className="pokemon-level">LV {pokemon.level}</span>
      <small>{pokemon.nature || "—"} · {(pokemon.abilities ?? []).join(" / ") || "—"}</small>
      <small>{pokemon.matches} {locale === "es" ? "partidos" : "matches"} · {pokemon.wins} W</small>
      <div className={`pokemon-longevity ${pokemon.career_health <= 24 ? "critical" : pokemon.career_health <= 50 ? "worn" : "healthy"}`} title={locale === "es" ? "Vida útil competitiva. Los Training Kits la reducen en forma permanente." : "Competitive career health. Training Kits reduce it permanently."}><span>{retired ? (locale === "es" ? "RETIRADO" : "RETIRED") : (locale === "es" ? "VIDA ÚTIL" : "CAREER HEALTH")}</span><b>{pokemon.career_health}%</b><i style={{ width: `${Math.max(0, Math.min(100, pokemon.career_health))}%` }} /></div>
      {Object.entries(pokemon.stat_training ?? {}).some(([, value]) => Number(value) > 0) ? <div className="pokemon-training">{Object.entries(pokemon.stat_training).filter(([, value]) => Number(value) > 0).map(([stat, value]) => <b key={stat} title={pokemonStatDescription(stat, locale)}>{pokemonStatLabel(stat, locale)} +{value}</b>)}</div> : null}
      {pokemon.gimmicks?.length ? <div className="pokemon-gimmicks">{pokemon.gimmicks.map((gimmick) => <b key={gimmick} title={gimmickDescription(gimmick, locale)}>✦ {gimmickLabel(gimmick, locale)}</b>)}</div> : null}
      {pokemon.taught_moves?.length ? <em>{pokemon.taught_moves.join(" · ")}</em> : null}
      {lastEvolution ? <em>{lastEvolution.from} → {lastEvolution.to}</em> : null}
    </button>
  );
}

function isPokemon(value: CareerPokemon | undefined): value is CareerPokemon { return Boolean(value); }
function isAvailable(pokemon: CareerPokemon): boolean { return pokemon.status !== "retired" && (pokemon.career_health ?? 100) > 0; }
function trainingStorageKey(runId: string): string { return `autoptu-career-training-plan:${runId}`; }
function storedTrainingPlan(runId: string): TrainingPlan {
  if (typeof window === "undefined") return "conditioning";
  const value = readLocalStorage(trainingStorageKey(runId));
  return value === "power" || value === "guard" || value === "agility" ? value : "conditioning";
}
function itemRequiresPokemon(item: string): boolean { return ["Training Kit", "Exp. Share", "Egg Incubator", "Choice Scarf", "Mega Stone", "Z-Crystal", "Dynamax Band", "Tera Orb"].includes(item); }

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

function pokemonStatDescription(stat: string, locale: Locale): string {
  const descriptions: Record<string, [string, string]> = {
    hp: ["PS: cuánto daño puede soportar antes de debilitarse.", "HP: how much damage it can take before fainting."],
    atk: ["Ataque: potencia de movimientos físicos.", "Attack: power of physical moves."],
    def: ["Defensa: reduce el daño físico recibido.", "Defense: reduces incoming physical damage."],
    spatk: ["Ataque Especial: potencia de movimientos especiales.", "Special Attack: power of special moves."],
    spdef: ["Defensa Especial: reduce el daño especial recibido.", "Special Defense: reduces incoming special damage."],
    spd: ["Velocidad: influye en iniciativa, alcance táctico y orden de acción.", "Speed: affects initiative, tactical reach and action order."],
  };
  return descriptions[stat]?.[locale === "es" ? 0 : 1] ?? stat;
}

function gimmickLabel(gimmick: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = {
    mega_evolution: ["Megaevolución", "Mega Evolution"], z_move: ["Movimiento Z", "Z-Move"],
    dynamax: ["Dynamax", "Dynamax"], terastallization: ["Teracristalización", "Terastallization"],
  };
  return labels[gimmick]?.[locale === "es" ? 0 : 1] ?? gimmick;
}

function gimmickDescription(gimmick: string, locale: Locale): string {
  const descriptions: Record<string, [string, string]> = {
    mega_evolution: ["Una activación por equipo: +2 a Ataque, Defensa, At. Esp., Def. Esp. y Velocidad.", "One team activation: +2 Attack, Defense, Sp. Atk, Sp. Def and Speed."],
    z_move: ["Una activación por equipo: +3 Ataque y +3 Ataque Especial.", "One team activation: +3 Attack and +3 Special Attack."],
    dynamax: ["Una activación por equipo: +8 PS durante el combate.", "One team activation: +8 HP during battle."],
    terastallization: ["Una activación por equipo: mejora ataque y adaptación defensiva.", "One team activation: improves offense and defensive adaptation."],
  };
  return descriptions[gimmick]?.[locale === "es" ? 0 : 1] ?? gimmick;
}

const TRAINING_METHODS: Record<TrainingPlan, [string, string, string, string]> = {
  conditioning: ["Fondo físico", "Conditioning", "+2 PS permanentes.", "+2 permanent HP."],
  power: ["Potencia mixta", "Mixed power", "+1 Ataque y +1 Ataque Especial permanentes.", "+1 permanent Attack and Special Attack."],
  guard: ["Bloque defensivo", "Defensive block", "+1 Defensa y +1 Defensa Especial permanentes.", "+1 permanent Defense and Special Defense."],
  agility: ["Agilidad", "Agility", "+2 Velocidad permanentes.", "+2 permanent Speed."],
};

function trainingDescription(method: TrainingPlan, locale: Locale): string {
  const details = TRAINING_METHODS[method];
  return details[locale === "es" ? 2 : 3];
}

function itemDescription(item: string, locale: Locale): string {
  const descriptions: Record<string, [string, string]> = {
    "Training Kit": ["+2 permanentes al stat elegido. Consume 12 de vida útil competitiva del Pokémon; al llegar a 0 se retira.", "+2 permanent points to the chosen stat. Costs 12 Pokémon career health; at 0 it retires."],
    "Exp. Share": ["+3 niveles al objetivo; evoluciona automáticamente al alcanzar el nivel.", "+3 levels to the target; it evolves automatically at the required level."],
    "Super Potion": ["Recupera 12 de salud de carrera del entrenador.", "Restores 12 trainer career health."],
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
    "Mega Stone": ["Desbloquea Megaevolución para un Pokémon compatible.", "Unlocks Mega Evolution for a compatible Pokémon."],
    "Z-Crystal": ["Desbloquea un Movimiento Z para el objetivo.", "Unlocks a Z-Move for the target."],
    "Dynamax Band": ["Desbloquea Dynamax para el objetivo.", "Unlocks Dynamax for the target."],
    "Tera Orb": ["Desbloquea Teracristalización para el objetivo.", "Unlocks Terastallization for the target."],
  };
  if (item.endsWith(" Charm")) return locale === "es" ? "+1 nivel de escáner Pokédex y +1 scouting." : "+1 Pokédex scanner level and +1 scouting.";
  return descriptions[item]?.[locale === "es" ? 0 : 1] ?? (locale === "es" ? "Objeto utilizable de carrera." : "Usable career item.");
}
