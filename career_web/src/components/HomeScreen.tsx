import { useEffect, useState } from "react";

import { navigate } from "../App";
import type { Locale } from "../types";

type HomeDestination = "new" | "daily" | "leaderboard";

const warmDestination: Record<HomeDestination, () => Promise<unknown>> = {
  new: () => import("./CreateScreen"),
  daily: () => import("./DailyScreen"),
  leaderboard: () => import("./DailyScreen"),
};

function warmHomeRoute(destination: HomeDestination): void {
  void warmDestination[destination]().catch(() => undefined);
}

export function HomeScreen({ locale }: { locale: Locale }) {
  const [lastRunId, setLastRunId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void import("../localCareer").then(({ loadLastLocalRunId }) => {
      if (active) setLastRunId(loadLastLocalRunId());
    }).catch(() => undefined);
    return () => { active = false; };
  }, []);

  return (
    <section className="career-home">
      <div className="career-home-copy">
        <p className="eyebrow">AUTO PTU · CAREER</p>
        <h1>{locale === "es" ? "Elegí cómo empieza tu historia" : "Choose how your story begins"}</h1>
        <p>{locale === "es" ? "Una carrera libre, el reto ranked del día o la clasificación pública." : "Play a normal career, enter today's ranked challenge, or inspect the public standings."}</p>
      </div>
      <div className="career-entry-grid">
        <button className="career-entry-card normal" onPointerEnter={() => warmHomeRoute("new")} onFocus={() => warmHomeRoute("new")} onClick={() => navigate("new")}>
          <small>{locale === "es" ? "TU MUNDO" : "YOUR WORLD"}</small>
          <strong>{locale === "es" ? "Carrera normal" : "Normal career"}</strong>
          <span>{locale === "es" ? "Elegí región, compañero, clase y ritmo. Jugá sin límite de intentos." : "Choose your region, partner, class, and pace. Play without attempt limits."}</span>
          <b>{locale === "es" ? "Crear carrera →" : "Create career →"}</b>
        </button>
        <button className="career-entry-card ranked" onPointerEnter={() => warmHomeRoute("daily")} onFocus={() => warmHomeRoute("daily")} onClick={() => navigate("daily")}>
          <small>{locale === "es" ? "RETO DIARIO" : "DAILY CHALLENGE"}</small>
          <strong>Ranked</strong>
          <span>{locale === "es" ? "Misma semilla y decisiones para todos. Requiere una cuenta permanente." : "The same seed and decisions for everyone. A permanent account is required."}</span>
          <b>{locale === "es" ? "Jugar ranked →" : "Play ranked →"}</b>
        </button>
        <button className="career-entry-card leaderboard" onPointerEnter={() => warmHomeRoute("leaderboard")} onFocus={() => warmHomeRoute("leaderboard")} onClick={() => navigate("leaderboard")}>
          <small>{locale === "es" ? "CLASIFICACIÓN" : "STANDINGS"}</small>
          <strong>Leaderboard</strong>
          <span>{locale === "es" ? "Compará los mejores resultados del reto simple y avanzado." : "Compare the best simple and advanced challenge results."}</span>
          <b>{locale === "es" ? "Ver tabla →" : "View standings →"}</b>
        </button>
      </div>
      {lastRunId ? <button className="continue-career" onClick={() => navigate(`run/${lastRunId}`)}>{locale === "es" ? "Continuar mi última carrera" : "Continue my last career"}</button> : null}
    </section>
  );
}
