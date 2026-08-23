from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List

from .catalogs import (
    EVENT_DOMAINS,
    FRANCHISE_TRAINERS,
    NPC_ARCHETYPES,
    REGIONS,
    RISK_TIERS,
    TRANSPARENCY_TIERS,
    choose_encounter_rarity,
    encounter_pool,
)
from .content_compiler import AUTHORIAL_VARIANTS
from .evolutions import next_evolution
from .models import CareerDecision, CareerDecisionOption, CareerRun
from .relationships import refresh_relationship_effects
from .ptu_builds import choose_legal_taught_move
from .roster import capture_species, grant_partner_levels, grant_stat_training, teach_partner_move


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
    if locale == "es":
        body = (
            f"{npc_name.split(' · ')[0]} lleva el caso a {club}. "
            f"{base_body} {hook} Tu experiencia como {trainer_class} abre una forma distinta de intervenir."
        )
    else:
        body = (
            f"{npc_name.split(' · ')[0]} brings the case to {club}. "
            f"{base_body} {hook} Your experience as a {trainer_class} opens a different way to intervene."
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
    owned = set() if run.ranked else {entry.caught_species.casefold() for entry in run.pokemon}
    recent = {
        str(species).casefold()
        for event in run.timeline[-40:]
        if event.get("type") == "pokemon.captured"
        for species in event.get("species", [])
    }
    used: set[str] = set()

    def encounter(minimum: str) -> tuple[str, str]:
        rarity = choose_encounter_rarity(
            run.build.region,
            run.league,
            rng,
            minimum=minimum,
            pokedex_level=run.pokedex_level,
        )
        pool = list(encounter_pool(run.build.region, rarity))
        rng.shuffle(pool)
        candidate = next(
            (entry for entry in pool if entry.casefold() not in owned | recent | used),
            next((entry for entry in pool if entry.casefold() not in used), pool[0] if pool else ""),
        )
        if candidate:
            used.add(candidate.casefold())
        return candidate, rarity

    first, first_rarity = encounter("common")
    second, second_rarity = encounter("rare")
    third, third_rarity = encounter("very_rare")

    def pokemon(species: str, rarity: str) -> List[dict]:
        return [{"type": "pokemon", "species": species, "rarity": rarity}] if species else [{"type": "item", "item": "Poké Ball", "quantity": 2}]

    def move(*preferred: str) -> List[dict]:
        chosen = choose_legal_taught_move(run.build.starter, preferred, rng.randrange(1 << 30))
        return [{"type": "move", "move": chosen}] if chosen else [{"type": "level", "levels": 2}]

    relationship = [{"type": "relationship", "name": npc_name, "amount": 2}]
    partner = next((entry for entry in run.pokemon if entry.is_partner), run.pokemon[0] if run.pokemon else None)
    target_id = partner.id if partner else ""
    target_species = partner.species if partner else run.build.starter

    def stat(name: str, amount: int) -> List[dict]:
        return [{"type": "stat", "pokemon_id": target_id, "species": target_species, "stat": name, "amount": amount}]

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
    regional_gimmick = {
        "kalos": "Mega Stone", "alola": "Z-Crystal", "galar": "Dynamax Band", "paldea": "Tera Orb",
    }.get(run.build.region, ("Mega Stone", "Z-Crystal", "Dynamax Band", "Tera Orb")[rng.randrange(4)])
    gimmick_reward = [{"type": "item", "item": regional_gimmick, "quantity": 1}]
    rewards: Dict[str, tuple[List[dict], List[dict], List[dict]]] = {
        "capture": (
            pokemon(first, first_rarity),
            pokemon(second, second_rarity),
            pokemon(third, third_rarity) + [{"type": "item", "item": "Premier Ball", "quantity": 1}],
        ),
        "evolution": (
            [{"type": "item", "item": "Exp. Share", "quantity": 1}],
            [{"type": "level", "levels": evolution_levels}],
            [{"type": "level", "levels": evolution_levels}, *evolution_move],
        ),
        "breeding": (relationship, pokemon(first, first_rarity), [{"type": "item", "item": "Egg Incubator", "quantity": 1}, *move("Return", "Helping Hand")]),
        "contest": ([{"type": "item", "item": "Contest Ribbon", "quantity": 1}], move("Swift", "Round"), relationship),
        "research": ([{"type": "item", "item": "Pokédex Upgrade", "quantity": 1}], move("Hidden Power", "Secret Power"), [*pokemon(second, second_rarity), *gimmick_reward]),
        "health": ([{"type": "item", "item": "Super Potion", "quantity": 2}], move("Rest", "Protect"), relationship),
        "economy": ([{"type": "item", "item": "Club Voucher", "quantity": 1}], [{"type": "item", "item": "Poké Ball", "quantity": 3}], [{"type": "item", "item": "Facility Pass", "quantity": 1}]),
        "media": (relationship, [{"type": "item", "item": "Press Pass", "quantity": 1}], [{"type": "item", "item": "Contest Ribbon", "quantity": 1}]),
        "crime": ([{"type": "item", "item": "Evidence File", "quantity": 1}], move("Thief", "Knock Off"), relationship),
        "friendship": (relationship, move("Return", "Helping Hand"), [{"type": "relationship", "name": npc_name, "amount": 4}]),
        "rivalry": (move("Quick Attack", "Protect"), [{"type": "item", "item": "Choice Scarf", "quantity": 1}], stat("spd", 3)),
        "conservation": (relationship, pokemon(first, first_rarity), [{"type": "item", "item": "Ranger Kit", "quantity": 1}]),
        "regional_culture": ([{"type": "item", "item": f"{REGIONS[run.build.region].label} Charm", "quantity": 1}], relationship, gimmick_reward),
        "contract": ([{"type": "item", "item": "Facility Pass", "quantity": 1}], relationship, [{"type": "item", "item": "Club Voucher", "quantity": 1}]),
        "training": (stat("hp", 2), stat(("atk", "def", "spatk", "spdef", "spd")[rng.randrange(5)], 2), [{"type": "level", "levels": 3}, *move("Protect", "Substitute")]),
    }
    return rewards.get(
        family,
        (relationship, [{"type": "level", "levels": 2}], [{"type": "item", "item": "Training Kit", "quantity": 1}]),
    )


def _option_description(index: int, rewards: List[dict], locale: str) -> str:
    reward = _reward_summary(rewards, locale)
    if locale == "es":
        return (
            f"Recibís: {reward}.",
            f"Pagás el coste indicado y asegurás {reward}.",
            f"Hay una tirada oculta: si sale bien, obtenés {reward}.",
        )[index]
    return (
        f"You receive: {reward}.",
        f"Pay the stated cost and secure {reward}.",
        f"There is a hidden roll: on success you receive {reward}.",
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
        elif kind == "stat": labels.append(
            f"{reward.get('species')} +{reward.get('amount', 1)} {_stat_label(str(reward.get('stat') or ''), locale)}"
        )
    return ", ".join(labels) or ("progreso de carrera" if locale == "es" else "career progress")


def _apply_reward(run: CareerRun, reward: Dict[str, Any], source: str) -> Dict[str, Any] | None:
    reward_type = str(reward.get("type") or "")
    if reward_type == "pokemon":
        pokemon = capture_species(run, str(reward.get("species") or ""), source=f"decision:{source}")
        return {
            "type": "pokemon", "species": pokemon.species, "pokemon_id": pokemon.id,
            "rarity": str(reward.get("rarity") or "common"),
        } if pokemon else None
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
    if reward_type == "stat":
        pokemon_id = str(reward.get("pokemon_id") or "")
        stat = str(reward.get("stat") or "")
        amount = max(0, int(reward.get("amount") or 0))
        event = grant_stat_training(run, pokemon_id, stat, amount, source=f"decision:{source}")
        if event is None:
            return None
        return {
            "type": "stat", "pokemon_id": pokemon_id, "species": event["species"],
            "stat": stat, "amount": event["amount"], "total": event["total"],
        }
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
    playable_domains = tuple(domain for domain in EVENT_DOMAINS if domain != "evolution")
    if run.ranked:
        # Daily attempts share the exact mechanical decision tree even when the
        # player chooses a different starter or class.
        return playable_domains[base_index % len(playable_domains)]
    if run.contract is None:
        return "contract"
    if run.health <= 55:
        return "health"
    if base_index % 3 == 0:
        return "capture"
    return playable_domains[base_index % len(playable_domains)]


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
        active_count = len(run.active_roster)
        pc_count = max(0, len(run.pokemon) - active_count)
        if locale == "es":
            return (
                f"{species} apareció cerca del estadio",
                f"El informe confirma que {species} está solo y puede sumarse al plantel. "
                f"Tenés {run.build.pokeballs} Poké Balls, {active_count}/6 plazas activas ocupadas y {pc_count} Pokémon en PC.",
            )
        return (
            f"{species} appeared near the stadium",
            f"The report confirms {species} is alone and can join the squad. "
            f"You have {run.build.pokeballs} Poke Balls, {active_count}/6 active places occupied and {pc_count} Pokemon in PC.",
        )
    if family == "breeding":
        species = next((str(reward.get("species")) for option in rewards for reward in option if reward.get("type") == "pokemon"), partner_name)
        if locale == "es":
            return (
                "La guardería abre una sola plaza",
                f"El cuidador puede trabajar el vínculo con {partner_name}, recibir a {species} o reservar la incubadora. "
                "Cada alternativa ocupa la semana completa y cambia quién llega al vestuario.",
            )
        return (
            "The nursery has one opening",
            f"The caretaker can work on {partner_name}'s bond, welcome {species}, or reserve the incubator. "
            "Each path consumes the full week and changes who enters the locker room.",
        )
    if family == "contest":
        if locale == "es":
            return (
                f"{REGIONS[run.build.region].label} prepara una exhibición nocturna",
                f"Los jueces invitaron a {partner_name}. Podés observar, ensayar un movimiento o competir por visibilidad, "
                "pero el tiempo usado acá no vuelve antes del calendario.",
            )
        return (
            f"{REGIONS[run.build.region].label} is preparing a night exhibition",
            f"The judges invited {partner_name}. You can observe, rehearse a move, or compete for attention, "
            "but the time spent here will not return before the schedule.",
        )
    if family == "research":
        if locale == "es":
            return (
                "Una señal nueva contradice el mapa del hábitat",
                f"El escáner está en nivel {run.pokedex_level}. Analizar la señal puede mejorar futuros encuentros, "
                "enseñar una técnica o revelar un Pokémon que el informe común no registró.",
            )
        return (
            "A new signal contradicts the habitat map",
            f"Your scanner is level {run.pokedex_level}. Studying the signal can improve future encounters, "
            "teach a technique or reveal a Pokémon missing from the common report.",
        )
    if family == "health":
        if locale == "es":
            return (
                "El parte médico exige cambiar la semana",
                f"Tu salud está en {run.health}/100. El equipo médico propone descanso, recuperación activa o competir con carga; "
                "la elección afecta cuánto podés sostener la carrera.",
            )
        return (
            "The medical report demands a different week",
            f"Your health is {run.health}/100. Staff offer rest, active recovery, or carrying the strain into competition; "
            "the choice affects how long the career can be sustained.",
        )
    if family in {"economy", "contract"}:
        salary = run.contract.salary if run.contract else 0
        warnings = run.seasons_without_contract
        if locale == "es":
            return (
                "La oficina del club puso números sobre la mesa",
                f"El salario actual es ₽ {salary} por temporada y llevás {warnings}/2 advertencias sin contrato. "
                "Podés proteger estabilidad, pedir recursos reales o exponerte a una oferta mejor.",
            )
        return (
            "The club office put real numbers on the table",
            f"Current salary is ₽ {salary} per season and you have {warnings}/2 no-contract warnings. "
            "You can protect stability, ask for usable resources or risk waiting for a better offer.",
        )
    if family == "media":
        if locale == "es":
            return (
                "Una cámara espera fuera del vestuario",
                f"Tu reputación está en {run.reputation}. La entrevista puede fortalecer un vínculo o abrir accesos, "
                "pero una respuesta impulsiva quedará asociada al club toda la temporada.",
            )
        return (
            "A camera is waiting outside the locker room",
            f"Your reputation is {run.reputation}. The interview can strengthen a bond or unlock access, "
            "but an impulsive answer will follow the club all season.",
        )
    if family == "crime":
        if locale == "es":
            return (
                "Un intermediario ofrece información que no debería tener",
                "La Liga no autorizó el contacto. Rechazar deja evidencia, investigar puede enseñar cómo opera la red y aceptar pone salud, reputación y licencia en juego.",
            )
        return (
            "A broker offers information they should not have",
            "The League did not authorize the contact. Refusing preserves evidence, investigating can expose the network, and accepting puts health, reputation and license at risk.",
        )
    if family == "conservation":
        if locale == "es":
            return (
                "El nuevo campo invade una ruta de migración",
                "El club quiere empezar obras mañana. Frenarlas protege vínculos y encuentros silvestres; rediseñar cuesta recursos; seguir cambia el hábitat para siempre.",
            )
        return (
            "The new facility crosses a migration route",
            "Construction starts tomorrow. Stopping it protects bonds and wild encounters; redesign costs resources; pushing ahead changes the habitat permanently.",
        )
    if family == "regional_culture":
        if locale == "es":
            return (
                f"Una tradición de {REGIONS[run.build.region].label} llega al club",
                f"La comunidad pidió que {partner_name} participe sin convertir la ceremonia en publicidad. "
                "La forma de responder define confianza local, scouting y acceso a encuentros regionales.",
            )
        return (
            f"A {REGIONS[run.build.region].label} tradition reaches the club",
            f"The community asked {partner_name} to participate without turning the ceremony into advertising. "
            "Your response shapes local trust, scouting and access to regional encounters.",
        )
    if family == "evolution" and partner is not None:
        target = next_evolution(partner.species, seed=_stable_seed(run.seed, partner.id), region=run.build.region)
        if target is not None:
            evolved, threshold = target
            if locale == "es":
                return (
                    f"{partner_name} está listo para cambiar",
                    f"{partner_name} está en nivel {partner_level}; su evolución natural a {evolved} ocurre "
                    f"al alcanzar el nivel {threshold}. El cuerpo técnico decide cómo acompañar su desarrollo.",
                )
            return (
                f"{partner_name} is ready to change",
                f"{partner_name} is level {partner_level}; its natural evolution into {evolved} happens "
                f"at level {threshold}. The staff must decide how to support that growth.",
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
                "resistencia, una mejora de stats o un movimiento antes del calendario.",
            )
        return (
            f"{partner_name} cannot train everything",
            f"{partner_name} enters at level {partner_level}. Staff must choose recovery, stat growth or a move before the schedule.",
        )
    return _COPY[locale].get(family, _COPY[locale]["default"])


def _stat_label(stat: str, locale: str) -> str:
    labels = {
        "hp": ("PS", "HP"), "atk": ("Ataque", "Attack"), "def": ("Defensa", "Defense"),
        "spatk": ("Ataque Especial", "Special Attack"), "spdef": ("Defensa Especial", "Special Defense"),
        "spd": ("Velocidad", "Speed"),
    }
    return labels.get(stat, (stat, stat))[0 if locale == "es" else 1]


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
