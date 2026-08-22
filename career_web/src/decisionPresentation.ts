import type { CareerDecision, CareerRun, DecisionOption, DecisionReward, Locale } from "./types";

type CrossLocaleCopy = {
  title: string;
  body: string;
  options: [string, string, string];
};

const CROSS_LOCALE: Record<string, { es: CrossLocaleCopy; en: CrossLocaleCopy }> = {
  capture: bilingual(
    "Una señal en la ruta", "Un ojeador encontró una oportunidad de captura fuera del plan habitual del club.", ["Seguir las huellas", "Cambiar la zona de búsqueda", "Ir por la pista difícil"],
    "A trail outside the plan", "A scout found a capture opportunity outside the club's usual plan.", ["Follow the tracks", "Change the search zone", "Take the difficult trail"],
  ),
  evolution: bilingual(
    "Tu compañero está cambiando", "El cuerpo técnico debe decidir cómo acompañar el próximo paso de desarrollo.", ["Esperar el momento", "Preparar la evolución", "Acelerar el desarrollo"],
    "Your partner is changing", "The staff must decide how to support the next development step.", ["Wait for the moment", "Prepare the evolution", "Accelerate development"],
  ),
  breeding: bilingual(
    "Una plaza en la guardería", "La guardería regional ofrece una semana de trabajo y sólo hay tiempo para una prioridad.", ["Priorizar el cuidado", "Financiar la guardería", "Aceptar la opción incierta"],
    "A nursery place opens", "The regional nursery offers one working week and there is time for only one priority.", ["Prioritize care", "Fund the nursery", "Take the uncertain option"],
  ),
  contest: bilingual(
    "La invitación del escenario", "Un concurso regional abre una actividad paralela antes del calendario.", ["Observar desde fuera", "Preparar una exhibición", "Buscar el gran premio"],
    "An invitation to perform", "A regional contest opens a parallel activity before the schedule.", ["Watch from outside", "Prepare an exhibition", "Chase the grand prize"],
  ),
  research: bilingual(
    "Una señal contradice el informe", "El laboratorio tiene información incompleta y necesita una decisión sobre cuánto invertir en verificarla.", ["Archivar la pista", "Financiar el análisis", "Publicar la teoría"],
    "A signal contradicts the report", "The lab has incomplete information and needs a decision on how much to invest in verifying it.", ["Archive the lead", "Fund the analysis", "Publish the theory"],
  ),
  health: bilingual(
    "El parte médico cambia la semana", "El cuerpo médico detectó desgaste y necesita una decisión antes de la siguiente carga.", ["Descanso completo", "Recuperación activa", "Competir con carga"],
    "The medical report changes the week", "Medical staff found wear and need a decision before the next workload.", ["Full rest", "Active recovery", "Compete under strain"],
  ),
  economy: bilingual(
    "El club tiene que elegir una prioridad", "Los recursos disponibles no alcanzan para financiar todo al mismo tiempo.", ["Proteger la caja", "Invertir en preparación", "Adelantar recursos"],
    "The club must choose a priority", "Available resources cannot fund every priority at once.", ["Protect the balance", "Invest in preparation", "Pull resources forward"],
  ),
  media: bilingual(
    "Una cámara espera afuera", "La atención pública llegó al club y la respuesta quedará asociada a esta temporada.", ["Cerrar el vestuario", "Dar una entrevista medida", "Responder en directo"],
    "A camera is waiting outside", "Public attention reached the club and the response will be tied to this season.", ["Close the locker room", "Give a measured interview", "Go live"],
  ),
  crime: bilingual(
    "Un contacto fuera del circuito", "Un intermediario ofrece información que la Liga no autorizó.", ["Rechazar y documentar", "Investigar sin comprar", "Aceptar el trato"],
    "A contact outside the circuit", "A broker offers information the League did not authorize.", ["Refuse and document", "Investigate without buying", "Take the deal"],
  ),
  friendship: bilingual(
    "Un contacto pide tiempo", "Una relación de la carrera necesita una respuesta concreta antes de seguir con el calendario.", ["Escuchar primero", "Trabajar juntos", "Exigir una respuesta"],
    "A contact asks for time", "A career relationship needs a concrete response before the schedule continues.", ["Listen first", "Work together", "Demand a response"],
  ),
  rivalry: bilingual(
    "El próximo rival respondió", "El cruce ya empezó fuera del campo y el club debe decidir cuánto involucrarse.", ["Responder en el campo", "Estudiar el cruce", "Aceptar el desafío"],
    "The next rival answered", "The matchup has already started away from the field and the club must decide how far to engage.", ["Answer on the field", "Study the matchup", "Accept the challenge"],
  ),
  conservation: bilingual(
    "Las obras chocan con el entorno", "El proyecto del club genera un conflicto con una zona usada por Pokémon silvestres.", ["Frenar las obras", "Rediseñar el proyecto", "Priorizar el proyecto"],
    "Construction conflicts with the environment", "The club project conflicts with an area used by wild Pokémon.", ["Pause construction", "Redesign the project", "Prioritize the project"],
  ),
  regional_culture: bilingual(
    "La comunidad invita al club", "Una tradición regional abre una oportunidad de participación, pero no todos esperan lo mismo del club.", ["Participar como invitado", "Apoyar la actividad", "Buscar exposición"],
    "The community invites the club", "A regional tradition opens a chance to participate, but not everyone expects the same thing from the club.", ["Join as a guest", "Support the activity", "Seek exposure"],
  ),
  contract: bilingual(
    "La dirección pide una definición", "La situación contractual y los recursos del club obligan a fijar una prioridad para esta temporada.", ["Priorizar estabilidad", "Pedir recursos", "Esperar una mejor posición"],
    "Management wants a decision", "The contract situation and club resources force a priority for this season.", ["Prioritize stability", "Ask for resources", "Wait for a stronger position"],
  ),
  training: bilingual(
    "Sólo queda una semana", "No hay tiempo para mejorar todo antes del calendario.", ["Reducir la carga", "Trabajar una debilidad", "Doblar las sesiones"],
    "Only one week remains", "There is not enough time to improve everything before the schedule.", ["Reduce the load", "Train a weakness", "Double the sessions"],
  ),
};

const GUARDED_DYNAMIC_FAMILIES = new Set([
  "breeding", "contest", "economy", "contract", "media", "crime", "friendship", "rivalry", "conservation", "regional_culture",
]);

export function decisionPresentation(decision: CareerDecision, run: CareerRun, locale: Locale) {
  const storedLocale = run.locale ?? locale;
  const crossLocale = storedLocale !== locale;
  const fallback = CROSS_LOCALE[decision.family]?.[locale];
  const title = crossLocale && fallback ? fallback.title : decision.title;
  const body = crossLocale && fallback
    ? fallback.body
    : GUARDED_DYNAMIC_FAMILIES.has(decision.family)
      ? supportedContextBody(decision, run, locale)
      : decision.body;

  return {
    title: title.replaceAll("{partner}", run.build.starter),
    body: body.replaceAll("{partner}", run.build.starter),
    options: decision.options.map((option, index) => ({
      ...option,
      label: crossLocale && fallback ? fallback.options[index] ?? option.label : option.label,
      description: optionTradeoff(option, locale),
    })),
  };
}

function supportedContextBody(decision: CareerDecision, run: CareerRun, locale: Locale): string {
  const npc = decision.npc_name?.split(" · ")[0] || (locale === "es" ? "el contacto" : "the contact");
  const club = run.contract?.club_name || (locale === "es" ? "tu equipo" : "your team");
  const partner = run.build.starter;

  if (locale === "es") {
    if (decision.family === "breeding") return `${npc} consiguió una plaza de trabajo en la guardería regional para ${club}. ${partner} puede participar de la semana, pero sólo hay tiempo y recursos para una de las tres alternativas que aparecen abajo.`;
    if (decision.family === "contest") return `${npc} acercó una invitación para una actividad pública en la región. ${partner} puede participar, pero la jornada compite por tiempo y recursos con la preparación de ${club}.`;
    if (decision.family === "economy") return `${npc} cerró las cuentas de ${club}. Tenés ${run.finances} puntos de recursos de club y ₽ ${run.money ?? 0} disponibles. Esta decisión define qué coste acepta el equipo esta semana.`;
    if (decision.family === "contract") return `${npc} pide una posición antes del calendario. Tu contrato actual es ${run.contract ? `${run.contract.club_name}, ₽ ${run.contract.salary} por temporada, ${run.contract.seasons_remaining} temporada(s) restante(s)` : "sin contrato activo"}. Esta decisión cambia tu margen de carrera, no reemplaza el mercado de clubes.`;
    if (decision.family === "media") return `${npc} espera una respuesta de ${club}. Tu reputación está en ${run.reputation}. Lo que elijas quedará asociado a esta temporada y los efectos concretos están detallados en cada opción.`;
    if (decision.family === "crime") return `${npc} trae un contacto que la Liga no autorizó. No sabés más que eso. Podés cortar la conversación, dedicar recursos a seguir la pista o asumir el riesgo que figura en la opción.`;
    if (decision.family === "friendship") return `${npc} vuelve a aparecer en una semana cargada. El vínculo registrado más alto de tu carrera es ${Math.max(0, ...Object.values(run.relationships ?? {}))}. Elegís cuánto tiempo y recursos le dedica ${club}; cualquier cambio de vínculo aparece explícitamente en la opción.`;
    if (decision.family === "rivalry") return `${npc} pone el próximo cruce sobre la mesa. ${partner} quedó en el centro de la conversación. Elegís si ${club} conserva recursos, invierte en preparación general o toma la apuesta indicada; no hay ventaja oculta fuera de los efectos mostrados.`;
    if (decision.family === "conservation") return `${npc} informa que un proyecto de ${club} entró en conflicto con una zona usada por Pokémon silvestres. La situación todavía no está resuelta. Esta semana sólo definís qué coste inmediato acepta el club; cualquier consecuencia posterior tendrá que aparecer como un hecho nuevo.`;
    if (decision.family === "regional_culture") return `${npc} invita a ${club} a una actividad de la región con ${partner}. La comunidad ya hizo la invitación; lo que todavía está abierto es cuánto tiempo, recursos y exposición acepta el club.`;
  }

  if (decision.family === "breeding") return `${npc} secured a working place at the regional nursery for ${club}. ${partner} can take part in the week, but there is time and budget for only one of the three options below.`;
  if (decision.family === "contest") return `${npc} brought an invitation to a public regional activity. ${partner} can participate, but the event competes with ${club}'s preparation for time and resources.`;
  if (decision.family === "economy") return `${npc} closed ${club}'s books. The club has ${run.finances} resource points and ₽ ${run.money ?? 0} available. This choice decides which cost the team accepts this week.`;
  if (decision.family === "contract") return `${npc} wants a position before the schedule. Your current contract is ${run.contract ? `${run.contract.club_name}, ₽ ${run.contract.salary} per season, ${run.contract.seasons_remaining} season(s) remaining` : "no active contract"}. This choice changes your career position; it does not replace the club market.`;
  if (decision.family === "media") return `${npc} is waiting for an answer from ${club}. Your reputation is ${run.reputation}. The response will stay with this season, and each option shows the concrete effects it can produce.`;
  if (decision.family === "crime") return `${npc} brings a contact the League did not authorize. That is all you know. End the conversation, spend resources following the lead, or take the listed risk.`;
  if (decision.family === "friendship") return `${npc} returns during a crowded week. Your highest recorded career bond is ${Math.max(0, ...Object.values(run.relationships ?? {}))}. You decide how much time and resources ${club} gives the contact; any bond change is stated explicitly in the option.`;
  if (decision.family === "rivalry") return `${npc} puts the next matchup on the table. ${partner} is at the center of the discussion. Decide whether ${club} preserves resources, invests in general preparation, or takes the listed gamble; there is no hidden competitive edge beyond the shown effects.`;
  if (decision.family === "conservation") return `${npc} reports that a ${club} project conflicts with an area used by wild Pokémon. The situation is not resolved yet. This week you only choose which immediate cost the club accepts; later consequences must arrive as new facts.`;
  if (decision.family === "regional_culture") return `${npc} invites ${club} and ${partner} to a regional activity. The invitation is real; what remains open is how much time, resources and exposure the club accepts.`;
  return decision.body;
}

function optionTradeoff(option: DecisionOption, locale: Locale): string {
  const guaranteed = effectSummary(option.guaranteed, locale);
  const rewards = rewardSummary(option.rewards ?? [], locale);
  const direct = [guaranteed, rewards].filter(Boolean).join(" · ");

  if (option.risk === "gamble") {
    const chance = Math.round(Number(option.gamble?.chance ?? 0.5) * 100);
    const success = [
      effectSummary(option.gamble?.success ?? {}, locale),
      rewardSummary(option.gamble?.success_rewards ?? [], locale),
    ].filter(Boolean).join(" · ") || (locale === "es" ? "sin premio adicional" : "no additional reward");
    const failure = [
      effectSummary(option.gamble?.failure ?? {}, locale),
      rewardSummary(option.gamble?.failure_rewards ?? [], locale),
    ].filter(Boolean).join(" · ") || (locale === "es" ? "sin cambio adicional" : "no additional change");
    const base = direct ? `Base: ${direct}. ` : "";
    return locale === "es"
      ? `${base}${chance}% de éxito: ${success}. Si falla: ${failure}.`
      : `${base}${chance}% success: ${success}. On failure: ${failure}.`;
  }

  if (!direct) return locale === "es" ? "No altera el estado de carrera de forma inmediata." : "No immediate career-state change.";
  return option.risk === "calculated"
    ? (locale === "es" ? `Intercambio conocido: ${direct}.` : `Known trade-off: ${direct}.`)
    : (locale === "es" ? `Consecuencia directa: ${direct}.` : `Direct consequence: ${direct}.`);
}

function effectSummary(effects: Record<string, number>, locale: Locale): string {
  return Object.entries(effects)
    .filter(([, value]) => Number(value) !== 0)
    .map(([key, value]) => `${effectLabel(key, locale)} ${signed(Number(value))}`)
    .join(", ");
}

function rewardSummary(rewards: DecisionReward[], locale: Locale): string {
  return rewards.map((reward) => {
    if (reward.type === "pokemon") return `${locale === "es" ? "Pokémon" : "Pokemon"}: ${reward.species}`;
    if (reward.type === "item") return `${reward.item} ×${reward.quantity}`;
    if (reward.type === "move") return `${locale === "es" ? "movimiento" : "move"}: ${reward.move}`;
    if (reward.type === "level") return `${locale === "es" ? "compañero" : "partner"} +${reward.levels} LV`;
    if (reward.type === "stat") return `${reward.species} ${effectLabel(reward.stat, locale)} +${reward.amount}`;
    return `${reward.name.split(" · ")[0]} ${locale === "es" ? "vínculo" : "bond"} ${signed(reward.amount)}`;
  }).join(", ");
}

function signed(value: number): string {
  return value > 0 ? `+${value}` : String(value);
}

export function effectLabel(key: string, locale: Locale): string {
  const labels: Record<string, [string, string]> = {
    health: ["Salud", "Health"], development: ["Desarrollo", "Development"],
    scouting: ["Scouting", "Scouting"], finances: ["Recursos", "Resources"], reputation: ["Reputación", "Reputation"],
    partner_levels: ["Niveles del compañero", "Partner levels"],
    home_level_bonus: ["Preparación propia", "Home preparation"],
    away_level_bonus: ["Preparación rival", "Opponent preparation"],
    hp: ["PS", "HP"], atk: ["Ataque", "Attack"], def: ["Defensa", "Defense"],
    spatk: ["At. Esp.", "Sp. Atk"], spdef: ["Def. Esp.", "Sp. Def"], spd: ["Velocidad", "Speed"],
  };
  return labels[key]?.[locale === "es" ? 0 : 1] ?? key;
}

export function riskLabel(risk: DecisionOption["risk"], locale: Locale): string {
  const labels = {
    safe: locale === "es" ? "Consecuencia directa" : "Direct outcome",
    calculated: locale === "es" ? "Intercambio conocido" : "Known trade-off",
    gamble: locale === "es" ? "Apuesta" : "Gamble",
  };
  return labels[risk];
}

export function transparencyLabel(value: DecisionOption["transparency"], locale: Locale): string {
  const labels = {
    full: "",
    estimated: locale === "es" ? "Probabilidad estimada" : "Estimated probability",
    hidden: locale === "es" ? "Hay consecuencias no reveladas" : "Some consequences are not revealed",
  };
  return labels[value];
}

export function effectRule(key: string, locale: Locale): string {
  const rules: Record<string, [string, string]> = {
    health: ["A 0 termina la carrera; por debajo de 45 reduce la preparación.", "At 0 the career ends; below 45 it reduces preparation."],
    development: ["Cada 3 puntos añade un nivel de preparación al compañero, hasta +3.", "Every 3 points adds one preparation level to your partner, up to +3."],
    scouting: ["Cada 3 puntos reduce un nivel de preparación rival, hasta −2.", "Every 3 points removes one opponent preparation level, up to −2."],
    finances: ["Cada 4 puntos financia +1 nivel. Cada punto de deuda resta 1, hasta −3; podés sanearla con tu dinero.", "Every 4 points funds +1 level. Each debt point removes 1, up to −3; you can clear it with your money."],
    reputation: ["Mejora salario, contratos y posición dentro del club.", "Improves salary, contracts and standing inside the club."],
  };
  return rules[key]?.[locale === "es" ? 0 : 1] ?? "";
}

function bilingual(
  esTitle: string,
  esBody: string,
  esOptions: [string, string, string],
  enTitle: string,
  enBody: string,
  enOptions: [string, string, string],
) {
  return {
    es: { title: esTitle, body: esBody, options: esOptions },
    en: { title: enTitle, body: enBody, options: enOptions },
  };
}
