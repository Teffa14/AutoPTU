import { useEffect, useState } from "react";

import { isGambleHistoryEntry, type DecisionHistoryEntry } from "../decisionOutcome";
import { pendingBattleRecovery } from "../seasonRecovery";
import type { CareerRun, Locale } from "../types";
import { DecisionOutcomePanel } from "./DecisionOutcomePanel";
import { PendingBattleRecovery } from "./PendingBattleRecovery";
import { PreseasonMarket } from "./PreseasonMarket";
import { SeasonScreen } from "./SeasonScreen";

export function SeasonHub({ run, locale, onRun }: { run: CareerRun; locale: Locale; onRun: (run: CareerRun) => void }) {
  const pendingBattle = pendingBattleRecovery(run);
  const needsMarket = run.status === "active" && run.season?.status === "decision" && (run.season?.decisions_completed ?? 0) === 0;
  const history = run.season?.decision_history ?? [];
  const historyCount = history.length;
  const latestDecision = history.at(-1) as DecisionHistoryEntry | undefined;
  const [clubReady, setClubReady] = useState(!needsMarket);
  const [acknowledgedDecisions, setAcknowledgedDecisions] = useState(historyCount);

  useEffect(() => {
    setClubReady(!needsMarket);
  }, [needsMarket, run.season_number]);

  useEffect(() => {
    setAcknowledgedDecisions(historyCount);
  }, [run.id, run.season_number]);

  if (pendingBattle) return <PendingBattleRecovery run={run} locale={locale} onRun={onRun} />;

  const showOutcome = run.season?.status === "decision"
    && Boolean(latestDecision)
    && historyCount > acknowledgedDecisions
    && !isGambleHistoryEntry(latestDecision);

  if (showOutcome && latestDecision) {
    return <DecisionOutcomePanel entry={latestDecision} locale={locale} onContinue={() => setAcknowledgedDecisions(historyCount)} />;
  }

  return <>
    {needsMarket ? <PreseasonMarket run={run} locale={locale} onRun={onRun} onClubReady={setClubReady} /> : null}
    {clubReady ? <SeasonScreen run={run} locale={locale} onRun={onRun} /> : <div className="preseason-gate">{locale === "es" ? "Elegí el club de esta temporada para abrir el calendario." : "Choose this season's club to open the schedule."}</div>}
  </>;
}