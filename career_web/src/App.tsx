import { lazy, Suspense, useEffect, useState } from "react";
import { careerApi } from "./api";
import { CreateScreen } from "./components/CreateScreen";
import { DailyScreen } from "./components/DailyScreen";
import { GameShell } from "./components/GameShell";
import { HomeScreen } from "./components/HomeScreen";
import { ProfileScreen } from "./components/ProfileScreen";
import { ShareScreen } from "./components/ShareScreen";
import { TimelineScreen } from "./components/TimelineScreen";
import { loadLocalRun, saveLocalRun } from "./localCareer";
import { trainerSpriteStorageEntry } from "./trainerSprites";
import type { CareerRun, Locale } from "./types";

const BattleScreen = lazy(() => import("./components/BattleScreen"));
const SeasonHub = lazy(() => import("./components/SeasonHub").then((module) => ({ default: module.SeasonHub })));
const CAREER_BASE_PATH = import.meta.env.BASE_URL.replace(/\/+$/, "");

function currentPath(): string {
  const pathname = window.location.pathname;
  if (pathname === CAREER_BASE_PATH || pathname === `${CAREER_BASE_PATH}/`) return "";
  if (pathname.startsWith(`${CAREER_BASE_PATH}/`)) return pathname.slice(CAREER_BASE_PATH.length + 1);
  return "";
}

export function navigate(path: string): void {
  const suffix = path.replace(/^\/+/, "");
  const target = suffix ? `${CAREER_BASE_PATH}/${suffix}` : `${CAREER_BASE_PATH}/`;
  window.history.pushState({}, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function App() {
  const [path, setPath] = useState(currentPath);
  const [locale, setLocale] = useState<Locale>(() => (localStorage.getItem("career-locale") === "en" ? "en" : "es"));
  const [run, setRun] = useState<CareerRun | null>(null);
  const [runLoadError, setRunLoadError] = useState("");

  useEffect(() => {
    const update = () => setPath(currentPath());
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);

  useEffect(() => {
    localStorage.setItem("career-locale", locale);
    document.documentElement.lang = locale;
    const skipLink = document.querySelector<HTMLElement>(".skip-link");
    if (skipLink) skipLink.textContent = locale === "es" ? "Saltar al contenido" : "Skip to content";
  }, [locale]);

  useEffect(() => {
    if (!run) return;
    saveLocalRun(run);
    const trainerSprite = trainerSpriteStorageEntry(run);
    if (trainerSprite) localStorage.setItem(trainerSprite.key, trainerSprite.sprite);
  }, [run]);

  const runMatch = path.match(/^(?:run|profile|timeline)\/([^/]+)/);
  const battleMatch = path.match(/^battle\/([^/]+)\/([^/]+)/);
  const shareMatch = path.match(/^share\/([^/]+)/);
  const requestedRunId = runMatch?.[1] ?? battleMatch?.[1];
  useEffect(() => {
    if (!requestedRunId) {
      setRunLoadError("");
      return;
    }
    if (run?.id === requestedRunId) {
      setRunLoadError("");
      return;
    }
    let active = true;
    setRunLoadError("");
    careerApi.run(requestedRunId).then((value) => {
      if (active) setRun(value);
    }).catch((reason: Error) => {
      if (!active) return;
      const local = loadLocalRun(requestedRunId);
      if (local) {
        setRun(local);
        setRunLoadError("");
        return;
      }
      setRunLoadError(reason.message);
    });
    return () => { active = false; };
  }, [requestedRunId, run?.id]);

  const routeRun = requestedRunId && run?.id === requestedRunId ? run : null;
  const battleSeason = Number(battleMatch?.[2].match(/-s(\d+)-m\d+$/)?.[1] ?? 0) || undefined;
  let screen;
  if (shareMatch) {
    screen = <ShareScreen shareId={shareMatch[1]} locale={locale} />;
  } else if (battleMatch) {
    screen = (
      <Suspense fallback={<div className="scene-loading">Loading arena…</div>}>
        <BattleScreen runId={battleMatch[1]} battleId={battleMatch[2]} locale={locale} run={routeRun} onRun={setRun} />
      </Suspense>
    );
  } else if (runMatch && !routeRun) {
    screen = runLoadError ? (
      <section className="battle-error" role="alert">
        <h1>{locale === "es" ? "No se pudo abrir esta carrera" : "This career could not be opened"}</h1>
        <p>{localizeApiError(runLoadError, locale)}</p>
        <button onClick={() => navigate(run ? `run/${run.id}` : "")}>{run ? (locale === "es" ? "Volver a mi carrera" : "Back to my career") : (locale === "es" ? "Volver al inicio" : "Back to start")}</button>
      </section>
    ) : <div className="scene-loading">{locale === "es" ? "Cargando carrera…" : "Loading career…"}</div>;
  } else if (path.startsWith("profile/") && routeRun) {
    screen = <ProfileScreen run={routeRun} locale={locale} onRun={setRun} />;
  } else if (path.startsWith("timeline/") && routeRun) {
    screen = <TimelineScreen run={routeRun} locale={locale} />;
  } else if (path === "daily" || path.startsWith("leaderboard")) {
    screen = <DailyScreen locale={locale} onRun={setRun} leaderboardOnly={path.startsWith("leaderboard")} />;
  } else if (path.startsWith("run/") && routeRun) {
    screen = (
      <Suspense fallback={<div className="scene-loading">{locale === "es" ? "Cargando temporada…" : "Loading season…"}</div>}>
        <SeasonHub run={routeRun} locale={locale} onRun={setRun} />
      </Suspense>
    );
  } else if (path === "new" || path === "create") {
    screen = <CreateScreen locale={locale} onCreated={(value) => { setRun(value); saveLocalRun(value); navigate(`run/${value.id}`); }} />;
  } else {
    screen = <HomeScreen locale={locale} />;
  }

  const shellRun = shareMatch || path === "" || path === "new" || path === "create" ? null : requestedRunId ? routeRun : run;
  return (
    <GameShell run={shellRun} locale={locale} path={path} displaySeason={battleSeason} homePath={battleMatch ? `run/${battleMatch[1]}` : undefined} onLocale={setLocale}>
      {screen}
    </GameShell>
  );
}

function localizeApiError(message: string, locale: Locale): string {
  if (locale !== "es") return message;
  if (message.includes("belongs to another account")) return "Esta carrera pertenece a otra cuenta.";
  if (message.includes("Career run not found")) return "No encontramos esa carrera.";
  return message;
}
