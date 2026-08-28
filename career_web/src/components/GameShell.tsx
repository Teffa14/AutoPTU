import { useEffect, useState, type ReactNode } from "react";
import { navigate } from "../App";
import { t } from "../i18n";
import type { CareerRun, Locale } from "../types";

interface Props {
  children: ReactNode;
  run: CareerRun | null;
  locale: Locale;
  path: string;
  displaySeason?: number;
  homePath?: string;
  onLocale: (locale: Locale) => void;
}

export function GameShell({ children, run, locale, path, displaySeason, homePath, onLocale }: Props) {
  const copy = t(locale);
  const inBattle = path.startsWith("battle/");
  const seasonNumber = displaySeason ?? run?.season_number;
  const nav = run ? [
    { id: "season", label: copy.season, path: `run/${run.id}`, glyph: "◈" },
    { id: "profile", label: copy.trainer, path: `profile/${run.id}`, glyph: "♙" },
    { id: "timeline", label: copy.timeline, path: `timeline/${run.id}`, glyph: "⌁" },
    { id: "daily", label: copy.daily, path: "daily", glyph: "✦" },
  ] : [];
  return (
    <div className={`game-shell ${inBattle ? "is-battle" : ""}`}>
      <header className="game-header">
        <button className="wordmark" onClick={() => navigate(homePath ?? (run ? `run/${run.id}` : ""))} aria-label="AutoPTU Career home">
          <span>AUTO</span>PTU <b>CAREER</b>
        </button>
        <div className="header-meta">
          {seasonNumber ? <span className="save-light"><i /> {locale === "es" ? "temporada" : "season"} {seasonNumber}</span> : <span>RULESET 1.05</span>}
          <GoogleAccount locale={locale} />
          <button className="locale-toggle" onClick={() => onLocale(locale === "es" ? "en" : "es")}>{locale.toUpperCase()}</button>
        </div>
      </header>
      <main id="career-main">{children}</main>
      {nav.length > 0 && !inBattle ? (
        <nav className="game-nav" aria-label="Career navigation">
          {nav.map((item) => {
            const active = path === item.path || path.startsWith(`${item.id}/`);
            return <button key={item.id} className={active ? "active" : ""} onClick={() => navigate(item.path)} aria-current={active ? "page" : undefined}><b>{item.glyph}</b><span>{item.label}</span></button>;
          })}
        </nav>
      ) : null}
    </div>
  );
}

function GoogleAccount({ locale }: { locale: Locale }) {
  const [authModule, setAuthModule] = useState<typeof import("../auth") | null>(null);
  const [label, setLabel] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void import("../auth").then((module) => {
      if (active) setAuthModule(module);
    }).catch(() => {
      if (active) setAuthModule(null);
    });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    const client = authModule?.supabase;
    if (!client) return;
    let active = true;
    const update = (user: { is_anonymous?: boolean; email?: string; user_metadata?: Record<string, unknown> } | null | undefined) => {
      if (!active) return;
      setLabel(user && !user.is_anonymous ? String(user.email ?? user.user_metadata?.name ?? "Google") : "");
    };
    void client.auth.getSession().then(({ data }) => update(data.session?.user));
    const { data } = client.auth.onAuthStateChange((_event, session) => update(session?.user));
    return () => { active = false; data.subscription.unsubscribe(); };
  }, [authModule]);

  if (!authModule?.supabase) return null;
  return label
    ? <button className="account-chip" title={label} onClick={() => { void authModule.signOut().catch((reason: Error) => setError(reason.message)); }}>{label.split("@")[0]} <small>{locale === "es" ? "salir" : "sign out"}</small></button>
    : <button className="account-chip google" title={error || undefined} onClick={() => { setError(""); void authModule.signInWithProvider("google").catch((reason: Error) => setError(reason.message)); }}>G <small>{error ? "!" : locale === "es" ? "Entrar" : "Sign in"}</small></button>;
}
