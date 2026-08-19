import { useEffect, useState } from "react";

import type { CareerRun, Locale } from "../types";
import { PreseasonMarket } from "./PreseasonMarket";
import { SeasonScreen } from "./SeasonScreen";

export function SeasonHub({ run, locale, onRun }: { run: CareerRun; locale: Locale; onRun: (run: CareerRun) => void }) {
  const needsMarket = run.status === "active" && run.season?.status === "decision" && (run.season?.decisions_completed ?? 0) === 0;
  const [clubReady, setClubReady] = useState(!needsMarket);

  useEffect(() => {
    setClubReady(!needsMarket);
  }, [needsMarket, run.season_number]);

  return <>
    {needsMarket ? <PreseasonMarket run={run} locale={locale} onRun={onRun} onClubReady={setClubReady} /> : null}
    {clubReady ? <SeasonScreen run={run} locale={locale} onRun={onRun} /> : <div className="preseason-gate">{locale === "es" ? "Elegí el club de esta temporada para abrir el calendario." : "Choose this season's club to open the schedule."}</div>}
  </>;
}
