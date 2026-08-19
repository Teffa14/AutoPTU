import { useEffect, useState } from "react";

import { careerApi, type PreseasonSnapshot } from "../api";
import type { CareerRun, Locale } from "../types";
import { PokemonSprite } from "./PokemonSprite";
import "./preseason-market.css";

interface Props {
  run: CareerRun;
  locale: Locale;
  onRun: (run: CareerRun) => void;
  onClubReady: (ready: boolean) => void;
}

export function PreseasonMarket({ run, locale, onRun, onClubReady }: Props) {
  const [snapshot, setSnapshot] = useState<PreseasonSnapshot | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (run.status !== "active" || run.season?.status !== "decision" || (run.season?.decisions_completed ?? 0) > 0) {
      setSnapshot(null);
      onClubReady(true);
      return;
    }
    let active = true;
    setError("");
    careerApi.preseason(run.id).then((value) => {
      if (!active) return;
      if (value.run && value.run.revision !== run.revision) onRun(value.run);
      setSnapshot(value);
      onClubReady(value.club_completed);
    }).catch((reason: Error) => {
      if (!active) return;
      setError(reason.message);
      onClubReady(true);
    });
    return () => { active = false; };
  }, [onClubReady, onRun, run.id, run.season?.decisions_completed, run.season?.status, run.status, run.revision]);

  async function mutate(key: string, action: () => Promise<CareerRun>) {
    setBusy(key);
    setError("");
    try {
      const next = await action();
      onRun(next);
      const fresh = await careerApi.preseason(next.id);
      if (fresh.run) onRun(fresh.run);
      setSnapshot(fresh);
      onClubReady(fresh.club_completed);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy("");
    }
  }

  if (!snapshot) {
    if (!error) return null;
    return <section className="preseason-market compact-error"><p role="alert">{error}</p></section>;
  }
  const allClosed = snapshot.club_completed && snapshot.sponsor_completed && snapshot.capture_completed;
  if (allClosed) return null;

  return (
    <section className="preseason-market" aria-label={locale === "es" ? "Mercado de temporada" : "Season market"}>
      <header className="preseason-heading">
        <div><span>{locale === "es" ? `TEMPORADA ${run.season_number}` : `SEASON ${run.season_number}`}</span><h2>{locale === "es" ? "Mercado de pretemporada" : "Preseason market"}</h2></div>
        <p>{locale === "es" ? "Elegí club. Después podés firmar sponsor y usar una oportunidad de captura antes de cerrar tu primera decisión." : "Choose a club. Then you can sign a sponsor and use one capture opportunity before committing your first decision."}</p>
      </header>

      {!snapshot.club_completed ? (
        <div className="market-block club-market">
          <div className="market-title"><b>{locale === "es" ? "Elegí club" : "Choose a club"}</b><span>{locale === "es" ? "Obligatorio para esta temporada" : "Required for this season"}</span></div>
          <div className="market-grid club-grid">
            {snapshot.club_offers.map((offer) => (
              <article key={offer.id} className="market-card club-card">
                <span className="market-tag">{offer.renewal ? (locale === "es" ? "RENOVACIÓN" : "RENEWAL") : (locale === "es" ? "OFERTA" : "OFFER")}</span>
                <h3>{offer.club_name}</h3>
                <strong>₽ {offer.salary} <small>/{locale === "es" ? "temporada" : "season"}</small></strong>
                <p>{offer.perk.label}: +{offer.perk.amount} {marketStat(offer.perk.stat, locale)}</p>
                <div className="loan-strip">
                  <small>{locale === "es" ? "PRÉSTAMOS DEL CLUB" : "CLUB LOANS"}</small>
                  {offer.loan_species.map((species) => <span key={species}><PokemonSprite name={species} className="market-sprite" /><b>{species}</b></span>)}
                </div>
                <button disabled={Boolean(busy)} onClick={() => mutate(`club:${offer.id}`, () => careerApi.chooseClub(run, offer.id))}>{busy === `club:${offer.id}` ? (locale === "es" ? "Firmando…" : "Signing…") : (locale === "es" ? "Firmar por la temporada" : "Sign for the season")}</button>
              </article>
            ))}
          </div>
          <p className="market-note">{locale === "es" ? "Los Pokémon cedidos pueden entrar en tu equipo de seis, pero regresan al club cuando cambies de contrato. No cuentan como capturas permanentes." : "Loan Pokémon may enter your active six, but return to the club when you change contracts. They do not count as permanent captures."}</p>
        </div>
      ) : null}

      {snapshot.club_completed && !snapshot.sponsor_completed ? (
        <div className="market-block sponsor-market">
          <div className="market-title"><b>{locale === "es" ? "Sponsors interesados" : "Interested sponsors"}</b><span>{locale === "es" ? "Opcional" : "Optional"}</span></div>
          <div className="market-grid sponsor-grid">
            {snapshot.sponsor_offers.map((offer) => (
              <article key={offer.id} className="market-card sponsor-card">
                <span className="market-tag">{offer.theme.toUpperCase()}</span><h3>{offer.name}</h3>
                <strong>₽ {offer.upfront} <small>{locale === "es" ? "al firmar" : "up front"}</small></strong>
                <p>{locale === "es" ? offer.description_es : offer.description_en}</p>
                <em>+ ₽ {offer.bonus} {locale === "es" ? "si cumplís" : "if completed"}</em>
                <button disabled={Boolean(busy)} onClick={() => mutate(`sponsor:${offer.id}`, () => careerApi.chooseSponsor(run, offer.id))}>{busy === `sponsor:${offer.id}` ? (locale === "es" ? "Firmando…" : "Signing…") : (locale === "es" ? "Firmar sponsor" : "Sign sponsor")}</button>
              </article>
            ))}
          </div>
          <button className="market-skip" disabled={Boolean(busy)} onClick={() => mutate("sponsor:skip", () => careerApi.chooseSponsor(run, ""))}>{locale === "es" ? "Seguir sin sponsor" : "Continue without sponsor"}</button>
        </div>
      ) : null}

      {snapshot.club_completed && !snapshot.capture_completed ? (
        <div className="market-block capture-market">
          <div className="market-title"><b>{locale === "es" ? "Salida de captura" : "Capture outing"}</b><span>{run.build.pokeballs} Poké Balls · {locale === "es" ? "una elección" : "one choice"}</span></div>
          <div className="capture-grid">
            {snapshot.capture_candidates.map((candidate) => (
              <button key={candidate.id} className="capture-card" disabled={Boolean(busy) || run.build.pokeballs < candidate.ball_cost} onClick={() => mutate(`capture:${candidate.id}`, () => careerApi.capture(run, candidate.id))}>
                <PokemonSprite name={candidate.species} className="capture-sprite" />
                <b>{candidate.species}</b><span>{rarityLabel(candidate.rarity, locale)}</span><small>{candidate.ball_cost} Poké Ball</small>
              </button>
            ))}
          </div>
          <p className="market-note">{locale === "es" ? "Aunque ya tengas seis Pokémon, podés seguir capturando. Si el equipo activo está lleno, la captura va al PC." : "You can keep catching Pokémon after owning six. When the active team is full, the capture goes to PC."}</p>
        </div>
      ) : null}
      {error ? <p className="form-error" role="alert">{error}</p> : null}
    </section>
  );
}

function rarityLabel(rarity: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = { common: ["común", "common"], rare: ["raro", "rare"], very_rare: ["muy raro", "very rare"], epic: ["épico", "epic"], legendary: ["legendario", "legendary"], mythical: ["mítico", "mythical"] };
  return labels[rarity]?.[locale === "es" ? 0 : 1] ?? rarity;
}

function marketStat(stat: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = { development: ["desarrollo", "development"], scouting: ["scouting", "scouting"], reputation: ["reputación", "reputation"], health: ["salud", "health"] };
  return labels[stat]?.[locale === "es" ? 0 : 1] ?? stat;
}
