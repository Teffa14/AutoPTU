import { effectLabel } from "../decisionPresentation";
import { achievementLabel } from "../achievementPresentation";
import type { CareerRun, Locale } from "../types";

interface TimelineDecision {
  label: string;
  effects: Record<string, unknown>;
}

export function timelineSeasonDecisions(entry: Record<string, unknown>): TimelineDecision[] {
  if (Array.isArray(entry.decisions)) {
    return entry.decisions.flatMap((value) => {
      const decision = asRecord(value);
      const label = String(decision.label ?? "").trim();
      return label ? [{ label, effects: asRecord(decision.effects) }] : [];
    });
  }
  const label = String(entry.decision ?? "").trim();
  return label ? [{ label, effects: asRecord(entry.decision_effects) }] : [];
}

export function TimelineScreen({ run, locale }: { run: CareerRun; locale: Locale }) {
  return (
    <section className="timeline-scene">
      <header className="career-book-cover">
        <p className="eyebrow">{run.build.name} · {locale === "es" ? "libro de carrera" : "career book"}</p>
        <h1>{locale === "es" ? "Lo que decidió. Lo que consiguió." : "What they chose. What they achieved."}</h1>
        <p>{locale === "es" ? "Una historia compacta de temporadas, decisiones, capturas y evolución." : "A compact history of seasons, decisions, captures and growth."}</p>
      </header>

      {run.status === "retired" ? <FinalCareerSheet run={run} locale={locale} /> : null}

      <div className="timeline-track">
        {run.timeline.map((entry, index) => {
          const decisions = timelineSeasonDecisions(entry);
          const pokemonUsed = Array.isArray(entry.pokemon_used) ? entry.pokemon_used.map(String) : [];
          const unlocked = Array.isArray(entry.new_achievements) ? entry.new_achievements.map(String) : [];
          const majorHighlight = entry.title === true || entry.promoted === true || unlocked.length > 0;
          return (
            <article className={`timeline-entry type-${String(entry.type).replaceAll(".", "-")} ${majorHighlight ? "major-highlight" : ""}`} key={`${String(entry.type)}-${index}`}>
              <div className="timeline-age"><b>{String(entry.age ?? run.age)}</b><small>{locale === "es" ? "años" : "years"}</small></div>
              <div className="timeline-entry-copy">
                <span>{eventKind(entry, locale)}</span>
                <h2>{eventTitle(entry, locale)}</h2>
                {entry.record ? <p className="season-record">{String(entry.league)} · {String(entry.record)} · score {signed(Number(entry.score_delta ?? 0))}</p> : null}
                {decisions.length ? (
                  <div className="decision-ledger">
                    <b>{locale === "es" ? (decisions.length > 1 ? "Decisiones" : "Decisión") : (decisions.length > 1 ? "Decisions" : "Decision")}</b>
                    {decisions.map((decision, decisionIndex) => (
                      <div key={`${decision.label}-${decisionIndex}`}>
                        <strong>{decision.label}</strong>
                        <small>{effectSummary(decision.effects, locale)}</small>
                      </div>
                    ))}
                  </div>
                ) : null}
                {pokemonUsed.length ? <p className="pokemon-used"><b>{locale === "es" ? "Jugaron" : "Played"}</b>{pokemonUsed.map((species) => <span key={species}>{species}</span>)}</p> : null}
                {unlocked.length ? <div className="timeline-achievements"><b>{locale === "es" ? "Logros desbloqueados" : "Achievements unlocked"}</b>{unlocked.map((entry) => <span key={entry}>◆ {achievementLabel(entry, locale)}</span>)}</div> : null}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function FinalCareerSheet({ run, locale }: { run: CareerRun; locale: Locale }) {
  const summary = run.summary;
  const evolutions = run.pokemon.reduce((total, pokemon) => total + pokemon.evolution_history.length, 0);
  const clubs = Array.from(new Set(run.timeline.filter((entry) => entry.type === "season.completed").map((entry) => String(entry.club ?? "")).filter(Boolean)));
  return (
    <section className="final-career-sheet" aria-labelledby="final-career-title">
      <header><div><p className="eyebrow">{locale === "es" ? "Registro final" : "Final record"}</p><h2 id="final-career-title">{locale === "es" ? "La carrera en números" : "The career in numbers"}</h2></div><strong>{run.score}<small>score</small></strong></header>
      <div className="final-stat-grid">
        <span><b>{summary?.seasons ?? run.season_number - 1}</b>{locale === "es" ? "temporadas" : "seasons"}</span>
        <span><b>{run.totals.wins}–{run.totals.losses}–{run.totals.draws}</b>W–L–D</span>
        <span><b>{run.totals.titles}</b>{locale === "es" ? "títulos" : "titles"}</span>
        <span><b>{summary?.highest_league ?? run.league}</b>{locale === "es" ? "máxima liga" : "highest league"}</span>
        <span><b>{summary?.final_age ?? run.age}</b>{locale === "es" ? "edad final" : "final age"}</span>
        <span><b>{run.pokemon.length}</b>{locale === "es" ? "Pokémon" : "Pokémon"}</span>
        <span><b>{evolutions}</b>{locale === "es" ? "evoluciones" : "evolutions"}</span>
        <span><b>{run.build.starter}</b>{locale === "es" ? "compañero final" : "final partner"}</span>
      </div>
      {clubs.length ? <p className="club-history"><b>{locale === "es" ? "Clubes" : "Clubs"}</b>{clubs.join(" · ")}</p> : null}
      <div className="final-achievements"><b>{locale === "es" ? "Logros" : "Achievements"}</b>{run.achievements.length ? run.achievements.map((achievement) => <span key={achievement}>{achievementLabel(achievement, locale)}</span>) : <small>{locale === "es" ? "Sin títulos registrados." : "No recorded titles."}</small>}</div>
    </section>
  );
}

function eventKind(entry: Record<string, unknown>, locale: Locale): string {
  const type = String(entry.type ?? "");
  const labels: Record<string, [string, string]> = {
    "career.started": ["inicio", "start"],
    "pokemon.captured": ["capturas", "captures"],
    "pokemon.evolved": ["evolución", "evolution"],
    "pokemon.trained": ["entrenamiento", "training"],
    "pokemon.move_learned": ["movimiento", "move learned"],
    "item.acquired": ["objeto", "item"],
    "relationship.changed": ["relación", "relationship"],
    "relationship.effect_applied": ["red de apoyo", "support network"],
    "relationship.contract_saved": ["contrato", "contract"],
    "class.effect_applied": ["clase PTU", "PTU class"],
    "season.schedule_ready": ["calendario", "schedule"],
    "roster.lineup_changed": ["alineación", "lineup"],
    "season.completed": ["temporada", "season"],
    "career.retired": ["retiro", "retirement"],
    "career.version_migrated": ["actualización", "update"],
  };
  return labels[type]?.[locale === "es" ? 0 : 1] ?? type.replace(".", " / ");
}

export function eventTitle(entry: Record<string, unknown>, locale: Locale): string {
  const type = String(entry.type ?? "");
  if (type === "career.started") {
    const structured = entry.trainer && entry.club && entry.starter
      ? { trainer: String(entry.trainer), club: String(entry.club), starter: String(entry.starter) }
      : parseLegacyStart(String(entry.label ?? ""));
    if (structured) return locale === "es"
      ? `${structured.trainer} empezó en ${structured.club} junto a ${structured.starter}`
      : `${structured.trainer} joined ${structured.club} with ${structured.starter}`;
  }
  if (type === "pokemon.captured" && Array.isArray(entry.species)) {
    const names = entry.species.map(String).join(", ");
    return locale === "es" ? `Se sumaron ${names}` : `Caught ${names}`;
  }
  if (type === "pokemon.evolved") {
    return locale === "es"
      ? `${String(entry.from)} evolucionó a ${String(entry.to)} en el nivel ${String(entry.level)}`
      : `${String(entry.from)} evolved into ${String(entry.to)} at level ${String(entry.level)}`;
  }
  if (type === "pokemon.trained") {
    const levels = Number(entry.levels ?? 0);
    return locale === "es"
      ? `${String(entry.species)} ganó ${levels} ${levels === 1 ? "nivel" : "niveles"}`
      : `${String(entry.species)} gained ${levels} ${levels === 1 ? "level" : "levels"}`;
  }
  if (type === "pokemon.move_learned") return locale === "es" ? `${String(entry.species)} aprendió ${String(entry.move)}` : `${String(entry.species)} learned ${String(entry.move)}`;
  if (type === "item.acquired") return locale === "es" ? `Conseguiste ${String(entry.quantity)} × ${String(entry.item)}` : `Received ${String(entry.quantity)} × ${String(entry.item)}`;
  if (type === "relationship.changed") return locale === "es" ? `El vínculo con ${String(entry.name).split(" · ")[0]} cambió ${signed(Number(entry.amount ?? 0))}` : `Bond with ${String(entry.name).split(" · ")[0]} changed ${signed(Number(entry.amount ?? 0))}`;
  if (type === "relationship.effect_applied") return locale === "es" ? `La red aportó +${String(entry.home_level_bonus ?? 0)} LV y +${String(entry.recovery_applied ?? 0)} salud` : `The network supplied +${String(entry.home_level_bonus ?? 0)} LV and +${String(entry.recovery_applied ?? 0)} health`;
  if (type === "relationship.contract_saved") return locale === "es" ? `${String(entry.name).split(" · ")[0]} protegió el contrato` : `${String(entry.name).split(" · ")[0]} protected the contract`;
  if (type === "class.effect_applied") {
    const classes = Array.isArray(entry.classes) ? entry.classes.map(String).join(" + ") : (locale === "es" ? "Clase PTU" : "PTU class");
    const seasonEffects = asRecord(entry.season_effects);
    const partnerLevels = Number(seasonEffects.partner_levels ?? 0);
    if (partnerLevels) return locale === "es"
      ? `${classes} dio +${partnerLevels} ${partnerLevels === 1 ? "nivel" : "niveles"} al compañero`
      : `${classes} gave the partner +${partnerLevels} ${partnerLevels === 1 ? "level" : "levels"}`;
    const summary = effectSummary(seasonEffects, locale);
    return locale === "es" ? `${classes} modificó la preparación: ${summary}` : `${classes} changed preparation: ${summary}`;
  }
  if (type === "season.schedule_ready") return locale === "es" ? "El equipo salió al campo" : "The team entered the field";
  if (type === "roster.lineup_changed") return locale === "es" ? "Se registraron los seis titulares" : "The starting six were registered";
  if (type === "career.retired") return locale === "es" ? "La carrera quedó cerrada" : "The career came to an end";
  if (type === "career.version_migrated") return locale === "es" ? "Las reglas de carrera se actualizaron" : "Career rules were updated";
  return String(entry.label ?? entry.club ?? entry.reason ?? (locale === "es" ? "Temporada registrada" : "Season recorded"));
}

function effectSummary(effects: Record<string, unknown>, locale: Locale): string {
  const pieces = Object.entries(effects).flatMap(([key, value]) => {
    if (key === "rewards" && Array.isArray(value)) return value.flatMap((entry) => {
      const reward = asRecord(entry);
      if (reward.type === "pokemon") return [`${locale === "es" ? "captura" : "caught"}: ${String(reward.species)}`];
      if (reward.type === "item") return [`${String(reward.item)} × ${String(reward.quantity)}`];
      if (reward.type === "move") return [`${locale === "es" ? "movimiento" : "move"}: ${String(reward.move)}`];
      if (reward.type === "relationship") return [`${locale === "es" ? "vínculo" : "bond"}: ${String(reward.name).split(" · ")[0]}`];
      if (reward.type === "level") return [`+${String(reward.levels)} LV`];
      return [];
    });
    if (key === "gamble_success") return [value ? (locale === "es" ? "La apuesta salió bien" : "The gamble succeeded") : (locale === "es" ? "La apuesta falló" : "The gamble failed")];
    if (typeof value !== "number") return [];
    return [`${effectLabel(key, locale)} ${signed(value)}`];
  });
  return pieces.join(" · ") || (locale === "es" ? "Sin cambios directos" : "No direct changes");
}

function signed(value: number): string { return `${value >= 0 ? "+" : ""}${value}`; }
function asRecord(value: unknown): Record<string, unknown> { return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {}; }
function parseLegacyStart(label: string): { trainer: string; club: string; starter: string } | null {
  const match = label.match(/^(.+) joined (.+) with (.+)\.$/);
  return match ? { trainer: match[1], club: match[2], starter: match[3] } : null;
}
