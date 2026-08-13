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

export default function BattleScreen({ runId, battleId, locale, run, onRun }: { runId: string; battleId: string; locale: Locale; run?: CareerRun | null; onRun: (run: CareerRun) => void }) {
  const copy = t(locale);
  const [transcript, setTranscript] = useState<BattleTranscript | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [speed, setSpeed] = useState(2);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    careerApi.battle(runId, battleId).then((value) => {
      if (!active) return;
      setTranscript(value);
      setStepIndex(0);
      careerApi.run(runId).then(onRun).catch(() => undefined);
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

  useEffect(() => {
    if (!complete) return;
    const timer = window.setTimeout(() => navigate(`run/${runId}`), 4200);
    return () => window.clearTimeout(timer);
  }, [complete, runId]);

  if (error) return <section className="battle-error"><h1>{locale === "es" ? "No se pudo abrir el combate" : "Battle unavailable"}</h1><p>{error}</p><button onClick={() => navigate(`run/${runId}`)}>{copy.back}</button></section>;
  if (!transcript || !view) return <BattlePreparing run={run} locale={locale} />;

  const homeTeam = view.combatants.filter((entry) => entry.team === "career-home");
  const awayTeam = view.combatants.filter((entry) => entry.team === "career-away");
  const home = homeTeam.find((entry) => entry.active !== false && entry.hp > 0) ?? homeTeam.find((entry) => entry.active !== false) ?? homeTeam[0];
  const away = awayTeam.find((entry) => entry.active !== false && entry.hp > 0) ?? awayTeam.find((entry) => entry.active !== false) ?? awayTeam[0];
  const userWon = transcript.winner_team === "career-home";
  const commentary = battleCommentary(locale, transcript, view);

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
          <div className={`event-callout ${view.critical ? "critical" : ""} ${view.hit === false ? "miss" : ""}`} key={`${rawEventIndex}-${eventTitle(locale, view)}`}>
            <span>{eventTitle(locale, view)}</span>
            {view.damage > 0 ? <b>−{view.damage} {locale === "es" ? "PS" : "HP"}</b> : null}
          </div>
          {complete ? (
            <div className={`battle-result ${userWon ? "victory" : "defeat"}`} role="status">
              <span>{locale === "es" ? "TEMPORADA RESUELTA" : "SEASON RESOLVED"}</span>
              <h1>{userWon ? (locale === "es" ? "VICTORIA" : "VICTORY") : (locale === "es" ? "DERROTA" : "DEFEAT")}</h1>
              <p>{transcript.winner_label} · {transcript.rounds} {locale === "es" ? "rondas" : "rounds"}</p>
              <CareerCelebration run={run} locale={locale} season={transcript.spec.season} />
              <button className="primary-action" onClick={() => navigate(`run/${runId}`)}>{locale === "es" ? "Continuar la carrera" : "Continue career"}</button>
              <small>{locale === "es" ? "La siguiente temporada se abrirá automáticamente." : "The next season will open automatically."}</small>
            </div>
          ) : null}
        </div>
        <CombatantHud combatant={home} team={homeTeam} club={transcript.spec.home_club} locale={locale} side="home" transcript={transcript} />
      </div>

      <div className="broadcast-lower">
        <div className="commentary-mark"><span>PTU</span><b>{locale === "es" ? "COMENTARIO" : "COMMENTARY"}</b></div>
        <blockquote key={rawEventIndex}>{commentary}</blockquote>
        <div className="playback-controls">
          <span>{Math.min(stepIndex + 1, steps.length + 1)}/{steps.length + 1}</span>
          <button className={speed === 1 ? "active" : ""} aria-pressed={speed === 1} disabled={complete} onClick={() => setSpeed(1)}>1×</button>
          <button className={speed === 2 ? "active" : ""} aria-pressed={speed === 2} disabled={complete} onClick={() => setSpeed(2)}>2×</button>
          <button disabled={complete} onClick={() => setStepIndex(steps.length)}>{copy.skip}</button>
        </div>
      </div>
      <footer className="verification-stamp"><span>✓ {locale === "es" ? "Motor PTU 1.05 · IA táctica en ambos equipos" : "PTU 1.05 engine · tactical AI on both teams"}</span><b>seed {transcript.spec.seed ?? "legacy"} · {transcript.sha256.slice(0, 10)}</b></footer>
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
      <div className="build-row"><span>{combatant.nature || (locale === "es" ? "Naturaleza desconocida" : "Unknown nature")}</span>{combatant.abilities?.map((ability) => <b key={ability}>{ability}</b>)}</div>
      <div className="team-rack" aria-label={`${team.filter((entry) => entry.hp > 0).length} / ${team.length} ${locale === "es" ? "Pokémon disponibles" : "Pokémon available"}`}>
        {team.map((entry) => <span key={entry.id} className={`${entry.hp <= 0 ? "fainted" : ""} ${entry.id === combatant.id ? "active" : ""}`} title={`${entry.species} · ${entry.hp}/${entry.max_hp}`}><PokemonSprite name={entry.species} className="team-sprite" /></span>)}
      </div>
      <dl className="battle-stats">{(["atk", "def", "spatk", "spdef", "spd"] as const).map((key) => <div key={key}><dt>{statLabel(key, locale)}</dt><dd>{stats[key] ?? "—"}</dd></div>)}</dl>
      {combatant.moves?.length ? <div className="move-rack">{combatant.moves.slice(0, 4).map((move) => <span key={move.name}><b>{move.name}</b><small>{move.type} · {move.category}{move.db ? ` · DB ${move.db}` : ""}</small></span>)}</div> : null}
    </aside>
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
