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

export interface BattleOutcomePresentation {
  kind: "victory" | "defeat" | "draw";
  title: string;
  commentary: string;
  detail: string;
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
        const hp = finiteNumber(raw.hp);
        const maxHp = finiteNumber(raw.max_hp);
        if (hp !== null) current.hp = Math.max(0, hp);
        if (maxHp !== null) current.max_hp = Math.max(0, maxHp);
        if (Array.isArray(raw.statuses)) current.statuses = raw.statuses.map(String);
        if (typeof raw.active === "boolean") current.active = raw.active;
      }
    }
    if (event.type === "shift") {
      const current = combatants.get(String(event.actor ?? ""));
      const position = finitePosition(event.to);
      if (current && position) current.position = position;
    }
    if (event.type === "forced_movement") {
      const current = combatants.get(String(event.target ?? ""));
      const position = finitePosition(event.to);
      if (current && position) current.position = position;
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
        const position = finitePosition(event.target_position ?? event.position);
        if (position) incoming.position = position;
      }
    }
    const hpOwner = String(event.target ?? event.actor ?? "");
    const hpCombatant = combatants.get(hpOwner);
    const targetHp = finiteNumber(event.target_hp);
    const newHp = finiteNumber(event.new_hp);
    if (hpCombatant && targetHp !== null) hpCombatant.hp = Math.max(0, targetHp);
    if (hpCombatant && newHp !== null) hpCombatant.hp = Math.max(0, newHp);
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
      const hp = finiteNumber(final.hp);
      const maxHp = finiteNumber(final.max_hp);
      const position = finitePosition(final.position);
      if (hp !== null) current.hp = Math.max(0, hp);
      if (maxHp !== null) current.max_hp = Math.max(0, maxHp);
      current.position = position ?? undefined;
      current.statuses = Array.isArray(final.statuses) ? final.statuses.map(String) : [];
      current.active = final.active;
    }
  }

  const event = complete ? null : transcript.events[rawEventIndex] ?? null;
  const context = isRecord(event?.context) ? event.context : {};
  const rollOptions = Array.isArray(context.roll_options) ? context.roll_options.map(String) : [];
  const damage = event?.type === "move"
    ? finiteNumber(event.damage) ?? 0
    : event?.type === "status" && event.outcome === "hit_self"
      ? finiteNumber(event.amount) ?? 0
      : 0;
  const effectiveness = finiteNumber(event?.type_multiplier) ?? 1;
  const targetHp = finiteNumber(event?.target_hp);
  return {
    combatants: [...combatants.values()],
    round: finiteNumber(complete ? transcript.rounds : event?.round) ?? 1,
    event,
    actorId: String(event?.actor ?? ""),
    targetId: String(event?.target ?? (event?.target_hp !== undefined ? event?.actor ?? "" : "")),
    move: String(event?.move ?? event?.ability ?? ""),
    damage,
    hit: typeof event?.hit === "boolean" ? event.hit : null,
    critical: Boolean(event?.crit),
    effectiveness,
    stab: rollOptions.includes("stab"),
    attackValue: finiteNumber(event?.attack_value),
    defenseValue: finiteNumber(event?.defense_value),
    effectiveDb: finiteNumber(event?.effective_db),
    knockout: event?.type === "move" && event?.hit !== false && targetHp === 0,
    complete,
  };
}

export function battleOutcomePresentation(locale: Locale, transcript: BattleTranscript): BattleOutcomePresentation {
  const rounds = Math.max(0, finiteNumber(transcript.rounds) ?? 0);
  const roundsLabel = locale === "es" ? "rondas" : "rounds";
  if (transcript.winner_team === "career-home") {
    const winner = authoritativeWinnerLabel(transcript.winner_label, transcript.spec.home_club);
    return {
      kind: "victory",
      title: locale === "es" ? "VICTORIA" : "VICTORY",
      commentary: locale === "es" ? `${winner} se lleva la victoria en ${rounds} ${roundsLabel}.` : `${winner} wins after ${rounds} ${roundsLabel}.`,
      detail: `${winner} · ${rounds} ${roundsLabel}`,
    };
  }
  if (transcript.winner_team === "career-away") {
    const winner = authoritativeWinnerLabel(transcript.winner_label, transcript.spec.away_club);
    return {
      kind: "defeat",
      title: locale === "es" ? "DERROTA" : "DEFEAT",
      commentary: locale === "es" ? `${winner} se lleva la victoria en ${rounds} ${roundsLabel}.` : `${winner} wins after ${rounds} ${roundsLabel}.`,
      detail: `${winner} · ${rounds} ${roundsLabel}`,
    };
  }
  return {
    kind: "draw",
    title: locale === "es" ? "EMPATE" : "DRAW",
    commentary: locale === "es" ? `El combate termina en empate después de ${rounds} ${roundsLabel}.` : `The battle ends in a draw after ${rounds} ${roundsLabel}.`,
    detail: `${transcript.spec.home_club} vs ${transcript.spec.away_club} · ${rounds} ${roundsLabel}`,
  };
}

export function battleCommentary(locale: Locale, transcript: BattleTranscript, view: BattleViewState): string {
  if (view.complete) return battleOutcomePresentation(locale, transcript).commentary;
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
    const damage = view.damage;
    const critical = event.crit ? (locale === "es" ? " ¡Golpe crítico!" : " Critical hit!") : "";
    const effectiveness = view.effectiveness;
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
    const amount = finiteNumber(event.amount) ?? 0;
    return locale === "es"
      ? `${String(event.move ?? actor)} cambia el ${stat} de ${target} ${Math.abs(amount)} niveles.`
      : `${String(event.move ?? actor)} changes ${target}'s ${stat} by ${amount} stages.`;
  }
  if (type === "status") {
    if (event.outcome === "hit_self") {
      const amount = finiteNumber(event.amount) ?? 0;
      return locale === "es"
        ? `${actor} se hiere por la confusión y pierde ${amount} PS.`
        : `${actor} hurts itself in confusion and loses ${amount} HP.`;
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

function authoritativeWinnerLabel(value: unknown, fallback: string): string {
  if (typeof value !== "string") return fallback;
  const label = value.trim();
  return label || fallback;
}

function combatantName(transcript: BattleTranscript, id: string): string {
  return transcript.initial_state.combatants.find((entry) => entry.id === id)?.species ?? id.replace(/^career-(home|away)-?/, "");
}

function cloneCombatant(entry: BattleCombatant): BattleCombatant {
  return {
    ...entry,
    position: finitePosition(entry.position) ?? undefined,
    hp: finiteNumber(entry.hp) ?? 0,
    max_hp: finiteNumber(entry.max_hp) ?? 0,
    statuses: Array.isArray(entry.statuses) ? entry.statuses.map(String) : [],
    stats: { ...(entry.stats ?? {}) },
    effective_stats: { ...(entry.effective_stats ?? {}) },
    abilities: Array.isArray(entry.abilities) ? entry.abilities.map(String) : [],
    moves: Array.isArray(entry.moves)
      ? entry.moves.filter(isRecord).map((move) => ({ ...move })) as BattleCombatant["moves"]
      : [],
  };
}

function finiteNumber(value: unknown): number | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return value;
}

function finitePosition(value: unknown): [number, number] | null {
  if (!Array.isArray(value) || value.length < 2) return null;
  const x = Number(value[0]);
  const y = Number(value[1]);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
  return [x, y];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
