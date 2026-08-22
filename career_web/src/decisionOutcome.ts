import { effectLabel } from "./decisionPresentation";
import type { DecisionReward, Locale } from "./types";

export type DecisionHistoryEntry = {
  decision_id?: string;
  option_id?: string;
  label?: string;
  effects?: Record<string, unknown>;
};

export type DecisionOutcomeView = {
  family: string;
  choice: string;
  headline: string;
  body: string;
  changes: string[];
  gamble: boolean;
};

export function decisionOutcomeView(entry: DecisionHistoryEntry, locale: Locale): DecisionOutcomeView {
  const family = String(entry.option_id ?? "decision").split(":", 1)[0] || "decision";
  const effects = entry.effects && typeof entry.effects === "object" ? entry.effects : {};
  const gamble = typeof effects.gamble_success === "boolean";
  const wonGamble = effects.gamble_success === true;
  const changes = appliedChanges(effects, locale);
  const copy = OUTCOME_COPY[family]?.[locale] ?? OUTCOME_COPY.default[locale];

  return {
    family,
    choice: String(entry.label ?? (locale === "es" ? "Decisión registrada" : "Decision recorded")),
    headline: gamble ? (wonGamble ? copy.success : copy.failure) : copy.headline,
    body: changes.length
      ? copy.body
      : (locale === "es" ? "La decisión quedó registrada, pero no produjo un cambio permanente adicional." : "The decision was recorded, but it produced no additional permanent change."),
    changes,
    gamble,
  };
}

export function isGambleHistoryEntry(entry: DecisionHistoryEntry | undefined): boolean {
  return typeof entry?.effects?.gamble_success === "boolean";
}

function appliedChanges(effects: Record<string, unknown>, locale: Locale): string[] {
  const changes: string[] = [];
  for (const [key, value] of Object.entries(effects)) {
    if (key === "gamble_success" || key === "rewards") continue;
    if (typeof value !== "number" || value === 0) continue;
    changes.push(`${effectLabel(key, locale)} ${value > 0 ? "+" : ""}${value}`);
  }
  const rewards = Array.isArray(effects.rewards) ? effects.rewards as DecisionReward[] : [];
  for (const reward of rewards) changes.push(rewardLabel(reward, locale));
  return changes;
}

function rewardLabel(reward: DecisionReward, locale: Locale): string {
  if (reward.type === "pokemon") return `${locale === "es" ? "Se sumó" : "Joined"} ${reward.species}`;
  if (reward.type === "item") return `${reward.item} ×${reward.quantity}`;
  if (reward.type === "move") return `${locale === "es" ? "Movimiento aprendido" : "Move learned"}: ${reward.move}`;
  if (reward.type === "level") return `${locale === "es" ? "Compañero" : "Partner"} +${reward.levels} LV`;
  if (reward.type === "stat") return `${reward.species} ${effectLabel(reward.stat, locale)} +${reward.amount}`;
  return `${reward.name.split(" · ")[0]} · ${locale === "es" ? "vínculo" : "bond"} ${reward.amount > 0 ? "+" : ""}${reward.amount}`;
}

const OUTCOME_COPY: Record<string, Record<Locale, { headline: string; success: string; failure: string; body: string }>> = {
  capture: pair("La salida dejó un resultado", "La apuesta de captura salió", "La pista no dio lo esperado", "El roster y los recursos ya reflejan lo que pasó fuera del estadio.", "The trip produced a result", "The capture gamble paid off", "The trail did not pay off", "The roster and resources now reflect what happened away from the stadium."),
  health: pair("El parte médico quedó actualizado", "La carga salió mejor de lo previsto", "La carga pasó factura", "El estado de salud de la carrera ya incorpora esta semana de trabajo.", "The medical record is updated", "The workload went better than expected", "The workload took its toll", "Career health now includes the result of this week."),
  rivalry: pair("La respuesta al rival quedó fijada", "La apuesta competitiva funcionó", "El rival ganó este intercambio", "La preparación registrada para la temporada ya refleja la decisión.", "The response to the rival is set", "The competitive gamble worked", "The rival won this exchange", "Recorded season preparation now reflects the decision."),
  training: pair("La semana de entrenamiento terminó", "La sobrecarga rindió", "La sobrecarga no rindió", "El desarrollo y el estado del equipo ya incluyen el trabajo elegido.", "The training week is over", "The overload paid off", "The overload did not pay off", "Team development and condition now include the chosen work."),
  contract: pair("La posición del club cambió", "La apuesta de negociación funcionó", "La apuesta debilitó la posición", "Los recursos y la reputación de carrera ya reflejan la decisión; un contrato real sólo cambia en el mercado de clubes.", "The club position changed", "The negotiation gamble worked", "The gamble weakened the position", "Career resources and reputation now reflect the choice; an actual contract changes only in the club market."),
  contest: pair("La actividad terminó", "La apuesta de exposición funcionó", "La exposición no dio el retorno esperado", "El juego registró únicamente los cambios y recompensas que esta actividad puede aplicar de verdad.", "The activity is over", "The exposure gamble worked", "The exposure did not return what was expected", "The game recorded only the changes and rewards this activity can actually apply."),
  conservation: pair("El club tomó una posición", "La apuesta salió a favor del club", "La apuesta tuvo un coste", "La carrera registra sus efectos actuales. No se inventa un cambio permanente del hábitat sin un sistema de mundo que lo sostenga.", "The club took a position", "The gamble went the club's way", "The gamble carried a cost", "The career records its current effects. No permanent habitat change is invented without a world system to support it."),
  media: pair("La respuesta ya es parte de la temporada", "La exposición funcionó", "La exposición se volvió en contra", "Reputación, recursos y recompensas reflejan la reacción que el sistema puede sostener.", "The response is now part of the season", "The exposure worked", "The exposure turned against you", "Reputation, resources and rewards reflect the reaction the system can support."),
  default: pair("La decisión tuvo consecuencias", "La apuesta funcionó", "La apuesta falló", "El estado de carrera ya refleja los cambios aplicados. Esta elección queda en el registro de la temporada.", "The decision had consequences", "The gamble worked", "The gamble failed", "Career state now reflects the applied changes. This choice remains in the season record."),
};

function pair(esHeadline: string, esSuccess: string, esFailure: string, esBody: string, enHeadline: string, enSuccess: string, enFailure: string, enBody: string) {
  return {
    es: { headline: esHeadline, success: esSuccess, failure: esFailure, body: esBody },
    en: { headline: enHeadline, success: enSuccess, failure: enFailure, body: enBody },
  };
}
