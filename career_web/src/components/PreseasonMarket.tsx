import { useEffect, useState } from "react";

import { careerApi, type PreseasonSnapshot } from "../api";
import { sponsorRenewalContext } from "../sponsorRenewalPresentation";
import type { CareerRun, Locale } from "../types";
import { ClubTransitionBrief } from "./ClubTransitionBrief";
import { PokemonSprite } from "./PokemonSprite";
import "./preseason-market.css";

interface Props {
  run: CareerRun;
  locale: Locale;
  onRun: (run: CareerRun) => void;
  onClubReady: (ready: boolean) => void;
}

interface ReturningLoan {
  id: string;
  species: string;
  club_id: string;
  club_name: string;
  active: boolean;
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
      onClubReady(false);
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
        <p>{locale === "es" ? "Si tu contrato sigue vigente, continuás con el mismo club y equipo cedido. Cuando vence, podés renovar o cambiar. Después resolvés sponsor y captura." : "If your contract is still active, you keep the same club and loan squad. When it expires, renew or move. Then resolve sponsor and capture."}</p>
      </header>

      {snapshot.club_completed ? <ClubTransitionBrief run={run} locale={locale} /> : null}

      {!snapshot.club_completed ? (
        <div className="market-block club-market">
          <div className="market-title"><b>{locale === "es" ? "Contrato de club" : "Club contract"}</b><span>{locale === "es" ? "Elegí continuidad o cambio" : "Choose continuity or a move"}</span></div>
          <div className="market-grid club-grid">
            {snapshot.club_offers.map((offer) => {
              const enhanced = offer as typeof offer & { gift_species?: string; gift_rarity?: string; retains_current_team?: boolean; returning_loans?: ReturningLoan[] };
              const returningLoans = enhanced.returning_loans ?? [];
              const returnClub = returningLoans[0]?.club_name ?? run.contract?.club_name ?? "";
              return (
                <article key={offer.id} className={`market-card club-card ${offer.renewal ? "renewal-card" : ""}`}>
                  <span className="market-tag">{offer.renewal ? (locale === "es" ? "EXTENSIÓN" : "EXTENSION") : (locale === "es" ? "OFERTA" : "OFFER")}</span>
                  <h3>{offer.club_name}</h3>
                  <strong>₽ {offer.salary} <small>/{locale === "es" ? "temporada" : "season"}</small></strong>
                  <p>{offer.perk.label}: +{offer.perk.amount} {marketStat(offer.perk.stat, locale)}</p>
                  {offer.renewal ? <p className="renewal-copy">{locale === "es" ? `Extendés ${offer.seasons} temporadas y mantenés los Pokémon cedidos actuales.` : `Extend for ${offer.seasons} seasons and keep the current loan Pokémon.`}</p> : null}
                  {returningLoans.length ? (
                    <div className="loan-return-warning">
                      <small>{locale === "es" ? `SI FIRMÁS, VUELVEN A ${returnClub}` : `IF YOU SIGN, RETURN TO ${returnClub}`}</small>
                      <div>{returningLoans.map((pokemon) => <span key={pokemon.id}><PokemonSprite name={pokemon.species} className="market-sprite" /><b>{pokemon.species}</b>{pokemon.active ? <em>{locale === "es" ? "ACTIVO" : "ACTIVE"}</em> : null}</span>)}</div>
                      <p>{locale === "es" ? "Salen de tu plantel al cambiar de club. Su paso por tu carrera queda registrado y no cuenta como captura permanente." : "They leave your squad when you change clubs. Their career history remains recorded and they do not count as permanent captures."}</p>
                    </div>
                  ) : null}
                  <div className="loan-strip">
                    <small>{locale === "es" ? "PLANTEL CEDIDO" : "LOAN SQUAD"}</small>
                    {offer.loan_species.map((species) => <span key={species}><PokemonSprite name={species} className="market-sprite" /><b>{species}</b></span>)}
                  </div>
                  {enhanced.gift_species ? (
                    <div className="club-gift">
                      <small>{locale === "es" ? "REGALO DE FIRMA · PERMANENTE" : "SIGNING GIFT · PERMANENT"}</small>
                      <span><PokemonSprite name={enhanced.gift_species} className="market-sprite gift-sprite" /><b>{enhanced.gift_species}</b><em>{rarityLabel(enhanced.gift_rarity ?? "common", locale)}</em></span>
                    </div>
                  ) : null}
                  <button disabled={Boolean(busy)} onClick={() => mutate(`club:${offer.id}`, () => careerApi.chooseClub(run, offer.id))}>{busy === `club:${offer.id}` ? (locale === "es" ? "Firmando…" : "Signing…") : offer.renewal ? (locale === "es" ? `Extender ${offer.seasons} temporadas` : `Extend ${offer.seasons} seasons`) : (locale === "es" ? "Firmar contrato" : "Sign contract")}</button>
                </article>
              );
            })}
          </div>
          <p className="market-note">{locale === "es" ? "El regalo de firma es tuyo para siempre. Su rareza mejora con la liga. Los Pokémon cedidos pertenecen al club y sólo se devuelven al cambiar de club o al terminar el vínculo." : "The signing gift is permanently yours and its rarity improves with league level. Loan Pokémon belong to the club and only return when you move or the relationship ends."}</p>
        </div>
      ) : null}

      {snapshot.club_completed && !snapshot.sponsor_completed ? (
        <div className="market-block sponsor-market">
          <div className="market-title"><b>{locale === "es" ? "Sponsors interesados" : "Interested sponsors"}</b><span>{locale === "es" ? "Opcional" : "Optional"}</span></div>
          <div className="market-grid sponsor-grid">
            {snapshot.sponsor_offers.map((offer) => {
              const enhanced = offer as typeof offer & { renewal?: boolean };
              const renewal = sponsorRenewalContext(enhanced, run.timeline, run.season_number, locale);
              return (
                <article key={offer.id} className={`market-card sponsor-card ${enhanced.renewal ? "renewal-card" : ""}`}>
                  <span className="market-tag">{enhanced.renewal ? (locale === "es" ? "RENOVACIÓN" : "RENEWAL") : offer.theme.toUpperCase()}</span>
                  <h3>{offer.name}</h3>
                  <strong>₽ {offer.upfront} <small>{locale === "es" ? "al firmar" : "up front"}</small></strong>
                  {renewal ? <p className="renewal-copy"><b>{renewal.relationshipLabel}</b><br />{renewal.resultLabel}</p> : null}
                  <p>{locale === "es" ? offer.description_es : offer.description_en}</p>
                  <em>+ ₽ {offer.bonus} {locale === "es" ? "si cumplís" : "if completed"}</em>
                  <button disabled={Boolean(busy)} onClick={() => mutate(`sponsor:${offer.id}`, () => careerApi.chooseSponsor(run, offer.id))}>{busy === `sponsor:${offer.id}` ? (locale === "es" ? "Firmando…" : "Signing…") : enhanced.renewal ? (locale === "es" ? "Renovar sponsor" : "Renew sponsor") : (locale === "es" ? "Firmar sponsor" : "Sign sponsor")}</button>
                </article>
              );
            })}
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
          <button className="market-skip" disabled={Boolean(busy)} onClick={() => mutate("capture:skip", () => careerApi.capture(run, ""))}>{busy === "capture:skip" ? (locale === "es" ? "Cerrando salida…" : "Closing outing…") : (locale === "es" ? "Guardar Poké Balls y seguir" : "Keep Poké Balls and continue")}</button>
          <p className="market-note">{locale === "es" ? "La captura es opcional. Aunque ya tengas seis Pokémon, podés seguir capturando; si el equipo activo está lleno, la captura va al PC." : "Capturing is optional. You can keep catching Pokémon after owning six; when the active team is full, the capture goes to PC."}</p>
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
