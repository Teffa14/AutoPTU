import type { BattleTranscript } from "./types";

export type OpponentKnowledge = {
  seenCombatantIds: ReadonlySet<string>;
  revealedMoves: ReadonlyMap<string, ReadonlySet<string>>;
  revealedAbilities: ReadonlyMap<string, ReadonlySet<string>>;
};

export function opponentKnowledgeAtEvent(transcript: BattleTranscript, rawEventIndex: number): OpponentKnowledge {
  const initialCombatants = Array.isArray(transcript.initial_state?.combatants)
    ? transcript.initial_state.combatants
    : [];
  const events = Array.isArray(transcript.events) ? transcript.events : [];
  const opponentIds = new Set<string>();
  const seenCombatantIds = new Set<string>();
  const revealedMoves = new Map<string, Set<string>>();
  const revealedAbilities = new Map<string, Set<string>>();

  for (const combatant of initialCombatants) {
    if (!isRecord(combatant) || combatant.team !== "career-away") continue;
    const id = safeString(combatant.id);
    if (!id) continue;
    opponentIds.add(id);
    if (combatant.active !== false) seenCombatantIds.add(id);
  }

  const safeIndex = Number.isFinite(rawEventIndex) ? Math.floor(rawEventIndex) : -1;
  const lastIndex = Math.min(Math.max(-1, safeIndex), events.length - 1);
  for (let index = 0; index <= lastIndex; index += 1) {
    const event = events[index];
    if (!isRecord(event)) continue;
    const actor = safeString(event.actor);
    const target = safeString(event.target);

    if (event.type === "switch") {
      if (target && opponentIds.has(target)) seenCombatantIds.add(target);
      continue;
    }

    if (event.type === "move" && actor && opponentIds.has(actor)) {
      seenCombatantIds.add(actor);
      addReveal(revealedMoves, actor, safeString(event.move));
      continue;
    }

    if (event.type === "ability" && actor && opponentIds.has(actor)) {
      seenCombatantIds.add(actor);
      addReveal(revealedAbilities, actor, safeString(event.ability));
    }
  }

  return { seenCombatantIds, revealedMoves, revealedAbilities };
}

export function opponentMoveIsRevealed(knowledge: OpponentKnowledge, combatantId: string, moveName: string): boolean {
  return knowledge.revealedMoves.get(combatantId)?.has(moveName) === true;
}

export function opponentAbilityIsRevealed(knowledge: OpponentKnowledge, combatantId: string, abilityName: string): boolean {
  return knowledge.revealedAbilities.get(combatantId)?.has(abilityName) === true;
}

function addReveal(target: Map<string, Set<string>>, combatantId: string, value: string | null) {
  if (!value) return;
  const current = target.get(combatantId) ?? new Set<string>();
  current.add(value);
  target.set(combatantId, current);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function safeString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}
