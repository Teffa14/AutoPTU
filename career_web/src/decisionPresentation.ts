import type { CareerDecision, CareerRun, DecisionOption, Locale } from "./types";

type ScenarioCopy = {
  title: string;
  body: string;
  options: [[string, string], [string, string], [string, string]];
};

const SCENARIOS: Record<string, { es: ScenarioCopy; en: ScenarioCopy }> = {
  capture: pair("Una señal en la ruta", "El ojeador encontró un Pokémon fuera del radar del club. Perseguir la pista puede ampliar el roster, pero quitará recursos al calendario.", [
    ["Intentar la captura", "Usa una Poké Ball y suma al primer candidato al equipo."], ["Cambiar de ruta", "Invierte en scouting para buscar otro Pokémon regional."], ["Ir por la pista difícil", "Busca una captura distinta y consigue apoyo adicional para futuras expediciones."],
  ], "A trail outside the club", "A scout found a Pokémon the club overlooked. Following it could expand the roster, but it will take resources from the schedule.", [
    ["Attempt the catch", "Use a Poké Ball and add the first candidate to your team."], ["Change the route", "Invest in scouting to find another regional Pokémon."], ["Take the difficult trail", "Pursue a different catch and secure support for future expeditions."],
  ]),
  evolution: pair("Tu compañero está cambiando", "El cuerpo técnico detectó señales de evolución. Debes decidir cuánto exigirle antes de que empiece el calendario.", [
    ["Esperar y protegerlo", "Prioriza su salud y deja que el proceso llegue a su ritmo."], ["Preparar la evolución", "Dedica instalaciones y entrenamiento a una transición controlada."], ["Forzar el momento", "Acelera el desarrollo, con riesgo real para la salud y la reputación."],
  ], "Your partner is changing", "The staff detected signs of evolution. Decide how much to demand before the schedule begins.", [
    ["Wait and protect them", "Prioritize health and let the process happen naturally."], ["Prepare the evolution", "Use facilities and training for a controlled transition."], ["Force the moment", "Accelerate development with a real health and reputation risk."],
  ]),
  breeding: pair("Una plaza en la guardería", "La guardería regional ofrece una única plaza al club. Puede producir talento futuro, pero exige tiempo, dinero y cuidado.", [
    ["Rechazar con respeto", "Conserva los recursos y mantén abierta la relación."], ["Financiar el cuidado", "Invierte en seguimiento profesional y conocimiento del linaje."], ["Aceptar sin garantías", "Asume todos los costes buscando un resultado excepcional."],
  ], "A nursery place opens", "The regional nursery offers the club one place. It may produce future talent, but demands time, money and care.", [
    ["Decline respectfully", "Keep resources while preserving the relationship."], ["Fund professional care", "Invest in expert monitoring and lineage research."], ["Accept without guarantees", "Carry every cost in pursuit of an exceptional result."],
  ]),
  contest: pair("La invitación del escenario", "Un concurso regional ofrece exposición y una forma distinta de entrenar. Participar puede mejorar al equipo, pero distraerlo de la liga.", [
    ["Observar desde fuera", "Aprende del evento sin alterar el plan de entrenamiento."], ["Preparar una exhibición", "Equilibra liga y concurso con una inversión moderada."], ["Buscar el gran premio", "Convierte el concurso en prioridad y acepta el coste de fallar."],
  ], "An invitation to perform", "A regional contest offers exposure and a different kind of training. Entering can develop the team but distract from league work.", [
    ["Watch from outside", "Learn from the event without changing the training plan."], ["Prepare an exhibition", "Balance league and contest with a moderate investment."], ["Chase the grand prize", "Make the contest a priority and accept the cost of failure."],
  ]),
  research: pair("Datos que nadie más tiene", "El laboratorio regional comparte resultados incompletos sobre los próximos rivales. Validarlos mejoraría el scouting, aunque cuesta recursos.", [
    ["Archivar la información", "Conserva una pequeña ventaja sin comprometer el presupuesto."], ["Financiar el análisis", "Convierte los datos en preparación competitiva verificable."], ["Publicar una teoría", "Arriesga credibilidad buscando un descubrimiento importante."],
  ], "Data no one else has", "The regional lab shares incomplete findings about future opponents. Validating them improves scouting but costs resources.", [
    ["Archive the lead", "Keep a small advantage without committing the budget."], ["Fund the analysis", "Turn the data into verified competitive preparation."], ["Publish a theory", "Risk credibility in pursuit of a major discovery."],
  ]),
  health: pair("El informe médico", "El desgaste ya aparece en las pruebas. El equipo médico pide una decisión antes de autorizar la siguiente carga de trabajo.", [
    ["Descanso completo", "Recupera salud y reduce el riesgo antes de competir."], ["Recuperación activa", "Combina tratamiento con una carga de entrenamiento limitada."], ["Competir lesionado", "Mantén el desarrollo a costa de una posible recaída seria."],
  ], "The medical report", "Wear is showing in the tests. Medical staff need a decision before approving the next workload.", [
    ["Full rest", "Recover health and reduce risk before competing."], ["Active recovery", "Combine treatment with a limited training load."], ["Compete hurt", "Protect development at the risk of a serious setback."],
  ]),
  economy: pair("El presupuesto no alcanza", "El club sólo puede financiar una prioridad. La elección afectará instalaciones, preparación y margen para futuros contratos.", [
    ["Proteger la caja", "Reduce el gasto y evita una crisis durante la temporada."], ["Mejorar instalaciones", "Invierte ahora para elevar la preparación del equipo."], ["Adelantar ingresos", "Busca liquidez inmediata con consecuencias si el resultado no llega."],
  ], "The budget falls short", "The club can fund only one priority. The choice affects facilities, preparation and future contract room.", [
    ["Protect the balance", "Reduce spending and avoid a crisis during the season."], ["Upgrade facilities", "Invest now to improve team preparation."], ["Borrow against results", "Find immediate cash with consequences if results fail."],
  ]),
  media: pair("Todos quieren una respuesta", "Una historia sobre el club domina los medios. Tu respuesta cambiará la reputación del proyecto y la presión sobre el equipo.", [
    ["Cerrar el vestuario", "Protege al equipo y limita el alcance de la historia."], ["Dar una entrevista medida", "Acepta exposición a cambio de controlar el mensaje."], ["Responder en directo", "Busca un gran impulso de reputación sin red de seguridad."],
  ], "Everyone wants an answer", "A story about the club dominates the media. Your response changes the project's reputation and pressure on the team.", [
    ["Close the locker room", "Protect the team and limit the story's reach."], ["Give a measured interview", "Accept exposure while controlling the message."], ["Go live", "Chase a major reputation boost without a safety net."],
  ]),
  crime: pair("Una oferta fuera del reglamento", "Un intermediario propone información obtenida de forma ilegal. Puede dar ventaja, pero pone en riesgo la licencia y al club.", [
    ["Rechazar y documentar", "Protege la licencia y conserva pruebas del contacto."], ["Investigar sin comprar", "Usa recursos para conocer el origen sin cruzar la línea."], ["Aceptar el trato", "Obtén una posible ventaja con consecuencias graves si se descubre."],
  ], "An offer outside the rules", "A broker offers illegally obtained information. It may give an edge, but puts the license and club at risk.", [
    ["Refuse and document", "Protect the license and keep evidence of the approach."], ["Investigate without buying", "Spend resources to trace the source without crossing the line."], ["Take the deal", "Seek an advantage with serious consequences if discovered."],
  ]),
  friendship: pair("El equipo ha perdido confianza", "Tu compañero nota la tensión del vestuario. La forma de responder afectará salud, vínculos y rendimiento futuro.", [
    ["Escuchar primero", "Reduce presión y reconstruye confianza sin exigir resultados."], ["Organizar trabajo conjunto", "Invierte tiempo de entrenamiento en fortalecer el vínculo."], ["Exigir una reacción", "Busca una respuesta inmediata arriesgando la relación."],
  ], "The team has lost trust", "Your partner feels the locker-room tension. Your response affects health, relationships and future performance.", [
    ["Listen first", "Lower pressure and rebuild trust without demanding results."], ["Train together", "Invest training time in strengthening the bond."], ["Demand a response", "Seek an immediate reaction while risking the relationship."],
  ]),
  rivalry: pair("Tu rival hizo público el desafío", "El próximo rival convirtió el cruce en algo personal. Puedes ignorarlo, preparar una respuesta o elevar la apuesta.", [
    ["Hablar en el campo", "Evita ruido y protege la preparación del equipo."], ["Estudiar cada detalle", "Dedica recursos a una respuesta táctica calculada."], ["Aceptar el desafío", "Arriesga reputación para obtener una ventaja psicológica."],
  ], "Your rival makes it personal", "The next rival turned the fixture into a personal challenge. Ignore it, prepare an answer or raise the stakes.", [
    ["Answer on the field", "Avoid noise and protect team preparation."], ["Study every detail", "Spend resources on a calculated tactical response."], ["Accept the challenge", "Risk reputation for a psychological advantage."],
  ]),
  conservation: pair("El estadio invade un hábitat", "Las obras del club afectan una zona protegida. Resolverlo exige equilibrar calendario, Pokémon salvajes y recursos.", [
    ["Detener las obras", "Protege el hábitat y asume una demora controlada."], ["Rediseñar el proyecto", "Invierte para conservar la zona sin abandonar las instalaciones."], ["Seguir adelante", "Prioriza la ventaja deportiva con riesgo social y ambiental."],
  ], "The stadium reaches a habitat", "Club construction affects protected land. Solving it means balancing the schedule, wild Pokémon and resources.", [
    ["Stop construction", "Protect the habitat and accept a controlled delay."], ["Redesign the project", "Invest to preserve the site without abandoning facilities."], ["Push ahead", "Prioritize the sporting edge with social and environmental risk."],
  ]),
  regional_culture: pair("La tradición de la región", "La comunidad invita al club a participar en una costumbre local. Respetarla puede abrir vínculos que la liga no ofrece.", [
    ["Participar como invitado", "Aprende la tradición sin convertirla en una campaña."], ["Integrarla al club", "Invierte recursos y crea una relación duradera con la comunidad."], ["Convertirla en espectáculo", "Busca impacto inmediato arriesgando rechazo cultural."],
  ], "A regional tradition", "The community invites the club into a local tradition. Respecting it can open relationships the league cannot offer.", [
    ["Join as a guest", "Learn the tradition without turning it into a campaign."], ["Bring it into the club", "Invest resources and build a lasting community relationship."], ["Turn it into a show", "Seek immediate impact while risking cultural backlash."],
  ]),
  contract: pair("Hay un contrato sobre la mesa", "El club quiere renovar antes de conocer el resultado final. Cada cláusula cambia estabilidad, salario y margen deportivo.", [
    ["Aceptar estabilidad", "Asegura continuidad con condiciones conservadoras."], ["Negociar recursos", "Cambia salario inmediato por mejores herramientas deportivas."], ["Esperar otra oferta", "Arriesga quedarte sin contrato buscando un salto mayor."],
  ], "A contract is on the table", "The club wants a renewal before final results. Each clause changes stability, salary and sporting room.", [
    ["Take stability", "Secure continuity on conservative terms."], ["Negotiate resources", "Trade immediate salary for better sporting tools."], ["Wait for another offer", "Risk being left without a contract while chasing a bigger move."],
  ]),
  training: pair("Sólo queda una semana", "No hay tiempo para mejorar todo. La prioridad elegida definirá la preparación del equipo durante el calendario.", [
    ["Reducir la carga", "Protege salud y consolida lo que el equipo ya domina."], ["Trabajar una debilidad", "Invierte recursos en una mejora medible y controlada."], ["Doblar las sesiones", "Busca desarrollo rápido con riesgo de fatiga y lesión."],
  ], "Only one week remains", "There is no time to improve everything. The chosen priority defines the team's preparation for the schedule.", [
    ["Reduce the load", "Protect health and consolidate what the team already knows."], ["Train a weakness", "Invest resources in a measurable, controlled improvement."], ["Double the sessions", "Chase rapid development with fatigue and injury risk."],
  ]),
};

export function decisionPresentation(decision: CareerDecision, run: CareerRun, locale: Locale) {
  return {
    title: decision.title.replaceAll("{partner}", run.build.starter),
    body: decision.body.replaceAll("{partner}", run.build.starter),
    options: decision.options,
  };
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
    safe: locale === "es" ? "Resultado seguro" : "Safe outcome",
    calculated: locale === "es" ? "Coste conocido" : "Known cost",
    gamble: locale === "es" ? "Apuesta" : "Gamble",
  };
  return labels[risk];
}

export function transparencyLabel(value: DecisionOption["transparency"], locale: Locale): string {
  const labels = {
    full: locale === "es" ? "Información completa" : "Full information",
    estimated: locale === "es" ? "Probabilidad estimada" : "Estimated probability",
    hidden: locale === "es" ? "Hay consecuencias ocultas" : "Some consequences are hidden",
  };
  return labels[value];
}

export function effectRule(key: string, locale: Locale): string {
  const rules: Record<string, [string, string]> = {
    health: ["A 0 termina la carrera; por debajo de 45 reduce la preparación.", "At 0 the career ends; below 45 it reduces preparation."],
    development: ["Cada 3 puntos añade un nivel de preparación al compañero, hasta +3.", "Every 3 points adds one preparation level to your partner, up to +3."],
    scouting: ["Cada 3 puntos reduce un nivel de preparación rival, hasta −2.", "Every 3 points removes one opponent preparation level, up to −2."],
    finances: ["Cada 4 puntos financia +1 nivel; una deuda de −4 aplica −1.", "Every 4 points funds +1 level; −4 debt applies −1."],
    reputation: ["Mejora salario, contratos y posición dentro del club.", "Improves salary, contracts and standing inside the club."],
  };
  return rules[key]?.[locale === "es" ? 0 : 1] ?? "";
}

function pair(esTitle: string, esBody: string, esOptions: ScenarioCopy["options"], enTitle: string, enBody: string, enOptions: ScenarioCopy["options"]) {
  return { es: { title: esTitle, body: esBody, options: esOptions }, en: { title: enTitle, body: enBody, options: enOptions } };
}
