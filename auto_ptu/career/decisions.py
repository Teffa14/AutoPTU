from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List

from .catalogs import EVENT_DOMAINS, FRANCHISE_TRAINERS, NPC_ARCHETYPES, REGIONS, RISK_TIERS, TRANSPARENCY_TIERS
from .class_adapters import selected_class_effects
from .content_compiler import AUTHORIAL_VARIANTS
from .evolutions import next_evolution
from .models import CareerDecision, CareerDecisionOption, CareerRun
from .relationships import refresh_relationship_effects
from .ptu_builds import choose_legal_taught_move
from .roster import capture_species, grant_partner_levels, teach_partner_move


_COPY = {
    "en": {
        "capture": ("A lead beyond the training ground", "A scout found tracks from a Pokémon the club overlooked."),
        "health": ("The season is leaving marks", "Medical staff ask how much recovery the next result is worth."),
        "contract": ("An offer with sharp edges", "Another club made contact before the table settles."),
        "training": ("One week, one priority", "There is time to change only one part of the squad."),
        "default": ("The world moves around the league", "A choice away from the arena will shape the next season."),
    },
    "es": {
        "capture": ("Una pista fuera del campo", "Un ojeador encontró rastros de un Pokémon que el club había pasado por alto."),
        "health": ("La temporada está dejando marcas", "El cuerpo médico pregunta cuánto descanso merece el próximo resultado."),
        "contract": ("Una oferta con aristas", "Otro club contactó antes de que cierre la clasificación."),
        "training": ("Una semana, una prioridad", "Sólo hay tiempo para cambiar una parte del equipo."),
        "default": ("El mundo se mueve alrededor de la liga", "Una decisión fuera de la arena cambiará la próxima temporada."),
    },
}

_VARIANT_HOOKS = {
    "first_contact": ("Es la primera vez que llama directamente al vestuario.", "It is the first direct call to the locker room."),
    "scarcity": ("Sólo hay una plaza y tres clubes ya preguntaron por ella.", "There is one place and three clubs have already asked for it."),
    "public_pressure": ("La decisión será pública antes del calendario.", "The decision will be public before the schedule."),
    "old_debt": ("El club todavía debe un favor de la temporada anterior.", "The club still owes a favor from last season."),
    "local_custom": ("La costumbre local no permite aplazar la respuesta.", "Local custom does not allow a delayed answer."),
    "unexpected_ally": ("Una antigua rival ofrece ayudar, pero quiere respuesta hoy.", "A former rival offers help, but wants an answer today."),
    "institutional_offer": ("La Liga respalda la propuesta y registrará lo elegido.", "The League backs the proposal and will record the choice."),
    "rival_claim": ("El próximo rival afirma que la oportunidad le pertenecía.", "The next rival claims the opportunity belonged to them."),
    "ethical_boundary": ("Aceptar obliga a fijar un límite que el club no podrá negar después.", "Accepting sets a boundary the club cannot deny later."),
    "lost_record": ("Un registro incompleto contradice la versión oficial.", "An incomplete record contradicts the official account."),
    "weather_window": ("La oportunidad desaparecerá cuando cambie el clima regional.", "The opportunity vanishes when the regional weather changes."),
    "family_request": ("La familia de un joven entrenador pidió que vos decidas.", "A young trainer's family asked you to decide."),
    "league_reform": ("Una nueva norma convierte este caso en precedente.", "A new rule turns this case into a precedent."),
    "hidden_cost": ("El coste completo apareció en la letra pequeña.", "The full cost appeared in the fine print."),
    "second_chance": ("Alguien que falló una vez vuelve con otra propuesta.", "Someone who failed once returns with another proposal."),
    "legacy_choice": ("La elección quedará asociada a tu nombre en el archivo regional.", "The regional archive will attach this choice to your name."),
}

_OPTION_LABELS = {
    "capture": ("Seguir las huellas", "Cambiar la zona de búsqueda", "Entrar al hábitat cerrado"),
    "evolution": ("Esperar el momento", "Preparar la evolución", "Forzar el salto"),
    "breeding": ("Cuidar el vínculo", "Financiar la guardería", "Aceptar el huevo incierto"),
    "contest": ("Observar el concurso", "Preparar una exhibición", "Buscar el gran premio"),
    "research": ("Archivar la pista", "Financiar el análisis", "Publicar la teoría"),
    "health": ("Descanso completo", "Recuperación activa", "Competir lesionado"),
    "economy": ("Proteger la caja", "Invertir en instalaciones", "Adelantar ingresos"),
    "media": ("Cerrar el vestuario", "Dar una entrevista medida", "Responder en directo"),
    "crime": ("Rechazar y documentar", "Investigar sin comprar", "Aceptar el trato"),
    "friendship": ("Escuchar primero", "Entrenar juntos", "Exigir una reacción"),
    "rivalry": ("Responder en el campo", "Estudiar cada detalle", "Aceptar el desafío"),
    "conservation": ("Detener las obras", "Rediseñar el proyecto", "Seguir adelante"),
    "regional_culture": ("Participar como invitado", "Integrarlo al club", "Convertirlo en espectáculo"),
    "contract": ("Aceptar estabilidad", "Negociar recursos", "Esperar otra oferta"),
    "training": ("Reducir la carga", "Trabajar una debilidad", "Doblar las sesiones"),
}

_OPTION_LABELS_EN = {
    "capture": ("Follow the tracks", "Change the search zone", "Enter the closed habitat"),
    "evolution": ("Wait for the moment", "Prepare the evolution", "Force the leap"),
    "breeding": ("Protect the bond", "Fund the nursery", "Accept the uncertain Egg"),
    "contest": ("Watch the contest", "Prepare an exhibition", "Chase the grand prize"),
    "research": ("Archive the lead", "Fund the analysis", "Publish the theory"),
    "health": ("Full rest", "Active recovery", "Compete hurt"),
    "economy": ("Protect the balance", "Invest in facilities", "Borrow against results"),
    "media": ("Close the locker room", "Give a measured interview", "Go live"),
    "crime": ("Refuse and document", "Investigate without buying", "Take the deal"),
    "friendship": ("Listen first", "Train together", "Demand a response"),
    "rivalry": ("Answer on the field", "Study every detail", "Accept the challenge"),
    "conservation": ("Stop construction", "Redesign the project", "Push ahead"),
    "regional_culture": ("Join as a guest", "Bring it into the club", "Turn it into a show"),
    "contract": ("Take stability", "Negotiate resources", "Wait for another offer"),
    "training": ("Reduce the load", "Train a weakness", "Double the sessions"),
}


def _stable_seed(*parts: object) -> int:
    digest = hashlib.sha256(":".join(str(part) for part in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def build_season_decision(run: CareerRun, slot: int = 0) -> CareerDecision:
    rng = random.Random(_stable_seed(run.seed, run.season_number, slot, "decision"))
    family = _decision_family(run, slot)
    variant = AUTHORIAL_VARIANTS[rng.randrange(len(AUTHORIAL_VARIANTS))]
    transparency = TRANSPARENCY_TIERS[rng.randrange(len(TRANSPARENCY_TIERS))]
    npc_kind = NPC_ARCHETYPES[rng.randrange(len(NPC_ARCHETYPES))]
    npc_name = _npc_name(run, npc_kind, rng)
    locale = "es" if run.locale.lower().startswith("es") else "en"
    effects = _effect_sets(family, run.mode)
    rewards = _reward_sets(run, family, npc_name, rng)
    title, base_body = _decision_story(run, family, rewards, locale)
    hook = _VARIANT_HOOKS[variant][0 if locale == "es" else 1]
    club = run.contract.club_name if run.contract else ("el club" if locale == "es" else "the club")
    trainer_class = run.build.classes[0]
    adapter = selected_class_effects(run.build.classes)["adapters"][0]
    if locale == "es":
        body = (
            f"{npc_name.split(' · ')[0]} lleva el caso a {club}. "
            f"{base_body} {hook} {trainer_class} cambia la respuesta posible: {adapter['description_es']}"
        )
    else:
        body = (
            f"{npc_name.split(' · ')[0]} brings the case to {club}. "
            f"{base_body} {hook} {trainer_class} changes what the staff can do: {adapter['description_en']}"
        )
    labels = (_OPTION_LABELS if locale == "es" else _OPTION_LABELS_EN).get(
        family,
        ("Proteger", "Invertir", "Apostar") if locale == "es" else ("Protect", "Invest", "Gamble"),
    )
    options = []
    for index, effect in enumerate(effects):
        gamble: Dict[str, object] = {}
        option_rewards = rewards[index]
        if index == 2:
            gamble = {
                "chance": 0.55 if run.mode == "simple" else 0.5,
                "success": {"reputation": 6, "development": 4},
                "failure": {"health": -8, "reputation": -3},
                "success_rewards": rewards[index],
                "failure_rewards": [],
            }
            option_rewards = []
        options.append(CareerDecisionOption(
            id=f"{family}:{run.season_number}:{slot}:{index}",
            label=labels[index],
            description=_option_description(index, rewards[index], locale),
            risk=RISK_TIERS[index],
            transparency=transparency if index == 2 else "full",
            guaranteed=effect,
            rewards=option_rewards,
            gamble=gamble,
        ))
    return CareerDecision(
        id=f"decision:{run.id}:{run.season_number}:{slot}",
        family=family,
        title=title,
        body=body,
        npc_name=npc_name,
        options=options,
        variant=variant,
    )


def apply_option(run: CareerRun, option: CareerDecisionOption) -> dict:
    applied = dict(option.guaranteed)
    for key, value in option.guaranteed.items():
        _apply_stat(run, key, int(value))
    if option.gamble:
        rng = random.Random(_stable_seed(run.seed, run.season_number, option.id, "gamble"))
        success = rng.random() < float(option.gamble.get("chance", 0.5))
        branch = dict(option.gamble.get("success" if success else "failure") or {})
        for key, value in branch.items():
            _apply_stat(run, key, int(value))
            applied[key] = applied.get(key, 0) + int(value)
        applied["gamble_success"] = success
        conditional_rewards = list(option.gamble.get("success_rewards" if success else "failure_rewards") or [])
    else:
        conditional_rewards = []
    granted = [
        result
        for reward in [*option.rewards, *conditional_rewards]
        if (result := _apply_reward(run, reward, option.id))
    ]
    if granted:
        applied["rewards"] = granted
    return applied


def _apply_stat(run: CareerRun, key: str, value: int) -> None:
    if key == "health":
        run.health = min(100, max(0, run.health + value))
    elif hasattr(run, key):
        setattr(run, key, int(getattr(run, key)) + value)


def _effect_sets(family: str, mode: str) -> tuple[dict, dict, dict]:
    scale = 1 if mode == "simple" else 2
    if family == "health":
        return ({"health": 8}, {"health": 3, "development": 2 * scale}, {"health": -2})
    if family in {"capture", "research", "conservation"}:
        return ({"scouting": 1}, {"scouting": 2 * scale, "finances": -1}, {"scouting": 3 * scale})
    if family in {"contract", "economy", "media"}:
        return ({"reputation": 1}, {"finances": 2 * scale}, {"reputation": 2})
    return ({"health": 2}, {"development": 2 * scale, "finances": -1}, {"development": 3 * scale})


def _reward_sets(run: CareerRun, family: str, npc_name: str, rng: random.Random) -> tuple[List[dict], List[dict], List[dict]]:
    candidates = [
        species for species in REGIONS[run.build.region].underdogs
        if run.ranked or (species != run.build.starter and all(entry.caught_species != species for entry in run.pokemon))
    ]
    rng.shuffle(candidates)
    first = candidates[0] if candidates else ""
    second = candidates[1] if len(candidates) > 1 else first
    third = candidates[2] if len(candidates) > 2 else second

    def pokemon(species: str) -> List[dict]:
        return [{"type": "pokemon", "species": species}] if species else [{"type": "item", "item": "Poké Ball", "quantity": 2}]

    def move(*preferred: str) -> List[dict]:
        chosen = choose_legal_taught_move(run.build.starter, preferred, rng.randrange(1 << 30))
        return [{"type": "move", "move": chosen}] if chosen else [{"type": "level", "levels": 2}]

    relationship = [{"type": "relationship", "name": npc_name, "amount": 2}]
    partner = next((entry for entry in run.pokemon if entry.is_partner), run.pokemon[0] if run.pokemon else None)
    evolution_levels = 4
    if partner is not None:
        target = next_evolution(
            partner.species,
            seed=_stable_seed(run.seed, partner.id),
            region=run.build.region,
        )
        if target is not None:
            evolution_levels = max(1, target[1] - partner.level)
    evolution_move = move("Return", "Protect")
    rewards: Dict[str, tuple[List[dict], List[dict], List[dict]]] = {
        "capture": (pokemon(first), pokemon(second), pokemon(third) + [{"type": "item", "item": "Premier Ball", "quantity": 1}]),
        "evolution": (
            [{"type": "item", "item": "Exp. Share", "quantity": 1}],
            [{"type": "level", "levels": evolution_levels}],
            [{"type": "level", "levels": evolution_levels}, *evolution_move],
        ),
        "breeding": (relationship, pokemon(first), pokemon(second) + [{"type": "item", "item": "Egg Incubator", "quantity": 1}]),
        "contest": ([{"type": "item", "item": "Contest Ribbon", "quantity": 1}], move("Swift", "Round"), relationship),
        "research": ([{"type": "item", "item": "Pokédex Upgrade", "quantity": 1}], move("Hidden Power", "Secret Power"), pokemon(first)),
        "health": ([{"type": "item", "item": "Super Potion", "quantity": 2}], move("Rest", "Protect"), relationship),
        "economy": ([{"type": "item", "item": "Club Voucher", "quantity": 1}], [{"type": "item", "item": "Poké Ball", "quantity": 3}], pokemon(first)),
        "media": (relationship, [{"type": "item", "item": "Press Pass", "quantity": 1}], pokemon(first)),
        "crime": ([{"type": "item", "item": "Evidence File", "quantity": 1}], move("Thief", "Knock Off"), relationship),
        "friendship": (relationship, move("Return", "Helping Hand"), pokemon(first)),
        "rivalry": (move("Quick Attack", "Protect"), [{"type": "item", "item": "Choice Scarf", "quantity": 1}], pokemon(first)),
        "conservation": (relationship, pokemon(first), [{"type": "item", "item": "Ranger Kit", "quantity": 1}]),
        "regional_culture": ([{"type": "item", "item": f"{REGIONS[run.build.region].label} Charm", "quantity": 1}], relationship, pokemon(first)),
        "contract": ([{"type": "item", "item": "Facility Pass", "quantity": 1}], relationship, pokemon(first)),
        "training": ([{"type": "level", "levels": 2}], move("Protect", "Substitute"), pokemon(first)),
    }
    return rewards.get(family, (relationship, [{"type": "level", "levels": 2}], pokemon(first)))


def _option_description(index: int, rewards: List[dict], locale: str) -> str:
    reward = _reward_summary(rewards, locale)
    if locale == "es":
        return (
            f"Resultado garantizado: {reward}; no hay tirada oculta.",
            f"Pagás el coste indicado y asegurás {reward}.",
            f"La apuesta puede cambiar la temporada; si sale bien, además obtenés {reward}.",
        )[index]
    return (
        f"Guaranteed outcome: {reward}; there is no hidden roll.",
        f"Pay the stated cost and secure {reward}.",
        f"The gamble can change the season; on success you also secure {reward}.",
    )[index]


def _reward_summary(rewards: List[dict], locale: str) -> str:
    labels = []
    for reward in rewards:
        kind = reward.get("type")
        if kind == "pokemon": labels.append(str(reward.get("species")))
        elif kind == "move": labels.append(str(reward.get("move")))
        elif kind == "item": labels.append(f"{reward.get('quantity', 1)} × {reward.get('item')}")
        elif kind == "relationship": labels.append("una relación" if locale == "es" else "a relationship")
        elif kind == "level": labels.append(f"{reward.get('levels', 1)} " + ("niveles" if locale == "es" else "levels"))
    return ", ".join(labels) or ("progreso de carrera" if locale == "es" else "career progress")


def _apply_reward(run: CareerRun, reward: Dict[str, Any], source: str) -> Dict[str, Any] | None:
    reward_type = str(reward.get("type") or "")
    if reward_type == "pokemon":
        pokemon = capture_species(run, str(reward.get("species") or ""), source=f"decision:{source}")
        return {"type": "pokemon", "species": pokemon.species, "pokemon_id": pokemon.id} if pokemon else None
    if reward_type == "move":
        move = str(reward.get("move") or "")
        if teach_partner_move(run, move, source=f"decision:{source}"):
            return {"type": "move", "move": move, "target": run.build.starter}
        return None
    if reward_type == "level":
        levels = max(0, int(reward.get("levels") or 0))
        if not levels:
            return None
        grant_partner_levels(run, levels, source=f"decision:{source}")
        return {"type": "level", "levels": levels, "target": run.build.starter}
    if reward_type == "relationship":
        name = str(reward.get("name") or "League staff")
        amount = int(reward.get("amount") or 0)
        run.relationships[name] = run.relationships.get(name, 0) + amount
        effects = refresh_relationship_effects(run)
        run.timeline.append({
            "type": "relationship.changed", "season": run.season_number, "age": run.age,
            "name": name, "amount": amount, "value": run.relationships[name],
            "active_effects": dict(effects),
            "label": f"Relationship with {name} changed by {amount:+d}.",
        })
        return {"type": "relationship", "name": name, "amount": amount, "active_effects": dict(effects)}
    if reward_type == "item":
        item = str(reward.get("item") or "Supplies")
        quantity = max(1, int(reward.get("quantity") or 1))
        if item == "Poké Ball":
            run.build.pokeballs = min(30, run.build.pokeballs + quantity)
        else:
            run.inventory[item] = run.inventory.get(item, 0) + quantity
        run.timeline.append({
            "type": "item.acquired", "season": run.season_number, "age": run.age,
            "item": item, "quantity": quantity,
            "label": f"Acquired {quantity} × {item}.",
        })
        return {"type": "item", "item": item, "quantity": quantity}
    return None


def _decision_family(run: CareerRun, slot: int) -> str:
    """Surface urgent career state before falling back to authored rotation."""
    base_index = run.season_number - 1 + slot
    if run.ranked:
        # Daily attempts share the exact mechanical decision tree even when the
        # player chooses a different starter or class.
        return EVENT_DOMAINS[base_index % len(EVENT_DOMAINS)]
    if run.contract is None:
        return "contract"
    if run.health <= 55:
        return "health"
    partner = next((entry for entry in run.pokemon if entry.is_partner), run.pokemon[0] if run.pokemon else None)
    if partner is not None:
        target = next_evolution(
            partner.species,
            seed=_stable_seed(run.seed, partner.id),
            region=run.build.region,
        )
        if target is not None and partner.level >= max(1, target[1] - 6):
            return "evolution"
    if len(run.pokemon) < 6 and base_index % 3 == 0:
        return "capture"
    return EVENT_DOMAINS[base_index % len(EVENT_DOMAINS)]


def _decision_story(
    run: CareerRun,
    family: str,
    rewards: tuple[List[dict], List[dict], List[dict]],
    locale: str,
) -> tuple[str, str]:
    partner = next((entry for entry in run.pokemon if entry.is_partner), run.pokemon[0] if run.pokemon else None)
    partner_name = partner.species if partner else run.build.starter
    partner_level = partner.level if partner else 1
    if family == "capture":
        species = next(
            (str(reward.get("species")) for option in rewards for reward in option if reward.get("type") == "pokemon"),
            "un Pokémon" if locale == "es" else "a Pokémon",
        )
        if locale == "es":
            return (
                f"{species} apareció cerca del estadio",
                f"El informe confirma que {species} está solo y puede sumarse al plantel. "
                f"Tenés {run.build.pokeballs} Poké Balls y {len(run.pokemon)}/6 plazas activas ocupadas.",
            )
        return (
            f"{species} appeared near the stadium",
            f"The report confirms {species} is alone and can join the squad. "
            f"You have {run.build.pokeballs} Poke Balls and {len(run.pokemon)}/6 active places occupied.",
        )
    if family == "evolution" and partner is not None:
        target = next_evolution(partner.species, seed=_stable_seed(run.seed, partner.id), region=run.build.region)
        if target is not None:
            evolved, threshold = target
            if locale == "es":
                return (
                    f"{partner_name} está listo para cambiar",
                    f"{partner_name} está en nivel {partner_level}; el umbral PTU para convertirse en "
                    f"{evolved} es {threshold}. El cuerpo técnico necesita una orden antes del calendario.",
                )
            return (
                f"{partner_name} is ready to change",
                f"{partner_name} is level {partner_level}; the PTU threshold for becoming {evolved} is "
                f"{threshold}. The staff needs an order before the schedule.",
            )
    if family == "rivalry":
        rivals = [club for club in REGIONS[run.build.region].clubs if club != (run.contract.club_name if run.contract else "")]
        rival = rivals[_stable_seed(run.seed, run.season_number, "rival-preview") % len(rivals)] if rivals else REGIONS[run.build.region].label
        if locale == "es":
            return (
                f"{rival} señaló a {partner_name}",
                f"El próximo rival publicó un análisis de {partner_name} y prepara una respuesta específica. "
                "Ignorarlo, estudiarlo o responder cambia la preparación real del cruce.",
            )
        return (
            f"{rival} called out {partner_name}",
            f"The next opponent published an analysis of {partner_name} and is preparing a specific answer. "
            "Ignoring, studying or answering it changes the real match preparation.",
        )
    if family == "friendship":
        bond = max(run.relationships.values(), default=0)
        if locale == "es":
            return (
                "Un vínculo exige una respuesta",
                f"Tu contacto más cercano está en vínculo {bond}. Esta decisión puede convertir esa relación "
                "en preparación, recuperación o protección contractual.",
            )
        return (
            "A bond demands an answer",
            f"Your strongest contact is at bond {bond}. This choice can turn that relationship into preparation, "
            "recovery or contract protection.",
        )
    if family == "training":
        if locale == "es":
            return (
                f"{partner_name} no puede entrenar todo",
                f"{partner_name} llega en nivel {partner_level}. El staff debe elegir entre descanso, "
                "niveles PTU o un movimiento legal antes del calendario.",
            )
        return (
            f"{partner_name} cannot train everything",
            f"{partner_name} enters at level {partner_level}. Staff must choose rest, PTU levels or a legal move before the schedule.",
        )
    return _COPY[locale].get(family, _COPY[locale]["default"])


def _npc_name(run: CareerRun, kind: str, rng: random.Random) -> str:
    region = run.build.region
    existing = sorted(
        name for name in run.relationships
        if f" · {kind} · " in name and name.lower().endswith(region.lower())
    )
    if existing and rng.random() < 0.75:
        return existing[rng.randrange(len(existing))]
    names = FRANCHISE_TRAINERS[region][kind]
    identity = _stable_seed(region, kind, run.season_number, len(run.relationships), "career-contact")
    return f"{names[identity % len(names)]} · {kind} · {region.title()}"
