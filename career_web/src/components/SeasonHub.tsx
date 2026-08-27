import { useEffect, useState } from "react";

import { isGambleHistoryEntry, normalizedDecisionHistory, type DecisionHistoryEntry } from "../decisionOutcome";
import { normalizeSeasonRosterState, pendingBattleRecovery } from "../seasonRecovery";
import type { CareerRun, Locale } from "../types";
import { DecisionOutcomePanel } from "./DecisionOutcomePanel";
import { PendingBattleRecovery } from "./PendingBattleRecovery";
import { PreseasonMarket } from "./PreseasonMarket";
import { SeasonScreen } from "./SeasonScreen";

export function SeasonHub({ run, locale, onRun }: { run: CareerRun; locale: Locale; onRun: (run: CareerRun) => void }) {
  const seasonRun = normalizeSeasonRosterState(run);
  const pendingBattle = pendingBattleRecovery(seasonRun);
  const needsMarket = seasonRun.status === "active" && seasonRun.season?.status === "decision" && (seasonRun.season?.decisions_completed ?? 0) === 0;
  const hasAvailablePokemon = seasonRun.pokemon.some((pokemon) => pokemon.status !== "retired" && pokemon.career_health > 0);
  const history = normalizedDecisionHistory(seasonRun.season?.decision_history);
  const historyCount = history.length;
  const latestDecision = history.at(-1) as DecisionHistoryEntry | undefined;
  const [clubReady, setClubReady] = useState(!needsMarket);
  const [acknowledgedDecisions, setAcknowledgedDecisions] = useState(historyCount);

  useEffect(() => {
    setClubReady(!needsMarket);
  }, [needsMarket, seasonRun.season_number]);

  useEffect(() => {
    setAcknowledgedDecisions(historyCount);
  }, [seasonRun.id, seasonRun.season_number]);

  if (pendingBattle) return <PendingBattleRecovery run={seasonRun} locale={locale} onRun={onRun} />;

  const showOutcome = seasonRun.season?.status === "decision"
    && Boolean(latestDecision)
    && historyCount > acknowledgedDecisions
    && !isGambleHistoryEntry(latestDecision);

  if (showOutcome && latestDecision) {
    return <DecisionOutcomePanel entry={latestDecision} locale={locale} onContinue={() => setAcknowledgedDecisions(historyCount)} />;
  }

  const seasonReady = clubReady && hasAvailablePokemon;

  return <>
    {needsMarket ? <PreseasonMarket run={seasonRun} locale={locale} onRun={onRun} onClubReady={setClubReady} /> : null}
    {seasonReady ? <SeasonScreen run={seasonRun} locale={locale} onRun={onRun} /> : <div className="preseason-gate">{!clubReady
      ? (locale === "es" ? "Elegí el club de esta temporada para abrir el calendario." : "Choose this season's club to open the schedule.")
      : (locale === "es" ? "Necesitás al menos un Pokémon disponible. Recuperá el plantel desde el scouting de pretemporada antes de abrir el calendario." : "You need at least one available Pokémon. Rebuild the squad through preseason scouting before opening the schedule.")}</div>}
  </>;
}
