import { useEffect, useMemo, useState, type CSSProperties } from "react";

import { careerApi } from "../api";
import { navigate } from "../App";
import { decisionPresentation, effectLabel, effectRule, riskLabel, transparencyLabel } from "../decisionPresentation";
import { t } from "../i18n";
import type { CareerRun, DecisionOption, Locale } from "../types";
import { PokemonSprite } from "./PokemonSprite";

interface Props { run: CareerRun; locale: Locale; onRun: (run: CareerRun) => void }

export function SeasonScreen({ run, locale, onRun }: Props) {
  const copy = t(locale);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [confirmRetire, setConfirmRetire] = useState(false);
  const [shareUrl, setShareUrl] = useState("");
  const decision = run.season?.decision;
  const presentation = useMemo(
    () => decision ? decisionPresentation(decision, run, locale) : null,
    [decision, locale, run],
  );
  const selected = presentation?.options.find((option) => option.id === selectedId);
  const finalDecision = Boolean(run.season && run.season.decisions_completed + 1 >= run.season.decisions_required);
  const decisionNumber = (run.season?.decisions_completed ?? 0) + 1;
  const decisionTotal = run.season?.decisions_required ?? 1;

  useEffect(() => setSelectedId(""), [decision?.id]);

  async function decide() {
    if (!selectedId) return;
    setBusy(true);
    setError("");
    try {
      const result = await careerApi.decide(run, selectedId);
      onRun(result.run);
      sessionStorage.setItem(`career-battles:${run.id}`, JSON.stringify(result.battle_ids));
      const featured = result.battle_ids.at(-1);
      if (featured) navigate(`battle/${run.id}/${featured}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally { setBusy(false); }
  }

  async function retire() {
    setBusy(true);
    try { onRun(await careerApi.retire(run.id)); setConfirmRetire(false); }
    catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setBusy(false); }
  }

  async function share(includeReplay: boolean) {
    setBusy(true);
    try { setShareUrl((await careerApi.share(run.id, includeReplay)).url); }
    catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setBusy(false); }
  }

  if (run.status === "retired") return (
    <section className="retirement-scene">
      <p className="eyebrow">Career record sealed</p><h1>{run.build.name}</h1>
      <p>{locale === "es" ? `Se retiró a los ${run.age}. La liga conserva el registro.` : `Retired at ${run.age}. The league keeps the record.`}</p>
      <div className="retirement-score"><b>{run.score}</b><span>{copy.score}</span></div>
      <div className="record-ribbon"><span>{run.totals.wins} W</span><span>{run.totals.losses} L</span><span>{run.totals.titles} titles</span></div>
      <button className="primary-action" onClick={() => navigate(`timeline/${run.id}`)}>{copy.timeline}</button>
      <div className="share-actions"><button onClick={() => share(false)} disabled={busy}>{locale === "es" ? "Compartir tarjeta" : "Share card"}</button><button onClick={() => share(true)} disabled={busy}>{locale === "es" ? "Compartir con replay" : "Share with replay"}</button></div>
      {shareUrl ? <output className="share-url"><a href={`${window.location.origin}${shareUrl}`} target="_blank" rel="noreferrer">{window.location.origin}{shareUrl}</a></output> : null}
      {error ? <p className="form-error" role="alert">{error}</p> : null}
    </section>
  );

  return (
    <section className="season-scene">
      <div className="season-sky" aria-hidden="true" />
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

      <div className="season-stage">
        <aside className="partner-stand">
          <div className="sprite-halo"><PokemonSprite name={run.build.starter} className="partner-sprite" /></div>
          <p>{locale === "es" ? "primer compañero" : "first partner"}</p><h2>{run.build.starter}</h2>
          <span>{run.build.pokeballs} Poké Balls · {run.build.classes.join(" / ")}</span>
          <div className="partner-preparation"><span>{locale === "es" ? "Ventaja de preparación" : "Preparation edge"}</span><b>{preparationEdge(run) >= 0 ? "+" : ""}{preparationEdge(run)} LV</b></div>
        </aside>

        <article className="decision-ticket">
          <div className="ticket-notch top" /><div className="ticket-notch bottom" />
          <header className="decision-brief">
            <div><span>{locale === "es" ? "QUIÉN" : "WHO"}</span><b>{decision?.npc_name?.split(" · ")[0] ?? "League staff"}</b></div>
            <div><span>{locale === "es" ? "ÁREA" : "AREA"}</span><b>{decision ? effectLabel(primaryEffect(decision.options), locale) : "—"}</b></div>
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
                <span className="choice-effects">{effectChips(option.guaranteed, locale)}<small>{transparencyLabel(option.transparency, locale)}</small></span>
              </button>
            ))}
          </div>

          {selected ? (
            <section className={`decision-confirmation ${selected.risk}`} aria-live="polite">
              <div>
                <span>{locale === "es" ? "CONSECUENCIA ASEGURADA" : "GUARANTEED OUTCOME"}</span>
                <strong>{effectSentence(selected.guaranteed, locale)}</strong>
                {selected.gamble?.chance ? (
                  <p><b>{Math.round(selected.gamble.chance * 100)}%</b> {locale === "es" ? "de éxito." : "success chance."} {gambleSentence(selected, locale)}</p>
                ) : <p>{locale === "es" ? "No hay tirada oculta para este resultado." : "There is no hidden roll for this outcome."}</p>}
              </div>
              <button className="primary-action" onClick={decide} disabled={busy}>
                {finalDecision
                  ? (locale === "es" ? "Confirmar y jugar la temporada" : "Confirm and play the season")
                  : (locale === "es" ? `Confirmar decisión ${decisionNumber} de ${decisionTotal}` : `Confirm decision ${decisionNumber} of ${decisionTotal}`)}
              </button>
            </section>
          ) : <p className="choice-help">{locale === "es" ? "Elige una opción para ver exactamente qué puede cambiar antes de confirmarla." : "Choose an option to see exactly what can change before confirming it."}</p>}

          {busy && selectedId ? <div className="simulating" role="status"><i /><div><b>{finalDecision ? (locale === "es" ? "Jugando el calendario PTU" : "Playing the PTU schedule") : (locale === "es" ? "Registrando la decisión" : "Recording the decision")}</b><span>{finalDecision ? (locale === "es" ? "6 combates · stats reales · resultado verificado" : "6 battles · real stats · verified result") : (locale === "es" ? `Quedan ${Math.max(0, decisionTotal - decisionNumber)} decisiones antes del calendario` : `${Math.max(0, decisionTotal - decisionNumber)} decisions remain before the schedule`)}</span></div></div> : null}
          {error ? <p className="form-error" role="alert">{error}</p> : null}
        </article>
      </div>
      <footer className="season-footer"><span>{run.totals.wins}–{run.totals.losses}–{run.totals.draws} career</span>{confirmRetire ? <span className="retire-confirm" role="dialog" aria-label={locale === "es" ? "Confirmar retiro" : "Confirm retirement"}>{locale === "es" ? "¿Cerrar la carrera aquí?" : "End the career here?"}<button onClick={retire} disabled={busy}>{copy.retire}</button><button onClick={() => setConfirmRetire(false)}>{locale === "es" ? "Cancelar" : "Cancel"}</button></span> : <button className="text-action" onClick={() => setConfirmRetire(true)}>{copy.retire}</button>}</footer>
    </section>
  );
}

function signed(value: number): string { return value > 0 ? `+${value}` : String(value); }

function effectChips(effects: Record<string, number>, locale: Locale) {
  return <>{Object.entries(effects).map(([key, value]) => <b key={key} className={value < 0 ? "negative" : "positive"}>{effectLabel(key, locale)} {signed(value)}</b>)}</>;
}

function effectSentence(effects: Record<string, number>, locale: Locale): string {
  return Object.entries(effects).map(([key, value]) => `${signed(value)} ${effectLabel(key, locale)}`).join(" · ");
}

function gambleSentence(option: DecisionOption, locale: Locale): string {
  const success = effectSentence(option.gamble?.success ?? {}, locale);
  const failure = effectSentence(option.gamble?.failure ?? {}, locale);
  return locale === "es" ? `Si sale bien: ${success}. Si falla: ${failure}.` : `On success: ${success}. On failure: ${failure}.`;
}

function primaryEffect(options: DecisionOption[]): string {
  return Object.keys(options[1]?.guaranteed ?? options[0]?.guaranteed ?? {})[0] ?? "development";
}

function preparationEdge(run: CareerRun): number {
  return Math.min(3, Math.max(0, run.development) / 3 | 0)
    + Math.min(1, Math.max(0, run.finances) / 4 | 0)
    - Number(run.health < 45)
    - Number(run.finances <= -4)
    + Math.min(2, Math.max(0, run.scouting) / 3 | 0);
}

function attributeHint(key: "development" | "scouting" | "finances" | "reputation", value: number, locale: Locale): string {
  if (key === "reputation") return locale === "es" ? "contratos" : "contracts";
  const threshold = key === "finances" ? 4 : 3;
  const remainder = Math.max(0, threshold - (Math.max(0, value) % threshold));
  if (value > 0 && value % threshold === 0) return locale === "es" ? "bono activo" : "bonus active";
  return locale === "es" ? `${remainder} para el próximo bono` : `${remainder} to next bonus`;
}
