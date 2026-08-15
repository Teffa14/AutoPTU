import { useEffect, useState } from "react";
import { navigate } from "../App";
import { careerApi } from "../api";
import { signInWithEmail, signInWithProvider, supabase } from "../auth";
import type { CareerCatalog, CareerMode, CareerRun, Locale } from "../types";
import { StarterPicker } from "./StarterPicker";

export function DailyScreen({ locale, onRun, leaderboardOnly = false }: { locale: Locale; onRun: (run: CareerRun) => void; leaderboardOnly?: boolean }) {
  const day = new Date().toISOString().slice(0, 10);
  const [challenge, setChallenge] = useState<Record<string, unknown> | null>(null);
  const [board, setBoard] = useState<Record<string, unknown> | null>(null);
  const [catalog, setCatalog] = useState<CareerCatalog | null>(null);
  const [mode, setMode] = useState<CareerMode>("simple");
  const [starter, setStarter] = useState("");
  const [trainerClass, setTrainerClass] = useState("Ace Trainer");
  const [trainerName, setTrainerName] = useState("Ranked Trainer");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    Promise.all([careerApi.daily(day), careerApi.leaderboard(day, mode), careerApi.catalog(locale)])
      .then(([daily, leaderboard, currentCatalog]) => {
        setChallenge(daily); setBoard(leaderboard); setCatalog(currentCatalog);
      })
      .catch((reason: Error) => setError(reason.message));
  }, [day, locale, mode]);

  const entries = (board?.entries as Record<string, unknown>[] | undefined) ?? [];
  const region = String(challenge?.region ?? "kanto");
  const regionCatalog = catalog?.regions.find((entry) => entry.id === region);

  useEffect(() => {
    if (!regionCatalog?.partner_choices.length) return;
    if (!regionCatalog.partner_choices.includes(starter)) setStarter(regionCatalog.partner_choices[0]);
  }, [regionCatalog, starter]);

  async function beginAttempt() {
    if (!starter) return;
    setBusy(true); setError("");
    try {
      const result = await careerApi.dailyAttempt(day, {
        mode, starter, name: trainerName, classes: [trainerClass], locale,
      });
      onRun(result.run);
      navigate(`run/${result.run.id}`);
    } catch (reason) { setError(localizedError(reason instanceof Error ? reason.message : String(reason), locale)); }
    finally { setBusy(false); }
  }

  async function emailOtp() {
    setBusy(true); setError("");
    try { await signInWithEmail(email); }
    catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setBusy(false); }
  }

  return (
    <section className="daily-scene">
      <header><p className="eyebrow">UTC · {day}</p><h1>{locale === "es" ? "El mismo mundo. Tu propio entrenador." : "The same world. Your own trainer."}</h1><p>{region.toUpperCase()} · seed {String(challenge?.seed ?? "—")} · {locale === "es" ? "mismos eventos y decisiones" : "same events and decisions"}</p></header>
      <div className="daily-mode">{(["simple", "advanced"] as CareerMode[]).map((entry) => <button key={entry} className={mode === entry ? "active" : ""} aria-pressed={mode === entry} onClick={() => setMode(entry)}>{entry}</button>)}</div>
      {!leaderboardOnly ? <aside className="ranked-entry">
        <div className="daily-build-heading"><span>{locale === "es" ? "Entrada ranked" : "Ranked entry"}</span><b>{regionCatalog?.label ?? region}</b><small>{locale === "es" ? "La región, el calendario y las decisiones quedan fijados. El starter y la clase son tuyos." : "Region, schedule and decisions are fixed. Starter and class are yours."}</small></div>
        <fieldset className="starter-field daily-starters"><legend>{locale === "es" ? "Elegí tu compañero" : "Choose your partner"}</legend><StarterPicker starters={regionCatalog?.starters ?? []} underdogs={regionCatalog?.underdogs ?? []} value={starter} locale={locale} name="daily-starter" onChange={setStarter} /></fieldset>
        <div className="daily-build-fields">
          <label><span>{locale === "es" ? "Nombre" : "Name"}</span><input value={trainerName} maxLength={30} onChange={(event) => setTrainerName(event.target.value)} /></label>
          <label><span>{locale === "es" ? "Clase de entrenador" : "Trainer class"}</span><select value={trainerClass} onChange={(event) => setTrainerClass(event.target.value)}>{catalog?.classes.map((entry) => <option key={entry.id} value={entry.name}>{entry.name}</option>)}</select><small>{catalog?.classes.find((entry) => entry.name === trainerClass)?.[locale === "es" ? "description_es" : "description_en"]}</small></label>
        </div>
        {supabase ? <div className="auth-actions"><button onClick={() => { void signInWithProvider("google").catch((reason: Error) => setError(reason.message)); }}>Google</button><button onClick={() => { void signInWithProvider("discord").catch((reason: Error) => setError(reason.message)); }}>Discord</button><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="email@trainer.club" /><button onClick={emailOtp} disabled={!email || busy}>OTP</button></div> : <small>Local development identity</small>}
        <footer><small>{locale === "es" ? "Tres intentos por modo · se conserva el mejor" : "Three attempts per mode · best result kept"}</small><button className="primary-action" onClick={beginAttempt} disabled={!starter || !trainerName.trim() || busy}>{busy ? "…" : locale === "es" ? "Iniciar intento" : "Start attempt"}</button></footer>
      </aside> : null}
      <div className="leaderboard-board">
        <div className="leaderboard-head"><span>rank</span><span>trainer</span><span>score</span></div>
        {entries.length ? entries.map((entry) => <div key={`${String(entry.handle)}:${String(entry.rank)}`}><b>#{String(entry.rank)}</b><span>{String(entry.handle)}</span><strong>{String(entry.score)}</strong></div>) : <div className="empty-board">{error || (locale === "es" ? "Nadie ha cerrado su carrera todavía." : "No career has been sealed yet.")}</div>}
      </div>
    </section>
  );
}

function localizedError(message: string, locale: Locale): string {
  if (locale === "es" && message.includes("All three ranked attempts")) return "Los tres intentos ranked de este modo ya están comprometidos.";
  if (locale === "es" && message.includes("permanent account is required")) return "Necesitas una cuenta permanente para jugar el reto diario ranked.";
  return message;
}
