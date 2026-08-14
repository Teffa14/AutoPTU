import { useEffect, useMemo, useState, type CSSProperties } from "react";

import { careerApi } from "../api";
import { navigate } from "../App";
import { battleCommentary, deriveBattleView, eventTitle, playbackEventIndexes, statLabel, statusLabel } from "../battlePresentation";
import { t } from "../i18n";
import type { BattleCombatant, BattleTranscript, CareerRun, Locale } from "../types";
import { BattleArena } from "./BattleArena";
import { BattlePreparing } from "./BattlePreparing";
import { CareerCelebration } from "./CareerCelebration";
import { PokemonSprite } from "./PokemonSprite";

export default function BattleScreen({ runId, battleId, locale, run }: { runId: string; battleId: string; locale: Locale; run?: CareerRun | null }) {
  const copy = t(locale);
  const [transcript, setTranscript] = useState<BattleTranscript | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    careerApi.battle(runId, battleId).then((value) => {
      if (!active) return;
      setTranscript(value);
      setStepIndex(0);
    }).catch((reason: Error) => active && setError(reason.message));
    return () => { active = false; };
  }, [runId, battleId]);

  const steps = useMemo(() => transcript ? playbackEventIndexes(transcript) : [], [transcript]);
  const complete = Boolean(transcript) && stepIndex >= steps.length;
  const rawEventIndex = transcript ? (complete ? transcript.events.length : steps[stepIndex] ?? transcript.events.length) : 0;
  const view = useMemo(() => transcript ? deriveBattleView(transcript, rawEventIndex) : null, [rawEventIndex, transcript]);

  useEffect(() => {
    if (!transcript || complete) return;
    const delay = view?.event?.type === "round_start" ? 520 : 620;
    const timer = window.setTimeout(() => setStepIndex((current) => current + 1), delay / speed);
    return () => window.clearTimeout(timer);
  }, [complete, speed, transcript, view?.event?.type, stepIndex]);

  if (error) return <section className="battle-error"><h1>{locale === "es" ? "No se pudo abrir el combate" : "Battle unavailable"}</h1><p>{error}</p><button onClick={() => navigate(`run/${runId}`)}>{copy.back}</button></section>;
  if (!transcript || !view) return <BattlePreparing run={run} locale={locale} />;

  const homeTeam = view.combatants.filter((entry) => entry.team === "career-home");
  const awayTeam = view.combatants.filter((entry) => entry.team === "career-away");
  const home = homeTeam.find((entry) => entry.active !== false && entry.hp > 0) ?? homeTeam.find((entry) => entry.active !== false) ?? homeTeam[0];
  const away = awayTeam.find((entry) => entry.active !== false && entry.hp > 0) ?? awayTeam.find((entry) => entry.active !== false) ?? awayTeam[0];
  const userWon = transcript.winner_team === "career-home";
  const commentary = battleCommentary(locale, transcript, view);
  const adjudicated = transcript.events.some((event) => event.type === "match_adjudicated");
  const homePower = battleTeamPower(homeTeam);
  const awayPower = battleTeamPower(awayTeam);
  const calloutClass = [
    "event-callout",
    view.critical ? "critical" : "",
    view.hit === false ? "miss" : "",
    view.effectiveness > 1 ? "super-effective" : "",
    view.effectiveness >= 0 && view.effectiveness < 1 ? "resisted" : "",
    view.knockout ? "knockout" : "",
  ].filter(Boolean).join(" ");

  return (
    <section className={`battle-scene event-${String(view.event?.type ?? "complete")}`}>
      <header className="broadcast-header">
        <button onClick={() => navigate(`run/${runId}`)}>← {locale === "es" ? "Temporada" : "Season"}</button>
        <div><span>{transcript.spec.region} · {transcript.spec.league} league</span><b>{transcript.spec.home_club} <i>vs</i> {transcript.spec.away_club}</b></div>
        <strong><small>{locale === "es" ? "RONDA" : "ROUND"}</small>{Math.max(1, view.round)}</strong>
      </header>

      <div className="battle-stage">
        <CombatantHud combatant={away} team={awayTeam} club={transcript.spec.away_club} locale={locale} side="away" transcript={transcript} />
        <div className="arena-wrap">
          <BattleArena transcript={transcript} eventIndex={rawEventIndex} view={view} />
          <div className={calloutClass} key={`${rawEventIndex}-${eventTitle(locale, view)}`}>
            <span>{eventTitle(locale, view)}</span>
            {view.knockout ? <b>{locale === "es" ? "¡DEBILITADO!" : "FAINTED!"}</b>
              : view.hit === false ? <b>{locale === "es" ? "FALLA" : "MISS"}</b>
              : view.effectiveness === 0 ? <b>{locale === "es" ? "INMUNE" : "IMMUNE"}</b>
              : view.effectiveness > 1 ? <b>{locale === "es" ? "¡MUY EFICAZ!" : "SUPER EFFECTIVE!"} ×{view.effectiveness}</b>
              : view.effectiveness < 1 ? <b>{locale === "es" ? "RESISTIDO" : "RESISTED"} ×{view.effectiveness}</b>
              : view.damage > 0 ? <b>−{view.damage} {locale === "es" ? "PS" : "HP"}</b> : null}
          </div>
          <BattleMechanics transcript={transcript} view={view} locale={locale} />
          {complete ? (
            <div className={`battle-result ${userWon ? "victory" : "defeat"}`} role="status">
              <span>{adjudicated ? (locale === "es" ? "DECISIÓN ARBITRAL" : "REFEREE DECISION") : (locale === "es" ? "COMBATE TERMINADO" : "BATTLE COMPLETE")}</span>
              <h1>{userWon ? (locale === "es" ? "VICTORIA" : "VICTORY") : (locale === "es" ? "DERROTA" : "DEFEAT")}</h1>
              <p>{transcript.winner_label} · {transcript.rounds} {locale === "es" ? "rondas" : "rounds"}</p>
              <p className="battle-result-explanation">{locale === "es" ? `Potencia efectiva ${homePower}–${awayPower}. El nivel es sólo una parte: stats, tipos, STAB, habilidades, precisión y decisiones tácticas también definieron el resultado.` : `Effective power ${homePower}–${awayPower}. Level is only one part: stats, types, STAB, abilities, accuracy and tactical choices also decided the result.`}</p>
              <CareerCelebration run={run} locale={locale} season={transcript.spec.season} />
              <button className="primary-action" onClick={() => navigate(`run/${runId}`)}>{locale === "es" ? "Continuar la carrera" : "Continue career"}</button>
              <small>{locale === "es" ? "Este resultado queda en pantalla hasta que decidas continuar." : "This result remains on screen until you choose to continue."}</small>
            </div>
          ) : null}
        </div>
        <CombatantHud combatant={home} team={homeTeam} club={transcript.spec.home_club} locale={locale} side="home" transcript={transcript} />
      </div>

      <div className="broadcast-lower">
        <div className="commentary-mark"><span>EN VIVO</span><b>{locale === "es" ? "COMENTARIO" : "COMMENTARY"}</b></div>
        <blockquote key={rawEventIndex}>{commentary}</blockquote>
        <div className="playback-controls">
          <span>{Math.min(stepIndex + 1, steps.length + 1)}/{steps.length + 1}</span>
          <button className={speed === 1 ? "active" : ""} aria-pressed={speed === 1} disabled={complete} onClick={() => setSpeed(1)}>1×</button>
          <button className={speed === 2 ? "active" : ""} aria-pressed={speed === 2} disabled={complete} onClick={() => setSpeed(2)}>2×</button>
          <button disabled={complete} onClick={() => setStepIndex(steps.length)}>{copy.skip}</button>
        </div>
      </div>
      <footer className="verification-stamp"><span>✓ {locale === "es" ? "Reglas 1.05 · IA táctica en ambos equipos" : "Rules 1.05 · tactical AI on both teams"}</span><b>seed {transcript.spec.seed ?? "legacy"} · {transcript.sha256.slice(0, 10)}</b></footer>
    </section>
  );
}

function CombatantHud({ combatant, team, club, locale, side, transcript }: { combatant?: BattleCombatant; team: BattleCombatant[]; club: string; locale: Locale; side: "home" | "away"; transcript: BattleTranscript }) {
  if (!combatant) return <aside className={`combatant-hud ${side}`} />;
  const ratio = Math.max(0, Math.min(100, (combatant.hp / Math.max(1, combatant.max_hp)) * 100));
  const stats = { ...fallbackStats(combatant.id, transcript), ...(combatant.stats ?? {}) };
  const level = combatant.level ?? Math.max(1, Number(transcript.spec.level ?? 1) + Number(side === "home" ? transcript.spec.home_level_bonus ?? 0 : transcript.spec.away_level_bonus ?? 0));
  return (
    <aside className={`combatant-hud ${side} ${combatant.hp <= 0 ? "fainted" : ""}`}>
      <header><span>{club}</span><b>{combatant.species}</b><small>LV {level}</small></header>
      <div className="hp-readout"><div><span>{locale === "es" ? "PS" : "HP"}</span><strong>{combatant.hp}<i>/{combatant.max_hp}</i></strong></div><div className="hp-track"><i style={{ "--hp": `${ratio}%` } as CSSProperties} /></div></div>
      <div className="status-row">{combatant.hp <= 0 ? <b>{locale === "es" ? "DEBILITADO" : "FAINTED"}</b> : (combatant.statuses?.length ? combatant.statuses.map((status) => <b key={status}>{statusLabel(status, locale)}</b>) : <span>{locale === "es" ? "Sin estados" : "No status"}</span>)}</div>
      <div className="combatant-types">{combatant.types?.map((type) => <b key={type} className={`type-${type.toLowerCase()}`}>{type}</b>)}</div>
      <div className="build-row"><span>{combatant.nature || (locale === "es" ? "Naturaleza desconocida" : "Unknown nature")}</span>{combatant.abilities?.length ? <small>{locale === "es" ? "HABILIDAD" : "ABILITY"}</small> : null}{combatant.abilities?.map((ability) => <b key={ability} title={locale === "es" ? "Habilidad activa en combate" : "Ability active in battle"}>{ability}</b>)}</div>
      <div className="team-rack" aria-label={`${team.filter((entry) => entry.hp > 0).length} / ${team.length} ${locale === "es" ? "Pokémon disponibles" : "Pokémon available"}`}>
        {team.map((entry) => <span key={entry.id} className={`${entry.hp <= 0 ? "fainted" : ""} ${entry.id === combatant.id ? "active" : ""}`} title={`${entry.species} · ${entry.hp}/${entry.max_hp}`}><PokemonSprite name={entry.species} className="team-sprite" /></span>)}
      </div>
      <dl className="battle-stats">{(["atk", "def", "spatk", "spdef", "spd"] as const).map((key) => {
        const base = stats[key];
        const effective = combatant.effective_stats?.[key];
        return <div key={key}><dt>{statLabel(key, locale)}</dt><dd className={effective !== undefined && effective !== base ? "modified" : ""}>{effective ?? base ?? "—"}{effective !== undefined && base !== undefined && effective !== base ? <small>{base} base</small> : null}</dd></div>;
      })}</dl>
      {combatant.moves?.length ? <div className="move-rack">{combatant.moves.slice(0, 4).map((move) => {
        const stab = combatant.types?.some((type) => type.toLowerCase() === move.type.toLowerCase());
        return <span key={move.name} className={`move-type-${move.type.toLowerCase()}`}><b>{move.name}{stab ? <i>STAB</i> : null}</b><small>{move.type} · {move.category}{move.db ? ` · DB ${move.db}` : ""}</small></span>;
      })}</div> : null}
    </aside>
  );
}

function BattleMechanics({ transcript, view, locale }: { transcript: BattleTranscript; view: ReturnType<typeof deriveBattleView>; locale: Locale }) {
  if (view.event?.type !== "move") return null;
  const actor = transcript.initial_state.combatants.find((entry) => entry.id === view.actorId);
  const target = transcript.initial_state.combatants.find((entry) => entry.id === view.targetId);
  const move = actor?.moves?.find((entry) => entry.name.toLowerCase() === view.move.toLowerCase());
  const special = move?.category.toLowerCase() === "special";
  const context = view.event.context && typeof view.event.context === "object" && !Array.isArray(view.event.context) ? view.event.context as Record<string, unknown> : {};
  const modifiers = Array.isArray(context.modifiers) ? context.modifiers.flatMap((value) => {
    if (!value || typeof value !== "object" || Array.isArray(value)) return [];
    const source = String((value as Record<string, unknown>).source ?? "");
    return source && source !== "Same Type Attack Bonus" ? [source] : [];
  }).slice(0, 2) : [];
  const abilitySources = [view.event.ignition_boosted_by, view.event.aqua_boosted_by].filter(Boolean).map(String);
  return (
    <div className="battle-mechanics" key={`mechanics-${String(view.event?.round)}-${view.move}-${view.damage}`}>
      <div className="mechanic-types"><span>{actor?.types?.join(" / ") || "—"}</span><b>{move?.type || "—"}</b><span>{target?.types?.join(" / ") || "—"}</span></div>
      <div className="mechanic-formula">
        {view.attackValue !== null ? <span>{statLabel(special ? "spatk" : "atk", locale)} <b>{view.attackValue}</b></span> : null}
        {view.defenseValue !== null ? <span>{statLabel(special ? "spdef" : "def", locale)} <b>{view.defenseValue}</b></span> : null}
        {view.effectiveDb !== null ? <span>DB <b>{view.effectiveDb}</b></span> : null}
        {view.stab ? <strong>STAB +2 DB</strong> : null}
        <strong className={view.effectiveness > 1 ? "positive" : view.effectiveness < 1 ? "negative" : ""}>{locale === "es" ? "TIPO" : "TYPE"} ×{view.effectiveness}</strong>
      </div>
      {modifiers.length || abilitySources.length ? <div className="mechanic-modifiers">{[...abilitySources, ...modifiers].map((source) => <span key={source}>{source}</span>)}</div> : null}
    </div>
  );
}

function fallbackStats(id: string, transcript: BattleTranscript): Partial<Record<"atk" | "def" | "spatk" | "spdef" | "spd", number>> {
  const result: Partial<Record<"atk" | "def" | "spatk" | "spdef" | "spd", number>> = {};
  for (const event of transcript.events) {
    if (event.actor === id && typeof event.attack_value === "number") result.atk = Math.max(result.atk ?? 0, event.attack_value);
    if (event.target === id && typeof event.defense_value === "number") result.def = Math.max(result.def ?? 0, event.defense_value);
    if (event.type === "round_start" && Array.isArray(event.initiative)) {
      const entry = event.initiative.find((value) => typeof value === "object" && value !== null && (value as Record<string, unknown>).actor === id) as Record<string, unknown> | undefined;
      if (typeof entry?.speed === "number") result.spd = entry.speed;
    }
  }
  return result;
}

function battleTeamPower(team: BattleCombatant[]): number {
  return Math.round(team.reduce((total, pokemon) => {
    const stats = pokemon.effective_stats ?? pokemon.stats ?? {};
    const statPower = ["atk", "def", "spatk", "spdef", "spd"].reduce((sum, key) => sum + Number(stats[key as keyof typeof stats] ?? 0), 0);
    return total + Number(pokemon.level ?? 1) * 4 + statPower;
  }, 0));
}
