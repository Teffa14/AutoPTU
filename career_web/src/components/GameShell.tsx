import { useEffect, useState, type ReactNode } from "react";
import { navigate } from "../App";
import { signInWithProvider, signOut, supabase } from "../auth";
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
  const [label, setLabel] = useState("");
  useEffect(() => {
    const client = supabase;
    if (!client) return;
    let active = true;
    const update = () => client.auth.getUser().then(({ data }) => {
      if (!active) return;
      setLabel(data.user && !data.user.is_anonymous ? String(data.user.email ?? data.user.user_metadata?.name ?? "Google") : "");
    });
    void update();
    const { data } = client.auth.onAuthStateChange(() => { void update(); });
    return () => { active = false; data.subscription.unsubscribe(); };
  }, []);
  if (!supabase) return null;
  return label
    ? <button className="account-chip" title={label} onClick={() => { void signOut(); }}>{label.split("@")[0]} <small>{locale === "es" ? "salir" : "sign out"}</small></button>
    : <button className="account-chip google" onClick={() => { void signInWithProvider("google"); }}>G <small>{locale === "es" ? "Entrar" : "Sign in"}</small></button>;
}
