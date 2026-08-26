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

export function normalizedDecisionHistory(value: unknown): DecisionHistoryEntry[] {
  if (!Array.isArray(value)) return [];
  return value.filter((entry): entry is DecisionHistoryEntry => Boolean(entry) && typeof entry === "object" && !Array.isArray(entry));
}

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
      : (locale === "es" ? "La decisión quedó asentada. Por ahora no dejó otro cambio concreto en la temporada." : "The decision is on record. For now it left no other concrete change in the season."),
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
  health: pair("El parte médico quedó actualizado", "La carga salió mejor de lo previsto", "La carga pasó factura", "El parte de esta semana ya está incorporado a tu estado de carrera.", "The medical record is updated", "The workload went better than expected", "The workload took its toll", "This week's report is now part of your career state."),
  rivalry: pair("La respuesta al rival quedó fijada", "La apuesta competitiva funcionó", "El rival ganó este intercambio", "La preparación registrada para la temporada ya refleja la decisión.", "The response to the rival is set", "The competitive gamble worked", "The rival won this exchange", "Recorded season preparation now reflects the decision."),
  training: pair("La semana de entrenamiento terminó", "La sobrecarga rindió", "La sobrecarga no rindió", "El desarrollo y el estado del equipo ya incluyen el trabajo elegido.", "The training week is over", "The overload paid off", "The overload did not pay off", "Team development and condition now include the chosen work."),
  contract: pair("La posición del club cambió", "La apuesta de negociación funcionó", "La apuesta debilitó la posición", "Cambió tu margen dentro del club. El contrato sigue siendo el que figura en la oficina hasta que llegue una renovación o un nuevo mercado.", "The club position changed", "The negotiation gamble worked", "The gamble weakened the position", "Your room inside the club changed. The contract remains the one on file until a renewal or a new market arrives."),
  contest: pair("La actividad terminó", "La apuesta de exposición funcionó", "La exposición no dio el retorno esperado", "La jornada dejó un resultado concreto y ya forma parte de la temporada.", "The activity is over", "The exposure gamble worked", "The exposure did not return what was expected", "The event left a concrete result and is now part of the season."),
  conservation: pair("El club tomó una posición", "La apuesta salió a favor del club", "La apuesta tuvo un coste", "El club ya asumió el efecto inmediato de la decisión. El conflicto con la zona sigue abierto hasta que existan consecuencias observables.", "The club took a position", "The gamble went the club's way", "The gamble carried a cost", "The club has absorbed the immediate effect of the decision. The conflict around the site remains open until observable consequences occur."),
  media: pair("La respuesta ya es parte de la temporada", "La exposición funcionó", "La exposición se volvió en contra", "La reacción ya se refleja en tu reputación, recursos y recompensas registradas.", "The response is now part of the season", "The exposure worked", "The exposure turned against you", "The reaction is now reflected in recorded reputation, resources and rewards."),
  default: pair("La decisión tuvo consecuencias", "La apuesta funcionó", "La apuesta falló", "El estado de la temporada ya refleja lo que cambió. La elección queda asentada en el registro.", "The decision had consequences", "The gamble worked", "The gamble failed", "Season state now reflects what changed. The choice remains on record."),
};

function pair(esHeadline: string, esSuccess: string, esFailure: string, esBody: string, enHeadline: string, enSuccess: string, enFailure: string, enBody: string) {
  return {
    es: { headline: esHeadline, success: esSuccess, failure: esFailure, body: esBody },
    en: { headline: enHeadline, success: enSuccess, failure: enFailure, body: enBody },
  };
}
