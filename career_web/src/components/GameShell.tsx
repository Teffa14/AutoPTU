import type { ReactNode } from "react";
import { navigate } from "../App";
import { t } from "../i18n";
import type { CareerRun, Locale } from "../types";

interface Props {
  children: ReactNode;
  run: CareerRun | null;
  locale: Locale;
  path: string;
  onLocale: (locale: Locale) => void;
}

export function GameShell({ children, run, locale, path, onLocale }: Props) {
  const copy = t(locale);
  const inBattle = path.startsWith("battle/");
  const nav = run ? [
    { id: "season", label: copy.season, path: `run/${run.id}`, glyph: "◈" },
    { id: "profile", label: copy.trainer, path: `profile/${run.id}`, glyph: "♙" },
    { id: "timeline", label: copy.timeline, path: `timeline/${run.id}`, glyph: "⌁" },
    { id: "daily", label: copy.daily, path: "daily", glyph: "✦" },
  ] : [];
  return (
    <div className={`game-shell ${inBattle ? "is-battle" : ""}`}>
      <header className="game-header">
        <button className="wordmark" onClick={() => navigate(run ? `run/${run.id}` : "")} aria-label="AutoPTU Career home">
          <span>AUTO</span>PTU <b>CAREER</b>
        </button>
        <div className="header-meta">
          {run ? <span className="save-light"><i /> season {run.season_number}</span> : <span>PTU 1.05</span>}
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
