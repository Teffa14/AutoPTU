import { useEffect, useState } from "react";
import { navigate } from "../App";
import { careerApi } from "../api";
import { signInWithEmail, signInWithProvider, supabase } from "../auth";
import type { CareerCatalog, CareerRun, Locale } from "../types";

export function DailyScreen({ locale, onRun }: { locale: Locale; onRun: (run: CareerRun) => void }) {
  const day = new Date().toISOString().slice(0, 10);
  const [challenge, setChallenge] = useState<Record<string, unknown> | null>(null);
  const [board, setBoard] = useState<Record<string, unknown> | null>(null);
  const [catalog, setCatalog] = useState<CareerCatalog | null>(null);
  const [mode, setMode] = useState("simple");
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
  const starter = catalog?.regions.find((entry) => entry.id === region)?.underdogs[0];

  async function beginAttempt() {
    if (!starter) return;
    setBusy(true); setError("");
    try {
      const result = await careerApi.dailyAttempt(day, {
        mode, starter, name: "Ranked Trainer", classes: ["Ace Trainer"], locale,
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
      <header><p className="eyebrow">UTC · {day}</p><h1>{locale === "es" ? "Todos reciben la misma llamada" : "Everyone gets the same call"}</h1><p>{region.toUpperCase()} · seed committed · best of three</p></header>
      <div className="daily-mode">{["simple", "advanced"].map((entry) => <button key={entry} className={mode === entry ? "active" : ""} aria-pressed={mode === entry} onClick={() => setMode(entry)}>{entry}</button>)}</div>
      <aside className="ranked-entry">
        <div><span>{locale === "es" ? "Entrada ranked" : "Ranked entry"}</span><b>{starter ?? "—"}</b><small>{locale === "es" ? "Tres intentos por modo · se conserva el mejor" : "Three attempts per mode · best result kept"}</small></div>
        {supabase ? <div className="auth-actions"><button onClick={() => signInWithProvider("google")}>Google</button><button onClick={() => signInWithProvider("discord")}>Discord</button><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="email@trainer.club" /><button onClick={emailOtp} disabled={!email || busy}>OTP</button></div> : <small>Local development identity</small>}
        <button className="primary-action" onClick={beginAttempt} disabled={!starter || busy}>{busy ? "…" : locale === "es" ? "Iniciar intento" : "Start attempt"}</button>
      </aside>
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
