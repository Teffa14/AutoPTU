import { useEffect, useMemo, useState } from "react";
import { careerApi } from "../api";
import { navigate } from "../App";
import { t } from "../i18n";
import { saveReplay } from "../replayStore";
import type { BattleTranscript, Locale } from "../types";
import { BattleArena } from "./BattleArena";
import { PokemonSprite } from "./PokemonSprite";

export default function BattleScreen({ runId, battleId, locale }: { runId: string; battleId: string; locale: Locale }) {
  const copy = t(locale);
  const [transcript, setTranscript] = useState<BattleTranscript | null>(null);
  const [eventIndex, setEventIndex] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    careerApi.battle(runId, battleId).then(async (value) => {
      if (!active) return;
      setTranscript(value);
      await saveReplay(value);
    }).catch((reason: Error) => active && setError(reason.message));
    return () => { active = false; };
  }, [runId, battleId]);
  useEffect(() => {
    if (!transcript || eventIndex >= transcript.events.length - 1) return;
    const timer = window.setTimeout(() => setEventIndex((current) => current + 1), 780 / speed);
    return () => window.clearTimeout(timer);
  }, [eventIndex, speed, transcript]);
  const event = transcript?.events[eventIndex];
  const commentary = useMemo(() => event ? String(event.description ?? event.move ?? event.effect ?? event.type ?? "The shape of the match changes.") : "", [event]);
  if (error) return <section className="battle-error"><h1>Replay unavailable</h1><p>{error}</p><button onClick={() => navigate(`run/${runId}`)}>{copy.back}</button></section>;
  if (!transcript) return <div className="scene-loading">Opening stadium feed…</div>;
  const complete = eventIndex >= transcript.events.length - 1;
  return (
    <section className="battle-scene">
      <header className="broadcast-header"><button onClick={() => navigate(`run/${runId}`)}>← {copy.back}</button><div><span>LIVE / {transcript.spec.region}</span><b>{transcript.spec.home_club} <i>vs</i> {transcript.spec.away_club}</b></div><strong>R{Math.max(1, Math.round((eventIndex / Math.max(1, transcript.events.length)) * transcript.rounds))}</strong></header>
      <div className="arena-wrap"><BattleArena transcript={transcript} eventIndex={eventIndex} complete={complete} /></div>
      <div className="broadcast-lower">
        <div className="combatants-strip"><span><PokemonSprite name={transcript.spec.home_species} className="combatant-sprite" decorative /><b>{transcript.spec.home_species}</b></span><em>{transcript.winner_label ? `${transcript.winner_label} wins` : "PTU AUTO"}</em><span><b>{transcript.spec.away_species}</b><PokemonSprite name={transcript.spec.away_species} className="combatant-sprite" decorative /></span></div>
        <blockquote>{commentary}</blockquote>
        <div className="playback-controls"><span>{eventIndex + 1}/{transcript.events.length}</span><button onClick={() => setSpeed((value) => value === 1 ? 2 : 1)}>{copy.speed} {speed}×</button><button onClick={() => setEventIndex(transcript.events.length - 1)}>{copy.skip}</button></div>
      </div>
      <footer className="verification-stamp"><span>SERVER VERIFIED</span><code>{transcript.sha256.slice(0, 20)}</code></footer>
    </section>
  );
}
