import { useEffect, useState } from "react";
import { careerApi } from "../api";
import type { Locale } from "../types";
import { PokemonSprite } from "./PokemonSprite";

export function ShareScreen({ shareId, locale }: { shareId: string; locale: Locale }) {
  const [payload, setPayload] = useState<{ summary: Record<string, unknown>; has_replay: boolean } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    careerApi.publicShare(shareId).then(setPayload).catch((reason: Error) => setError(reason.message));
  }, [shareId]);
  if (error) return <section className="shared-career"><h1>{locale === "es" ? "Registro no disponible" : "Record unavailable"}</h1><p>{error}</p></section>;
  if (!payload) return <div className="scene-loading">Opening league archive…</div>;
  const summary = payload.summary;
  const totals = (summary.totals as Record<string, number> | undefined) ?? {};
  const achievements = (summary.achievements as string[] | undefined) ?? [];
  return (
    <section className="shared-career">
      <p className="eyebrow">PUBLIC LEAGUE ARCHIVE · {String(summary.region ?? "").toUpperCase()}</p>
      <PokemonSprite name={String(summary.starter ?? "Rattata")} className="shared-partner" />
      <h1>{String(summary.trainer ?? "Trainer")}</h1>
      <p>{locale === "es" ? `Retiro a los ${String(summary.final_age ?? "—")}` : `Retired at ${String(summary.final_age ?? "—")}`}</p>
      <div className="shared-score"><b>{String(summary.score ?? 0)}</b><span>competitive score</span></div>
      <div className="record-ribbon"><span>{totals.wins ?? 0} W</span><span>{totals.losses ?? 0} L</span><span>{totals.titles ?? 0} titles</span></div>
      {achievements.length ? <ul>{achievements.map((entry) => <li key={entry}>{entry}</li>)}</ul> : null}
      <small>{payload.has_replay ? "VERIFIED REPLAY ATTACHED" : "CAREER CARD ONLY"}</small>
    </section>
  );
}
