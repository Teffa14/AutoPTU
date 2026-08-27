import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";

import { careerApi } from "../api";
import { navigate } from "../App";
import { battleCommentary, battleOutcomePresentation, deriveBattleView, eventTitle, playbackEventIndexes, statLabel, statusLabel } from "../battlePresentation";
import { t } from "../i18n";
import { opponentAbilityIsRevealed, opponentKnowledgeAtEvent, opponentMoveIsRevealed, type OpponentKnowledge } from "../opponentKnowledge";
import type { BattleCombatant, BattleTranscript, CareerRun, Locale } from "../types";
import { BattleArena } from "./BattleArena";
import { BattlePreparing } from "./BattlePreparing";
import { BattleTrainerStrip } from "./BattleTrainerStrip";
import { CareerCelebration } from "./CareerCelebration";
import { PokemonSprite } from "./PokemonSprite";

export default function BattleScreen({ runId, battleId, locale, run, onRun }: {
  runId: string;
  battleId: string;
  locale: Locale;
  run?: CareerRun | null;
  onRun?: (run: CareerRun) => void;
}) {
  const copy = t(locale);
  const [transcript, setTranscript] = useState<BattleTranscript | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [error, setError] = useState("");
  const [retryAttempt, setRetryAttempt] = useState(0);
  const [finalizing, setFinalizing] = useState(false);
  const [finalizeError, setFinalizeError] = useState("");
  const finalizationRef = useRef<{ key: string; promise: Promise<CareerRun> } | null>(null);

  useEffect(() => {
    let active = true;
    setTranscript(null);
    setError("");
    careerApi.battle(runId, battleId).then((value) => {
      if (!active) return;
      setTranscript(value);
      setStepIndex(0);
    }).catch((reason: Error) => active && setError(reason.message));
    return () => { active = false; };
  }, [runId, battleId, retryAttempt]);

  useEffect(() => {
    if (!transcript) return;
    const key = `${runId}:${battleId}`;
    if (finalizationRef.current?.key !== key) {
      finalizationRef.current = { key, promise: careerApi.finalizeSeason(runId, battleId) };
    }
    let active = true;
    setFinalizing(true);
    setFinalizeError("");
    finalizationRef.current.promise.then((value) => {
      if (!active) return;
      onRun?.(value);
      setFinalizing(false);
    }).catch((reason: Error) => {
      if (!active) return;
      setFinalizeError(reason.message);
      setFinalizing(false);
    });
    return () => { active = false; };
  }, [battleId, onRun, runId, transcript]);

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

  function retryBattleLoading() {
    setTranscript(null);
    setError("");
    setStepIndex(0);
    setRetryAttempt((current) => current + 1);
  }

  async function continueCareer() {
    if (finalizing) return;
    if (finalizeError) {
      setFinalizing(true);
      setFinalizeError("");
      try {
        const value = await careerApi.finalizeSeason(runId, battleId);
        onRun?.(value);
      } catch (reason) {
        setFinalizeError(reason instanceof Error ? reason.message : String(reason));
        setFinalizing(false);
        return;
      }
      setFinalizing(false);
    }
    navigate(`run/${runId}`);
  }

  if (error) return <section className="battle-error"><h1>{locale === "es" ? "No se pudo abrir el combate" : "Battle unavailable"}</h1><p>{error}</p><button onClick={retryBattleLoading}>{locale === "es" ? "Reintentar carga" : "Retry loading"}</button><button onClick={() => navigate(`run/${runId}`)}>{copy.back}</button></section>;
  if (!transcript || !view) return <BattlePreparing run={run} locale={locale} onRetry={retryBattleLoading} attempt={retryAttempt} />;

  const homeTeam = view.combatants.filter((entry) => entry.team === "career-home");
  const awayTeam = view.combatants.filter((entry) => entry.team === "career-away");
  const home = homeTeam.find((entry) => entry.active !== false && entry.hp > 0) ?? homeTeam.find((entry) => entry.active !== false) ?? homeTeam[0];
  const away = awayTeam.find((entry) => entry.active !== false && entry.hp > 0) ?? awayTeam.find((entry) => entry.active !== false) ?? awayTeam[0];
  const awayKnowledge = opponentKnowledgeAtEvent(transcript, rawEventIndex);
  const outcome = battleOutcomePresentation(locale, transcript);
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
        <div><span>{transcript.spec.region} · {locale === "es" ? `liga ${transcript.spec.league}` : `${transcript.spec.league} league`}</span><b>{transcript.spec.home_club} <i>vs</i> {transcript.spec.away_club}</b></div>
        <strong><small>{locale === "es" ? "RONDA" : "ROUND"}</small>{Math.max(1, view.round)}</strong>
      </header>

      <div className="battle-stage">
        <CombatantHud combatant={away} team={awayTeam} club={transcript.spec.away_club} locale={locale} side="away" transcript={transcript} knowledge={awayKnowledge} />
        <div className="arena-wrap">
          <BattleTrainerStrip transcript={transcript} run={run} locale={locale} complete={complete} />
          <BattleArena transcript={transcript} eventIndex={rawEventIndex} view={view} locale={locale} />
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
            <div className={`battle-result ${outcome.kind}`} role="status">
              <span>{adjudicated ? (locale === "es" ? "DECISIÓN ARBITRAL" : "REFEREE DECISION") : (locale === "es" ? "COMBATE TERMINADO" : "BATTLE COMPLETE")}</span>
              <h1>{outcome.title}</h1>
              <p>{outcome.detail}</p>
              <p className="battle-result-explanation">{locale === "es" ? `Potencia efectiva ${homePower}–${awayPower}. El nivel es sólo una parte: stats, tipos, STAB, habilidades, precisión y decisiones tácticas también definieron el resultado.` : `Effective power ${homePower}–${awayPower}. Level is only one part: stats, types, STAB, abilities, accuracy and tactical choices also decided the result.`}</p>
              <CareerCelebration run={run} locale={locale} season={transcript.spec.season} />
              {finalizeError ? <p className="form-error" role="alert">{locale === "es" ? "La temporada no terminó de guardarse. Reintentá para continuar." : "The season did not finish saving. Retry to continue."}</p> : null}
              <button className="primary-action" onClick={continueCareer} disabled={finalizing}>
                {finalizing
                  ? (locale === "es" ? "Cerrando temporada…" : "Finalizing season…")
                  : finalizeError
                  ? (locale === "es" ? "Reintentar y continuar" : "Retry and continue")
                  : (locale === "es" ? "Continuar la carrera" : "Continue career")}
              </button>
              <small>{finalizing ? (locale === "es" ? "El resto del calendario se está resolviendo mientras termina el replay." : "The rest of the schedule is resolving while the replay finishes.") : (locale === "es" ? "Este resultado queda en pantalla hasta que decidas continuar." : "This result remains on screen until you choose to continue.")}</small>
            </div>
          ) : null}
        </div>
        <CombatantHud combatant={home} team={homeTeam} club={transcript.spec.home_club} locale={locale} side="home" transcript={transcript} />
      </div>

      <div className="broadcast-lower">
        <div className="commentary-mark"><span>{locale === "es" ? "EN VIVO" : "LIVE"}</span><b>{locale === "es" ? "COMENTARIO" : "COMMENTARY"}</b></div>
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

function CombatantHud({ combatant, team, club, locale, side, transcript, knowledge }: { combatant?: BattleCombatant; team: BattleCombatant[]; club: string; locale: Locale; side: "home" | "away"; transcript: BattleTranscript; knowledge?: OpponentKnowledge }) {
  if (!combatant) return <aside className={`combatant-hud ${side}`} />;
  const ratio = Math.max(0, Math.min(100, (combatant.hp / Math.max(1, combatant.max_hp)) * 100));
  const stats = { ...fallbackStats(combatant.id, transcript), ...(combatant.stats ?? {}) };
  const level = combatant.level ?? Math.max(1, Number(transcript.spec.level ?? 1) + Number(side === "home" ? transcript.spec.home_level_bonus ?? 0 : transcript.spec.away_level_bonus ?? 0));
  const revealedAbilities = side === "away" && knowledge
    ? (combatant.abilities ?? []).filter((ability) => opponentAbilityIsRevealed(knowledge, combatant.id, ability))
    : combatant.abilities ?? [];
  const revealedMoves = side === "away" && knowledge
    ? (combatant.moves ?? []).filter((move) => opponentMoveIsRevealed(knowledge, combatant.id, move.name))
    : combatant.moves ?? [];
  const revealedTeamCount = side === "away" && knowledge
    ? team.filter((entry) => knowledge.seenCombatantIds.has(entry.id)).length
    : team.filter((entry) => entry.hp > 0).length;
  const teamLabel = side === "away" && knowledge
    ? `${revealedTeamCount} / ${team.length} ${locale === "es" ? "Pokémon rivales revelados" : "opponent Pokémon revealed"}`
    : `${revealedTeamCount} / ${team.length} ${locale === "es" ? "Pokémon disponibles" : "Pokémon available"}`;
  return (
    <aside className={`combatant-hud ${side} ${combatant.hp <= 0 ? "fainted" : ""}`}>
      <header><span>{club}</span><b>{combatant.species}</b><small>LV {level}</small></header>
      <div className="hp-readout"><div><span>{locale === "es" ? "PS" : "HP"}</span><strong>{combatant.hp}<i>/{combatant.max_hp}</i></strong></div><div className="hp-track"><i style={{ "--hp": `${ratio}%` } as CSSProperties} /></div></div>
      <div className="status-row">{combatant.hp <= 0 ? <b>{locale === "es" ? "DEBILITADO" : "FAINTED"}</b> : (combatant.statuses?.length ? combatant.statuses.map((status) => <b key={status}>{statusLabel(status, locale)}</b>) : <span>{locale === "es" ? "Sin estados" : "No status"}</span>)}</div>
      <div className="combatant-types">{combatant.types?.map((type) => <b key={type} className={`type-${type.toLowerCase()}`}>{type}</b>)}</div>
      {combatant.gimmick ? <div className="gimmick-active" title={locale === "es" ? "Gimmick activo: sus bonos ya están incluidos en los stats mostrados." : "Active gimmick: its bonuses are already included in the displayed stats."}>✦ {gimmickBattleLabel(combatant.gimmick, locale)}</div> : null}
      <div className="build-row">
        <span>{side === "home" ? (combatant.nature || (locale === "es" ? "Naturaleza desconocida" : "Unknown nature")) : (locale === "es" ? "Datos observados" : "Observed data")}</span>
        {revealedAbilities.length ? <small>{locale === "es" ? "HABILIDAD" : "ABILITY"}</small> : side === "away" ? <small>{locale === "es" ? "HABILIDAD NO REVELADA" : "ABILITY UNREVEALED"}</small> : null}
        {revealedAbilities.map((ability) => <b key={ability} title={locale === "es" ? "Habilidad revelada por un evento del combate" : "Ability revealed by a battle event"}>{ability}</b>)}
      </div>
      <div className="team-rack" aria-label={teamLabel}>
        {team.map((entry) => {
          if (side === "away" && knowledge && !knowledge.seenCombatantIds.has(entry.id)) {
            return <span key={entry.id} className="unknown" title={locale === "es" ? "Pokémon rival no revelado" : "Unrevealed opponent Pokémon"}>?</span>;
          }
          return <span key={entry.id} className={`${entry.hp <= 0 ? "fainted" : ""} ${entry.id === combatant.id ? "active" : ""}`} title={`${entry.species} · ${entry.hp}/${entry.max_hp}`}><PokemonSprite name={entry.species} className="team-sprite" /></span>;
        })}
      </div>
      {side === "home" ? <dl className="battle-stats">{(["atk", "def", "spatk", "spdef", "spd"] as const).map((key) => {
        const base = stats[key];
        const effective = combatant.effective_stats?.[key];
        return <div key={key} title={battleStatDescription(key, locale)}><dt>{statLabel(key, locale)}</dt><dd className={effective !== undefined && effective !== base ? "modified" : ""}>{effective ?? base ?? "—"}{effective !== undefined && base !== undefined && effective !== base ? <small>{base} base</small> : null}</dd></div>;
      })}</dl> : null}
      {revealedMoves.length ? <div className="move-rack">{revealedMoves.slice(0, 4).map((move) => {
        const stab = combatant.types?.some((type) => type.toLowerCase() === move.type.toLowerCase());
        return <span key={move.name} className={`move-type-${move.type.toLowerCase()}`}><b>{move.name}{stab ? <i>STAB</i> : null}</b><small>{move.type} · {move.category}{move.db ? ` · DB ${move.db}` : ""}</small></span>;
      })}</div> : side === "away" ? <div className="move-rack"><span><b>{locale === "es" ? "MOVIMIENTOS NO REVELADOS" : "MOVES UNREVEALED"}</b><small>{locale === "es" ? "Aparecen cuando se usan" : "Shown when used"}</small></span></div> : null}
    </aside>
  );
}

function gimmickBattleLabel(gimmick: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = {
    mega_evolution: ["MEGAEVOLUCIÓN", "MEGA EVOLUTION"], z_move: ["MOVIMIENTO Z", "Z-MOVE"],
    dynamax: ["DYNAMAX", "DYNAMAX"], terastallization: ["TERACRISTALIZACIÓN", "TERASTALLIZATION"],
  };
  return labels[gimmick]?.[locale === "es" ? 0 : 1] ?? gimmick.toUpperCase();
}

function battleStatDescription(stat: string, locale: Locale): string {
  const descriptions: Record<string, [string, string]> = {
    atk: ["Potencia de los movimientos físicos.", "Power of physical moves."],
    def: ["Reduce el daño físico recibido.", "Reduces incoming physical damage."],
    spatk: ["Potencia de los movimientos especiales.", "Power of special moves."],
    spdef: ["Reduce el daño especial recibido.", "Reduces incoming special damage."],
    spd: ["Define iniciativa y orden de acción.", "Determines initiative and action order."],
  };
  return descriptions[stat]?.[locale === "es" ? 0 : 1] ?? stat;
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
