import { lazy, Suspense, useEffect, useState } from "react";
import { careerApi } from "./api";
import { CreateScreen } from "./components/CreateScreen";
import { DailyScreen } from "./components/DailyScreen";
import { GameShell } from "./components/GameShell";
import { ProfileScreen } from "./components/ProfileScreen";
import { SeasonScreen } from "./components/SeasonScreen";
import { ShareScreen } from "./components/ShareScreen";
import { TimelineScreen } from "./components/TimelineScreen";
import type { CareerRun, Locale } from "./types";

const BattleScreen = lazy(() => import("./components/BattleScreen"));

function currentPath(): string {
  return window.location.pathname.replace(/^\/career-game\/?/, "");
}

export function navigate(path: string): void {
  const target = `/career-game/${path.replace(/^\//, "")}`;
  window.history.pushState({}, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function App() {
  const [path, setPath] = useState(currentPath);
  const [locale, setLocale] = useState<Locale>(() => (localStorage.getItem("career-locale") === "en" ? "en" : "es"));
  const [run, setRun] = useState<CareerRun | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const update = () => setPath(currentPath());
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);

  useEffect(() => {
    localStorage.setItem("career-locale", locale);
    document.documentElement.lang = locale;
  }, [locale]);

  const runMatch = path.match(/^(?:run|profile|timeline)\/([^/]+)/);
  const battleMatch = path.match(/^battle\/([^/]+)\/([^/]+)/);
  const shareMatch = path.match(/^share\/([^/]+)/);
  const requestedRunId = runMatch?.[1] ?? battleMatch?.[1];
  useEffect(() => {
    if (!requestedRunId || run?.id === requestedRunId) return;
    let active = true;
    careerApi.run(requestedRunId).then((value) => {
      if (active) setRun(value);
    }).catch((reason: Error) => {
      if (active) setError(reason.message);
    });
    return () => { active = false; };
  }, [requestedRunId, run?.id]);

  let screen;
  if (shareMatch) {
    screen = <ShareScreen shareId={shareMatch[1]} locale={locale} />;
  } else if (battleMatch) {
    screen = (
      <Suspense fallback={<div className="scene-loading">Loading arena…</div>}>
        <BattleScreen runId={battleMatch[1]} battleId={battleMatch[2]} locale={locale} />
      </Suspense>
    );
  } else if (path.startsWith("profile/") && run) {
    screen = <ProfileScreen run={run} locale={locale} />;
  } else if (path.startsWith("timeline/") && run) {
    screen = <TimelineScreen run={run} locale={locale} />;
  } else if (path === "daily" || path.startsWith("leaderboard")) {
    screen = <DailyScreen locale={locale} />;
  } else if (path.startsWith("run/") && run) {
    screen = <SeasonScreen run={run} locale={locale} onRun={setRun} />;
  } else {
    screen = <CreateScreen locale={locale} onCreated={(value) => { setRun(value); localStorage.setItem("career-last-run", value.id); navigate(`run/${value.id}`); }} />;
  }

  return (
    <GameShell run={run} locale={locale} path={path} onLocale={setLocale}>
      {error ? <div className="error-banner" role="alert">{error}<button onClick={() => setError("")}>×</button></div> : null}
      {screen}
    </GameShell>
  );
}
