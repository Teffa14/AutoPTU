import { useEffect, useMemo, useState, type CSSProperties } from "react";

import { careerApi } from "../api";
import { navigate } from "../App";
import { decisionPresentation, effectLabel, effectRule, riskLabel, transparencyLabel } from "../decisionPresentation";
import { t } from "../i18n";
import type { CareerRun, DecisionOption, DecisionReward, Locale } from "../types";
import { BattlePreparing } from "./BattlePreparing";
import { PokemonSprite } from "./PokemonSprite";

interface Props { run: CareerRun; locale: Locale; onRun: (run: CareerRun) => void }

export function SeasonScreen({ run, locale, onRun }: Props) {
  const copy = t(locale);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [confirmRetire, setConfirmRetire] = useState(false);
  const [shareUrl, setShareUrl] = useState("");
  const [roulette, setRoulette] = useState<"idle" | "spinning" | "settling" | "success" | "failure">("idle");
  const [rouletteOutcome, setRouletteOutcome] = useState<Record<string, unknown> | null>(null);
  const [rouletteOption, setRouletteOption] = useState<DecisionOption | undefined>();
  const [rouletteTarget, setRouletteTarget] = useState<"success" | "failure" | null>(null);
  const [readyBattleId, setReadyBattleId] = useState<string | null>(null);
  const [fieldTransition, setFieldTransition] = useState(false);
  const decision = run.season?.decision;
  const presentation = useMemo(
    () => decision ? decisionPresentation(decision, run, locale) : null,
    [decision, locale, run],
  );
  const selected = presentation?.options.find((option) => option.id === selectedId);
  const finalDecision = Boolean(run.season && run.season.decisions_completed + 1 >= run.season.decisions_required);
  const decisionNumber = (run.season?.decisions_completed ?? 0) + 1;
  const decisionTotal = run.season?.decisions_required ?? 1;
  const lineup = run.active_roster
    .map((id) => run.pokemon.find((pokemon) => pokemon.id === id))
    .filter((pokemon) => pokemon !== undefined);
  const featuredContact = run.relationship_effects?.contact_effects?.[0];

  useEffect(() => setSelectedId(""), [decision?.id]);
  async function decide() {
    if (!selectedId) return;
    const isGamble = selected?.risk === "gamble";
    setBusy(true);
    setError("");
    if (isGamble) {
      setRouletteOutcome(null);
      setRouletteOption(selected);
      setRouletteTarget(null);
      setReadyBattleId(null);
      setRoulette("spinning");
    }
    try {
      const pending = careerApi.decide(run, selectedId);
      if (isGamble) {
        const [result] = await Promise.all([pending, delay(1800)]);
        onRun(result.run);
        const outcome = latestDecisionEffects(result.run);
        const target = outcome?.gamble_success === true ? "success" : "failure";
        setRouletteOutcome(outcome);
        setRouletteTarget(target);
        setReadyBattleId(result.battle_ids.at(-1) ?? null);
        setRoulette("settling");
        await delay(1450);
        setRoulette(target);
        return;
      }
      if (finalDecision) {
        await new Promise((resolve) => window.setTimeout(resolve, 120));
        setFieldTransition(true);
      }
      const result = await pending;
      onRun(result.run);
      const featured = result.battle_ids.at(-1);
      if (featured) navigate(`battle/${run.id}/${featured}`);
    } catch (reason) {
      setFieldTransition(false);
      setRoulette("idle");
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally { setBusy(false); }
  }

  function continueAfterRoulette() {
    const featured = readyBattleId;
    setRoulette("idle");
    setRouletteOutcome(null);
    setRouletteOption(undefined);
    setRouletteTarget(null);
    setReadyBattleId(null);
    if (!featured) return;
    setFieldTransition(true);
    window.setTimeout(() => navigate(`battle/${run.id}/${featured}`), 420);
  }

  async function retire() {
    setBusy(true);
    try { onRun(await careerApi.retire(run.id)); setConfirmRetire(false); }
    catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setBusy(false); }
  }

  async function share() {
    setBusy(true);
    try { setShareUrl((await careerApi.share(run.id)).url); }
    catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setBusy(false); }
  }

  if (run.status === "retired") return (
    <section className="retirement-scene">
      <p className="eyebrow">Career record sealed</p><h1>{run.build.name}</h1>
      <p>{locale === "es" ? `Se retiró a los ${run.age}. La liga conserva el registro.` : `Retired at ${run.age}. The league keeps the record.`}</p>
      <div className="retirement-score"><b>{run.score}</b><span>{copy.score}</span></div>
      <div className="record-ribbon"><span>{run.totals.wins} W</span><span>{run.totals.losses} L</span><span>{run.totals.titles} titles</span></div>
      <div className="retirement-roster"><span><b>{run.summary?.pokemon_owned ?? run.pokemon.length}</b> Pokémon</span><span><b>{run.summary?.evolutions ?? 0}</b> {locale === "es" ? "evoluciones" : "evolutions"}</span></div>
      <button className="primary-action" onClick={() => navigate(`timeline/${run.id}`)}>{copy.timeline}</button>
      <div className="share-actions"><button onClick={() => navigate("")}>{locale === "es" ? "Nueva historia" : "New story"}</button><button onClick={share} disabled={busy}>{locale === "es" ? "Compartir resumen" : "Share summary"}</button></div>
      {shareUrl ? <output className="share-url"><a href={`${window.location.origin}${shareUrl}`} target="_blank" rel="noreferrer">{window.location.origin}{shareUrl}</a></output> : null}
      {error ? <p className="form-error" role="alert">{error}</p> : null}
    </section>
  );

  if (fieldTransition) return (
    <BattlePreparing run={run} locale={locale} />
  );

  return (
    <section className="season-scene">
      <div className="season-sky" aria-hidden="true" />
      {roulette !== "idle" ? (
        <RouletteOverlay
          state={roulette}
          target={rouletteTarget}
          locale={locale}
          option={rouletteOption}
          outcome={rouletteOutcome}
          hasBattle={Boolean(readyBattleId)}
          onContinue={continueAfterRoulette}
        />
      ) : null}
      <header className="season-scoreboard">
        <div><span>{copy.season} {run.season_number}</span><b>{run.contract?.club_name ?? "Independent"}</b><small>{run.league} league · age {run.age}</small></div>
        <div className="scoreboard-metrics"><span><i style={{ "--meter": `${run.health}%` } as CSSProperties} />{copy.health} <b>{run.health}</b></span><span>{copy.score} <b>{run.score}</b></span></div>
      </header>

      <div className="career-attributes" aria-label={locale === "es" ? "Estado de carrera" : "Career state"}>
        {(["development", "scouting", "finances", "reputation"] as const).map((key) => (
          <div key={key} title={effectRule(key, locale)}>
            <span>{effectLabel(key, locale)}</span><b>{signed(run[key])}</b><small>{attributeHint(key, run[key], locale)}</small>
          </div>
        ))}
      </div>
      <div className="active-class-effect">{run.class_effects?.adapters?.map((entry) => <span key={entry.class_name}><b>{entry.class_name}</b> · {locale === "es" ? entry.description_es : entry.description_en}</span>)}</div>
      {run.relationship_effects?.best_contact ? (
        <div className="relationship-edge" aria-label={locale === "es" ? "Beneficios de relaciones" : "Relationship benefits"}>
          <span><b>{run.relationship_effects.best_contact.split(" · ")[0]}</b>{locale === "es" ? " está de tu lado" : " has your back"}{featuredContact ? <i>{relationshipRoleLabel(featuredContact.role, locale)} · {featuredContact.bond}/6</i> : null}</span>
          <small>{featuredContact ? relationshipEdgeBenefit(featuredContact.benefit, featuredContact.amount, locale) : `+${run.relationship_effects.home_level_bonus ?? 0} LV`}{run.relationship_effects.contract_guard ? ` · ${locale === "es" ? "protege un contrato" : "protects one contract"}` : ""}</small>
        </div>
      ) : null}

      <div className="season-stage">
        <aside className="partner-stand squad-stand">
          <div className="sprite-halo"><PokemonSprite name={run.build.starter} className="partner-sprite" /></div>
          <p>{locale === "es" ? "capitán del equipo" : "team captain"}</p><h2>{run.build.starter}</h2>
          <span>{run.build.pokeballs} Poké Balls · {run.pokemon.length} {locale === "es" ? "capturados" : "caught"}</span>
          <div className="season-lineup" aria-label={locale === "es" ? "Alineación activa" : "Active lineup"}>
            {lineup.map((pokemon) => (
              <div key={pokemon.id} title={`${pokemon.species} · LV ${pokemon.level}`}>
                <PokemonSprite name={pokemon.species} className="lineup-sprite" />
                <small>LV {pokemon.level}</small>
              </div>
            ))}
          </div>
          <button type="button" className="manage-squad" onClick={() => navigate(`profile/${run.id}`)}>{locale === "es" ? "Gestionar equipo y PC" : "Manage team and PC"}</button>
          <div className="partner-preparation"><span>{locale === "es" ? "Ventaja de preparación" : "Preparation edge"}</span><b>{preparationEdge(run) >= 0 ? "+" : ""}{preparationEdge(run)} LV</b></div>
        </aside>

        <article className="decision-ticket">
          <div className="ticket-notch top" /><div className="ticket-notch bottom" />
          <header className="decision-brief">
            <div><span>{locale === "es" ? "QUIÉN" : "WHO"}</span><b>{decision?.npc_name?.split(" · ")[0] ?? "League staff"}</b></div>
            <div><span>{locale === "es" ? "OPORTUNIDAD" : "OPPORTUNITY"}</span><b>{decision ? familyLabel(decision.family, locale) : "—"}</b></div>
            <div><span>{locale === "es" ? "DECISIÓN" : "DECISION"}</span><b>{run.season ? `${run.season.decisions_completed + 1}/${run.season.decisions_required}` : "—"}</b></div>
          </header>
          <p className="eyebrow">{locale === "es" ? "Antes del calendario" : "Before the schedule"}</p>
          <h1>{presentation?.title}</h1><p className="decision-body">{presentation?.body}</p>

          <div className="decision-options" role="radiogroup" aria-label={locale === "es" ? "Opciones de decisión" : "Decision options"}>
            {presentation?.options.map((option, index) => (
              <button
                key={option.id}
                className={selectedId === option.id ? "selected" : ""}
                onClick={() => setSelectedId(option.id)}
                disabled={busy}
                role="radio"
                aria-checked={selectedId === option.id}
              >
                <span className={`choice-number ${option.risk}`}>{String(index + 1).padStart(2, "0")}</span>
                <span className="choice-copy"><small className={`risk ${option.risk}`}>{riskLabel(option.risk, locale)}</small><b>{option.label}</b><p>{option.description}</p></span>
                <span className="choice-effects"><span className="choice-rewards">{rewardChips(option.risk === "gamble" ? option.gamble?.success_rewards ?? [] : option.rewards ?? [], locale)}</span>{effectChips(option.guaranteed, locale)}<small>{transparencyLabel(option.transparency, locale)}</small></span>
              </button>
            ))}
          </div>

          {selected ? (
            <section className={`decision-confirmation ${selected.risk}`} aria-live="polite">
              <div>
                <span>{selected.risk === "gamble" ? (locale === "es" ? "PREMIO DE LA RULETA" : "ROULETTE PRIZE") : (locale === "es" ? "RECIBIRÁS" : "YOU RECEIVE")}</span>
                <strong>{rewardSentence(selected.risk === "gamble" ? selected.gamble?.success_rewards ?? [] : selected.rewards ?? [], locale) || effectSentence(selected.guaranteed, locale)}</strong>
                {selected.risk !== "gamble" && (selected.rewards?.length ?? 0) > 0 ? <p>{locale === "es" ? "Además:" : "Also:"} {effectSentence(selected.guaranteed, locale)}</p> : null}
                {selected.gamble?.chance ? (
                  <p><b>{Math.round(selected.gamble.chance * 100)}%</b> {locale === "es" ? "de éxito." : "success chance."} {gambleSentence(selected, locale)}</p>
                ) : <p>{locale === "es" ? "No hay tirada oculta para este resultado." : "There is no hidden roll for this outcome."}</p>}
              </div>
              <button className="primary-action" onClick={decide} disabled={busy}>
                {selected.risk === "gamble"
                  ? (locale === "es" ? "Girar la ruleta y comprometerse" : "Spin the wheel and commit")
                  : finalDecision
                  ? (locale === "es" ? "Confirmar y jugar la temporada" : "Confirm and play the season")
                  : (locale === "es" ? `Confirmar decisión ${decisionNumber} de ${decisionTotal}` : `Confirm decision ${decisionNumber} of ${decisionTotal}`)}
              </button>
            </section>
          ) : <p className="choice-help">{locale === "es" ? "Elige una opción para ver exactamente qué puede cambiar antes de confirmarla." : "Choose an option to see exactly what can change before confirming it."}</p>}

          {busy && selectedId ? <div className="simulating" role="status"><i /><div><b>{finalDecision ? (locale === "es" ? "Jugando el calendario de liga" : "Playing the league schedule") : (locale === "es" ? "Registrando la decisión" : "Recording the decision")}</b><span>{finalDecision ? (locale === "es" ? "6 combates · stats reales · resultado verificado" : "6 battles · real stats · verified result") : (locale === "es" ? `Quedan ${Math.max(0, decisionTotal - decisionNumber)} decisiones antes del calendario` : `${Math.max(0, decisionTotal - decisionNumber)} decisions remain before the schedule`)}</span></div></div> : null}
          {error ? <p className="form-error" role="alert">{error}</p> : null}
        </article>
      </div>
      <footer className="season-footer"><span>{run.totals.wins}–{run.totals.losses}–{run.totals.draws} career</span>{confirmRetire ? <span className="retire-confirm" role="dialog" aria-label={locale === "es" ? "Confirmar retiro" : "Confirm retirement"}>{locale === "es" ? "¿Cerrar la carrera aquí?" : "End the career here?"}<button onClick={retire} disabled={busy}>{copy.retire}</button><button onClick={() => setConfirmRetire(false)}>{locale === "es" ? "Cancelar" : "Cancel"}</button></span> : <button className="text-action" onClick={() => setConfirmRetire(true)}>{copy.retire}</button>}</footer>
    </section>
  );
}

function signed(value: number): string { return value > 0 ? `+${value}` : String(value); }

function RouletteOverlay({ state, target, locale, option, outcome, hasBattle, onContinue }: {
  state: "spinning" | "settling" | "success" | "failure";
  target: "success" | "failure" | null;
  locale: Locale;
  option?: DecisionOption;
  outcome?: Record<string, unknown> | null;
  hasBattle: boolean;
  onContinue: () => void;
}) {
  const actualRewards = Array.isArray(outcome?.rewards) ? outcome.rewards as DecisionReward[] : [];
  const reward = rewardSentence(actualRewards.length ? actualRewards : option?.gamble?.success_rewards ?? [], locale);
  const mechanical = outcome ? effectSentence(Object.fromEntries(Object.entries(outcome).filter(([, value]) => typeof value === "number")) as Record<string, number>, locale) : "";
  const resolved = state === "success" || state === "failure";
  return <div className={`roulette-overlay ${state}${target ? ` target-${target}` : ""}`} role="status" aria-live="assertive">
    <div className="roulette-wheel" aria-hidden="true"><i>×</i><i>×</i><i>✓</i><i>✓</i><b /></div>
    <section>
      <span>{locale === "es" ? "RULETA DE APUESTA" : "GAMBLE WHEEL"}</span>
      <h2>{state === "spinning" ? (locale === "es" ? "Girando…" : "Spinning…") : state === "settling" ? (locale === "es" ? "La rueda se detiene" : "The wheel is stopping") : state === "success" ? (locale === "es" ? "¡ÉXITO!" : "SUCCESS!") : (locale === "es" ? "NO SALIÓ" : "NO WIN")}</h2>
      <p>{state === "spinning" ? (locale === "es" ? "La elección está comprometida. La rueda completará el giro antes de revelar el resultado." : "The choice is committed. The wheel will complete its spin before revealing the result.") : state === "settling" ? (locale === "es" ? "Mira el puntero: el resultado quedará fijado en la rueda." : "Watch the pointer: the result will lock on the wheel.") : state === "success" ? `${reward}${mechanical ? ` · ${mechanical}` : ""}` : (locale === "es" ? `Resultado aplicado: ${mechanical || "sin cambios permanentes"}. El premio no se entrega.` : `Applied result: ${mechanical || "no permanent changes"}. The prize is not granted.`)}</p>
      {resolved ? <button type="button" className="primary-action roulette-continue" onClick={onContinue}>{hasBattle ? (locale === "es" ? "Entrar al campo de batalla" : "Enter the battlefield") : (locale === "es" ? "Continuar la carrera" : "Continue career")}</button> : null}
    </section>
  </div>;
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

function latestDecisionEffects(run: CareerRun): Record<string, unknown> {
  const history = run.season?.decision_history?.at(-1) as { effects?: Record<string, unknown> } | undefined;
  if (history?.effects) return history.effects;
  const seasonEvent = [...run.timeline].reverse().find((entry) => entry.type === "season.completed");
  return seasonEvent?.decision_effects && typeof seasonEvent.decision_effects === "object"
    ? seasonEvent.decision_effects as Record<string, unknown>
    : {};
}

function relationshipRoleLabel(role: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = { mentor: ["mentor", "mentor"], rival: ["rival", "rival"], owner: ["dirección", "club owner"], contact: ["contacto", "contact"] };
  return labels[role]?.[locale === "es" ? 0 : 1] ?? role;
}

function relationshipEdgeBenefit(benefit: string, amount: number, locale: Locale): string {
  if (benefit === "partner_training") return locale === "es" ? `Entrenamiento guiado +${amount}` : `Guided training +${amount}`;
  if (benefit === "rival_read") return locale === "es" ? `Lectura rival −${amount} preparación enemiga` : `Opponent read −${amount} enemy preparation`;
  if (benefit === "club_protection") return locale === "es" ? `Recuperación del club +${amount}` : `Club recovery +${amount}`;
  return locale === "es" ? `Preparación +${amount}` : `Preparation +${amount}`;
}

function effectChips(effects: Record<string, number>, locale: Locale) {
  return <>{Object.entries(effects).map(([key, value]) => <b key={key} className={value < 0 ? "negative" : "positive"}>{effectLabel(key, locale)} {signed(value)}</b>)}</>;
}

function effectSentence(effects: Record<string, number>, locale: Locale): string {
  return Object.entries(effects).map(([key, value]) => `${signed(value)} ${effectLabel(key, locale)}`).join(" · ");
}

function rewardChips(rewards: DecisionReward[], locale: Locale) {
  return <>{rewards.map((reward, index) => <b key={`${reward.type}-${index}`} className="world-reward">{rewardLabel(reward, locale)}</b>)}</>;
}

function rewardSentence(rewards: DecisionReward[], locale: Locale): string {
  return rewards.map((reward) => rewardLabel(reward, locale)).join(" · ");
}

function rewardLabel(reward: DecisionReward, locale: Locale): string {
  if (reward.type === "pokemon") return `${locale === "es" ? "Capturar" : "Catch"} ${reward.species}`;
  if (reward.type === "item") return `${reward.item} × ${reward.quantity}`;
  if (reward.type === "move") return `${locale === "es" ? "Aprender" : "Learn"} ${reward.move}`;
  if (reward.type === "level") return `${locale === "es" ? "Compañero" : "Partner"} +${reward.levels} LV`;
  if (reward.type === "stat") return `${reward.species} +${reward.amount} ${effectLabel(reward.stat, locale)}`;
  return `${locale === "es" ? "Vínculo" : "Bond"}: ${reward.name.split(" · ")[0]} ${reward.amount > 0 ? "+" : ""}${reward.amount}`;
}

function gambleSentence(option: DecisionOption, locale: Locale): string {
  const success = effectSentence(option.gamble?.success ?? {}, locale);
  const failure = effectSentence(option.gamble?.failure ?? {}, locale);
  return locale === "es" ? `Si sale bien: ${success}. Si falla: ${failure}.` : `On success: ${success}. On failure: ${failure}.`;
}

function familyLabel(family: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = {
    capture: ["Captura", "Capture"], evolution: ["Evolución", "Evolution"], breeding: ["Crianza", "Breeding"], contest: ["Concurso", "Contest"],
    research: ["Investigación", "Research"], health: ["Salud", "Health"], economy: ["Economía", "Economy"], media: ["Medios", "Media"],
    crime: ["Legalidad", "Legality"], friendship: ["Amistad", "Friendship"], rivalry: ["Rivalidad", "Rivalry"], conservation: ["Conservación", "Conservation"],
    regional_culture: ["Cultura regional", "Regional culture"], contract: ["Contrato", "Contract"], training: ["Entrenamiento", "Training"],
  };
  return labels[family]?.[locale === "es" ? 0 : 1] ?? family;
}

function preparationEdge(run: CareerRun): number {
  return Math.min(3, Math.max(0, run.development) / 3 | 0)
    + Math.min(1, Math.max(0, run.finances) / 4 | 0)
    - Number(run.health < 45)
    - Number(run.finances <= -4)
    + Math.min(2, Math.max(0, run.scouting) / 3 | 0)
    + Number(run.class_effects?.battle?.home_level_bonus ?? 0)
    - Number(run.class_effects?.battle?.away_level_bonus ?? 0);
}

function attributeHint(key: "development" | "scouting" | "finances" | "reputation", value: number, locale: Locale): string {
  if (key === "reputation") return locale === "es" ? "contratos" : "contracts";
  const threshold = key === "finances" ? 4 : 3;
  const remainder = Math.max(0, threshold - (Math.max(0, value) % threshold));
  if (value > 0 && value % threshold === 0) return locale === "es" ? "bono activo" : "bonus active";
  return locale === "es" ? `${remainder} para el próximo bono` : `${remainder} to next bonus`;
}
