import { useEffect, useState } from "react";
import { navigate } from "../App";
import { careerApi } from "../api";
import { hasPersistentCareerAccount, signInWithPassword, signUpWithPassword, supabase } from "../auth";
import { leaderboardEntries, leaderboardTrainerName } from "../leaderboardPresentation";
import { DEFAULT_TRAINER_SPRITE, trainerSpriteOptions, trainerSpriteStorageEntry } from "../trainerSprites";
import type { CareerCatalog, CareerMode, CareerRun, Locale } from "../types";
import { StarterPicker } from "./StarterPicker";
import { TrainerSpritePicker } from "./TrainerSpritePicker";

export function DailyScreen({ locale, onRun, leaderboardOnly = false }: { locale: Locale; onRun: (run: CareerRun) => void; leaderboardOnly?: boolean }) {
  const day = new Date().toISOString().slice(0, 10);
  const [challenge, setChallenge] = useState<Record<string, unknown> | null>(null);
  const [board, setBoard] = useState<Record<string, unknown> | null>(null);
  const [catalog, setCatalog] = useState<CareerCatalog | null>(null);
  const [mode, setMode] = useState<CareerMode>("simple");
  const [starter, setStarter] = useState("");
  const [trainerClass, setTrainerClass] = useState("Ace Trainer");
  const [trainerName, setTrainerName] = useState("Ranked Trainer");
  const [trainerSprite, setTrainerSprite] = useState(DEFAULT_TRAINER_SPRITE);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [accountReady, setAccountReady] = useState(false);
  const [accountChecking, setAccountChecking] = useState(Boolean(supabase));

  useEffect(() => {
    Promise.all([careerApi.daily(day), careerApi.leaderboard(day, mode), careerApi.catalog(locale)])
      .then(([daily, leaderboard, currentCatalog]) => {
        setChallenge(daily); setBoard(leaderboard); setCatalog(currentCatalog);
      })
      .catch((reason: Error) => setError(reason.message));
  }, [day, locale, mode]);

  useEffect(() => {
    let active = true;
    async function refreshAccount() {
      setAccountChecking(true);
      const ready = await hasPersistentCareerAccount();
      if (active) {
        setAccountReady(ready);
        setAccountChecking(false);
      }
    }
    void refreshAccount();
    const subscription = supabase?.auth.onAuthStateChange(() => { void refreshAccount(); }).data.subscription;
    return () => {
      active = false;
      subscription?.unsubscribe();
    };
  }, []);

  const entries = leaderboardEntries(board?.entries);
  const region = String(challenge?.region ?? "kanto");
  const regionCatalog = catalog?.regions.find((entry) => entry.id === region);
  const spriteOptions = trainerSpriteOptions(catalog);

  useEffect(() => {
    if (!regionCatalog?.partner_choices.length) return;
    if (!regionCatalog.partner_choices.includes(starter)) setStarter(regionCatalog.partner_choices[0]);
  }, [regionCatalog, starter]);

  async function beginAttempt() {
    if (!starter) return;
    if (!accountReady) {
      setError(locale === "es" ? "Iniciá sesión para usar uno de tus tres intentos ranked." : "Sign in before using one of your three ranked attempts.");
      return;
    }
    setBusy(true); setError("");
    try {
      const result = await careerApi.dailyAttempt(day, {
        mode, starter, name: trainerName, classes: [trainerClass], locale, trainer_sprite: trainerSprite,
      });
      const storageEntry = trainerSpriteStorageEntry(result.run);
      if (storageEntry) localStorage.setItem(storageEntry.key, trainerSprite);
      onRun(result.run);
      navigate(`run/${result.run.id}`);
    } catch (reason) { setError(localizedError(reason instanceof Error ? reason.message : String(reason), locale)); }
    finally { setBusy(false); }
  }

  async function passwordAuth(action: "signin" | "signup") {
    setBusy(true); setError("");
    try {
      if (action === "signin") {
        await signInWithPassword(email, password);
      } else {
        const result = await signUpWithPassword(email, password);
        if (!result.signedIn) {
          await signInWithPassword(email, password);
        }
      }
      const ready = await hasPersistentCareerAccount();
      setAccountReady(ready);
      if (!ready) throw new Error(locale === "es" ? "La cuenta se creó, pero Supabase no abrió una sesión ranked." : "The account was created, but Supabase did not open a ranked session.");
    }
    catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setBusy(false); }
  }

  return (
    <section className="daily-scene">
      <header><p className="eyebrow">UTC · {day}</p><h1>{locale === "es" ? "El mismo mundo. Tu propio entrenador." : "The same world. Your own trainer."}</h1><p>{region.toUpperCase()} · seed {String(challenge?.seed ?? "—")} · {locale === "es" ? "mismos eventos y decisiones" : "same events and decisions"}</p></header>
      <div className="daily-mode">{(["simple", "advanced"] as CareerMode[]).map((entry) => <button key={entry} className={mode === entry ? "active" : ""} aria-pressed={mode === entry} onClick={() => setMode(entry)}>{entry}</button>)}</div>
      {!leaderboardOnly ? <aside className="ranked-entry">
        <div className="daily-build-heading"><span>{locale === "es" ? "Entrada ranked" : "Ranked entry"}</span><b>{regionCatalog?.label ?? region}</b><small>{locale === "es" ? "La región, el calendario y las decisiones quedan fijados. El starter, la clase y el sprite son tuyos." : "Region, schedule and decisions are fixed. Starter, class and sprite are yours."}</small></div>
        <fieldset className="starter-field daily-starters"><legend>{locale === "es" ? "Elegí tu compañero" : "Choose your partner"}</legend><StarterPicker starters={regionCatalog?.starters ?? []} underdogs={regionCatalog?.underdogs ?? []} value={starter} locale={locale} name="daily-starter" onChange={setStarter} /></fieldset>
        <TrainerSpritePicker sprites={spriteOptions} value={trainerSprite} locale={locale} compact onChange={setTrainerSprite} />
        <div className="daily-build-fields">
          <label><span>{locale === "es" ? "Nombre" : "Name"}</span><input value={trainerName} maxLength={30} onChange={(event) => setTrainerName(event.target.value)} /></label>
          <label><span>{locale === "es" ? "Clase de entrenador" : "Trainer class"}</span><select value={trainerClass} onChange={(event) => setTrainerClass(event.target.value)}>{catalog?.classes.map((entry) => <option key={entry.id} value={entry.name}>{entry.name}</option>)}</select><small>{catalog?.classes.find((entry) => entry.name === trainerClass)?.[locale === "es" ? "description_es" : "description_en"]}</small></label>
        </div>
        {supabase ? <div className="auth-actions">
          {accountReady ? <strong>{locale === "es" ? "Cuenta ranked verificada" : "Ranked account verified"}</strong> : <>
            <input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="email@trainer.club" />
            <input type="password" autoComplete="current-password" minLength={6} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={locale === "es" ? "contraseña" : "password"} />
            <button onClick={() => { void passwordAuth("signin"); }} disabled={!email || password.length < 6 || busy}>{locale === "es" ? "Entrar" : "Sign in"}</button>
            <button onClick={() => { void passwordAuth("signup"); }} disabled={!email || password.length < 6 || busy}>{locale === "es" ? "Crear cuenta" : "Create account"}</button>
          </>}
          <small>{accountReady ? (locale === "es" ? "Tu identidad se usa sólo para ranked y leaderboard." : "Your identity is used only for ranked and leaderboard.") : accountChecking ? (locale === "es" ? "Comprobando cuenta…" : "Checking account…") : (locale === "es" ? "Acceso directo en esta página. No usa redirects externos." : "Direct sign-in on this page. No external redirects.")}</small>
        </div> : <small>{locale === "es" ? "Ranked no está disponible en este build; el Career casual sigue libre." : "Ranked is unavailable in this build; casual Career remains open."}</small>}
        <footer><small>{locale === "es" ? "Tres intentos por modo · se conserva el mejor" : "Three attempts per mode · best result kept"}</small><button className="primary-action" onClick={beginAttempt} disabled={!starter || !trainerName.trim() || busy || !accountReady}>{busy ? "…" : locale === "es" ? "Iniciar intento" : "Start attempt"}</button></footer>
      </aside> : null}
      <div className="leaderboard-board">
        <div className="leaderboard-head"><span>rank</span><span>{locale === "es" ? "entrenador" : "trainer"}</span><span>score</span></div>
        {entries.length ? entries.map((entry) => {
          const visibleTrainerName = leaderboardTrainerName(entry);
          return <div key={`${visibleTrainerName}:${String(entry.rank)}`}><b>#{String(entry.rank)}</b><span>{visibleTrainerName}</span><strong>{String(entry.score)}</strong></div>;
        }) : <div className="empty-board">{error || (locale === "es" ? "Nadie ha cerrado su carrera todavía." : "No career has been sealed yet.")}</div>}
      </div>
    </section>
  );
}

function localizedError(message: string, locale: Locale): string {
  if (locale === "es" && message.includes("All three ranked attempts")) return "Los tres intentos ranked de este modo ya están comprometidos.";
  if (locale === "es" && message.includes("permanent account is required")) return "Necesitas una cuenta permanente para jugar el reto diario ranked.";
  return message;
}
