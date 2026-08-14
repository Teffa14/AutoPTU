import type { BattleCombatant, BattleTranscript, Locale } from "./types";

export interface BattleViewState {
  combatants: BattleCombatant[];
  round: number;
  event: Record<string, unknown> | null;
  actorId: string;
  targetId: string;
  move: string;
  damage: number;
  hit: boolean | null;
  critical: boolean;
  effectiveness: number;
  stab: boolean;
  attackValue: number | null;
  defenseValue: number | null;
  effectiveDb: number | null;
  knockout: boolean;
  complete: boolean;
}

const PRESENTED_EVENT_TYPES = new Set([
  "round_start", "shift", "forced_movement", "maneuver", "move", "status", "ability", "combat_stage", "switch",
]);

export function playbackEventIndexes(transcript: BattleTranscript): number[] {
  return transcript.events.flatMap((event, index) => PRESENTED_EVENT_TYPES.has(String(event.type ?? "")) ? [index] : []);
}

export function deriveBattleView(transcript: BattleTranscript, rawEventIndex: number): BattleViewState {
  const complete = rawEventIndex >= transcript.events.length;
  const combatants = new Map(
    transcript.initial_state.combatants.map((entry) => [entry.id, cloneCombatant(entry)]),
  );
  const lastIndex = complete ? transcript.events.length - 1 : rawEventIndex;

  for (let index = 0; index <= lastIndex; index += 1) {
    const event = transcript.events[index];
    if (!event) continue;
    if (event.type === "round_start" && Array.isArray(event.initial_states)) {
      for (const raw of event.initial_states) {
        if (!isRecord(raw)) continue;
        const id = String(raw.actor ?? "");
        const current = combatants.get(id);
        if (!current) continue;
        if (typeof raw.hp === "number") current.hp = raw.hp;
        if (typeof raw.max_hp === "number") current.max_hp = raw.max_hp;
        if (Array.isArray(raw.statuses)) current.statuses = raw.statuses.map(String);
        if (typeof raw.active === "boolean") current.active = raw.active;
      }
    }
    if (event.type === "shift" && Array.isArray(event.to)) {
      const current = combatants.get(String(event.actor ?? ""));
      if (current && event.to.length >= 2) current.position = [Number(event.to[0]), Number(event.to[1])];
    }
    if (event.type === "forced_movement" && Array.isArray(event.to)) {
      const current = combatants.get(String(event.target ?? ""));
      if (current && event.to.length >= 2) current.position = [Number(event.to[0]), Number(event.to[1])];
    }
    if (event.type === "switch") {
      const outgoing = combatants.get(String(event.outgoing ?? ""));
      const incoming = combatants.get(String(event.target ?? ""));
      if (outgoing) {
        outgoing.active = false;
        outgoing.position = undefined;
      }
      if (incoming) {
        incoming.active = true;
        const position = event.target_position ?? event.position;
        if (Array.isArray(position) && position.length >= 2) incoming.position = [Number(position[0]), Number(position[1])];
      }
    }
    const hpOwner = String(event.target ?? event.actor ?? "");
    const hpCombatant = combatants.get(hpOwner);
    if (hpCombatant && typeof event.target_hp === "number") hpCombatant.hp = Math.max(0, event.target_hp);
    if (hpCombatant && typeof event.new_hp === "number") hpCombatant.hp = Math.max(0, event.new_hp);
    if (event.status) {
      const statusOwner = combatants.get(String(event.target ?? event.actor ?? ""));
      if (statusOwner) {
        const status = String(event.status);
        const statuses = new Set(statusOwner.statuses ?? []);
        if (event.type === "status_removed" || event.effect === "cure") statuses.delete(status);
        else statuses.add(status);
        statusOwner.statuses = [...statuses];
      }
    }
  }

  if (complete) {
    for (const final of transcript.final_state.combatants) {
      const current = combatants.get(final.id);
      if (!current) continue;
      current.hp = final.hp;
      current.max_hp = final.max_hp;
      current.position = final.position;
      current.statuses = [...(final.statuses ?? [])];
      current.active = final.active;
    }
  }

  const event = complete ? null : transcript.events[rawEventIndex] ?? null;
  const context = isRecord(event?.context) ? event.context : {};
  const rollOptions = Array.isArray(context.roll_options) ? context.roll_options.map(String) : [];
  return {
    combatants: [...combatants.values()],
    round: complete ? transcript.rounds : Number(event?.round ?? 1),
    event,
    actorId: String(event?.actor ?? ""),
    targetId: String(event?.target ?? (event?.target_hp !== undefined ? event?.actor ?? "" : "")),
    move: String(event?.move ?? event?.ability ?? ""),
    damage: event?.type === "move"
      ? Number(event.damage ?? 0)
      : event?.type === "status" && event.outcome === "hit_self"
        ? Number(event.amount ?? 0)
        : 0,
    hit: typeof event?.hit === "boolean" ? event.hit : null,
    critical: Boolean(event?.crit),
    effectiveness: Number(event?.type_multiplier ?? 1),
    stab: rollOptions.includes("stab"),
    attackValue: typeof event?.attack_value === "number" ? event.attack_value : null,
    defenseValue: typeof event?.defense_value === "number" ? event.defense_value : null,
    effectiveDb: typeof event?.effective_db === "number" ? event.effective_db : null,
    knockout: event?.type === "move" && event?.hit !== false && Number(event?.target_hp ?? -1) === 0,
    complete,
  };
}

export function battleCommentary(locale: Locale, transcript: BattleTranscript, view: BattleViewState): string {
  if (view.complete) {
    return locale === "es"
      ? `${transcript.winner_label ?? "El combate"} se lleva la victoria en ${transcript.rounds} rondas.`
      : `${transcript.winner_label ?? "The match"} wins after ${transcript.rounds} rounds.`;
  }
  const event = view.event ?? {};
  const type = String(event.type ?? "");
  const actor = combatantName(transcript, String(event.actor ?? ""));
  const target = combatantName(transcript, String(event.target ?? event.actor ?? ""));
  if (type === "round_start") {
    return locale === "es" ? `Comienza la ronda ${view.round}. Los dos equipos buscan la iniciativa.` : `Round ${view.round} begins. Both teams fight for position.`;
  }
  if (type === "switch") {
    const incoming = combatantName(transcript, String(event.target ?? ""));
    return locale === "es" ? `${incoming} entra a la cancha.` : `${incoming} enters the field.`;
  }
  if (type === "shift") {
    return locale === "es" ? `${actor} toma una nueva posición en la cancha.` : `${actor} takes a new position on the field.`;
  }
  if (type === "forced_movement" || type === "maneuver") {
    return locale === "es"
      ? `${actor} rompe la posición de ${target} con una maniobra táctica.`
      : `${actor} breaks ${target}'s position with a tactical maneuver.`;
  }
  if (type === "move") {
    const move = String(event.move ?? (locale === "es" ? "un movimiento" : "a move"));
    if (event.hit === false) return locale === "es" ? `${actor} usa ${move}, pero falla.` : `${actor} uses ${move}, but misses.`;
    const damage = Number(event.damage ?? 0);
    const critical = event.crit ? (locale === "es" ? " ¡Golpe crítico!" : " Critical hit!") : "";
    const effectiveness = Number(event.type_multiplier ?? 1);
    const effect = effectiveness > 1
      ? (locale === "es" ? " Es muy eficaz." : " It's super effective.")
      : effectiveness > 0 && effectiveness < 1
        ? (locale === "es" ? " No es muy eficaz." : " It's not very effective.")
        : "";
    return locale === "es"
      ? `${actor} usa ${move}.${critical}${damage > 0 ? ` ${target} pierde ${damage} PS.` : ""}${effect}`
      : `${actor} uses ${move}.${critical}${damage > 0 ? ` ${target} loses ${damage} HP.` : ""}${effect}`;
  }
  if (type === "ability") {
    const ability = String(event.ability ?? event.effect ?? "");
    const status = event.status ? ` ${target} ${locale === "es" ? "queda" : "is"} ${statusLabel(String(event.status), locale)}.` : "";
    return locale === "es" ? `Se activa ${ability} de ${actor}.${status}` : `${actor}'s ${ability} activates.${status}`;
  }
  if (type === "combat_stage") {
    const stat = statLabel(String(event.stat ?? ""), locale);
    const amount = Number(event.amount ?? 0);
    return locale === "es"
      ? `${String(event.move ?? actor)} cambia el ${stat} de ${target} ${Math.abs(amount)} niveles.`
      : `${String(event.move ?? actor)} changes ${target}'s ${stat} by ${amount} stages.`;
  }
  if (type === "status") {
    if (event.outcome === "hit_self") {
      return locale === "es"
        ? `${actor} se hiere por la confusión y pierde ${Number(event.amount ?? 0)} PS.`
        : `${actor} hurts itself in confusion and loses ${Number(event.amount ?? 0)} HP.`;
    }
    if (event.status) return locale === "es" ? `${target} queda ${statusLabel(String(event.status), locale)}.` : `${target} is ${statusLabel(String(event.status), locale)}.`;
  }
  return locale === "es" ? "La posición del combate cambia." : "The shape of the match changes.";
}

export function eventTitle(locale: Locale, view: BattleViewState): string {
  if (view.complete) return locale === "es" ? "FINAL DEL COMBATE" : "FULL TIME";
  const event = view.event ?? {};
  if (event.type === "round_start") return `${locale === "es" ? "RONDA" : "ROUND"} ${view.round}`;
  if (event.type === "move") return String(event.move ?? (locale === "es" ? "ATAQUE" : "ATTACK")).toUpperCase();
  if (event.type === "shift") return locale === "es" ? "REPOSICIONAMIENTO" : "REPOSITION";
  if (event.type === "forced_movement" || event.type === "maneuver") return locale === "es" ? "MANIOBRA TÁCTICA" : "TACTICAL MANEUVER";
  if (event.type === "ability") return String(event.ability ?? (locale === "es" ? "HABILIDAD" : "ABILITY")).toUpperCase();
  if (event.type === "combat_stage") return locale === "es" ? "CAMBIO DE STATS" : "STAT CHANGE";
  if (event.type === "switch") return locale === "es" ? "CAMBIO DE POKÉMON" : "POKÉMON SWITCH";
  return event.status ? statusLabel(String(event.status), locale).toUpperCase() : (locale === "es" ? "ESTADO" : "STATUS");
}

export function statLabel(value: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = {
    hp: ["PS", "HP"], atk: ["Ataque", "Attack"], def: ["Defensa", "Defense"],
    spatk: ["At. Esp.", "Sp. Atk"], spdef: ["Def. Esp.", "Sp. Def"], spd: ["Velocidad", "Speed"],
  };
  return labels[value.toLowerCase()]?.[locale === "es" ? 0 : 1] ?? value;
}

export function statusLabel(value: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = {
    paralyzed: ["paralizado", "paralyzed"], confused: ["confundido", "confused"],
    burned: ["quemado", "burned"], poisoned: ["envenenado", "poisoned"],
    asleep: ["dormido", "asleep"], frozen: ["congelado", "frozen"], fainted: ["debilitado", "fainted"],
  };
  return labels[value.toLowerCase()]?.[locale === "es" ? 0 : 1] ?? value;
}

function combatantName(transcript: BattleTranscript, id: string): string {
  return transcript.initial_state.combatants.find((entry) => entry.id === id)?.species ?? id.replace(/^career-(home|away)-?/, "");
}

function cloneCombatant(entry: BattleCombatant): BattleCombatant {
  return {
    ...entry,
    position: entry.position ? [...entry.position] as [number, number] : undefined,
    statuses: [...(entry.statuses ?? [])],
    stats: { ...(entry.stats ?? {}) },
    effective_stats: { ...(entry.effective_stats ?? {}) },
    abilities: [...(entry.abilities ?? [])],
    moves: (entry.moves ?? []).map((move) => ({ ...move })),
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
