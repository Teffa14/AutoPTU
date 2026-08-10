import { useState, type CSSProperties } from "react";
import { careerApi } from "../api";
import { navigate } from "../App";
import { t } from "../i18n";
import type { CareerRun, Locale } from "../types";
import { PokemonSprite } from "./PokemonSprite";

interface Props { run: CareerRun; locale: Locale; onRun: (run: CareerRun) => void }

export function SeasonScreen({ run, locale, onRun }: Props) {
  const copy = t(locale);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [confirmRetire, setConfirmRetire] = useState(false);
  const [shareUrl, setShareUrl] = useState("");
  const decision = run.season?.decision;

  async function decide(optionId: string) {
    setBusy(true);
    setError("");
    try {
      const result = await careerApi.decide(run, optionId);
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
      {shareUrl ? <output className="share-url">{window.location.origin}{shareUrl}</output> : null}
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
      <div className="season-stage">
        <aside className="partner-stand">
          <div className="sprite-halo"><PokemonSprite name={run.build.starter} className="partner-sprite" /></div>
          <p>first partner</p><h2>{run.build.starter}</h2><span>{run.build.pokeballs} Poké Balls · {run.build.classes.join(" / ")}</span>
        </aside>
        <article className="decision-ticket">
          <div className="ticket-notch top" /><div className="ticket-notch bottom" />
          <p className="eyebrow">{decision?.family ?? "season"} · {decision?.npc_name} · {run.season ? `${run.season.decisions_completed + 1}/${run.season.decisions_required}` : ""}</p>
          <h1>{decision?.title}</h1><p className="decision-body">{decision?.body}</p>
          <div className="decision-options">
            {decision?.options.map((option, index) => (
              <button key={option.id} onClick={() => decide(option.id)} disabled={busy}>
                <span className={`risk ${option.risk}`}>{index + 1} · {option.risk}</span><b>{option.label}</b><p>{option.description}</p>
                <small>{Object.entries(option.guaranteed).map(([key, value]) => `${key} ${value > 0 ? "+" : ""}${value}`).join(" · ")}{option.gamble?.chance ? ` · ${Math.round(option.gamble.chance * 100)}%` : ""}</small>
              </button>
            ))}
          </div>
          {busy ? <div className="simulating"><i /><span>{locale === "es" ? "Simulando el calendario con reglas PTU…" : "Simulating the schedule with PTU rules…"}</span></div> : null}
          {error ? <p className="form-error" role="alert">{error}</p> : null}
        </article>
      </div>
      <footer className="season-footer"><span>{run.totals.wins}–{run.totals.losses}–{run.totals.draws} career</span>{confirmRetire ? <span className="retire-confirm">{locale === "es" ? "¿Cerrar la carrera aquí?" : "End the career here?"}<button onClick={retire} disabled={busy}>{copy.retire}</button><button onClick={() => setConfirmRetire(false)}>Cancel</button></span> : <button className="text-action" onClick={() => setConfirmRetire(true)}>{copy.retire}</button>}</footer>
    </section>
  );
}
