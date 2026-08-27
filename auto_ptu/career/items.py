from __future__ import annotations

from typing import Any, Dict

from .catalogs import LEAGUES, REGIONS
from .models import CareerRun, ClubContract
from .roster import TRAINING_KIT_WEAR, grant_pokemon_levels, grant_stat_training


ITEM_CATALOG: Dict[str, Dict[str, Any]] = {
    "Training Kit": {
        "description_es": f"Sesión individual: +2 permanentes al stat elegido. Consume {TRAINING_KIT_WEAR} de vida útil competitiva del Pokémon; al llegar a 0 se retira. No puede retirar al último Pokémon disponible de una carrera activa.",
        "description_en": f"Individual session: +2 permanent points to one chosen stat. Costs {TRAINING_KIT_WEAR} Pokémon career health; at 0 the Pokémon retires. It cannot retire the final available Pokémon in an active career.",
        "target": "pokemon_stat",
        "career_health_cost": TRAINING_KIT_WEAR,
    },
    "Exp. Share": {
        "description_es": "Otorga 3 niveles al Pokémon elegido y evoluciona automáticamente si corresponde.",
        "description_en": "Gives 3 levels to the chosen Pokémon and evolves it automatically when eligible.",
        "target": "pokemon",
    },
    "Super Potion": {
        "description_es": "Recupera 12 puntos de salud de carrera.",
        "description_en": "Restores 12 career health.",
        "target": "none",
    },
    "Pokédex Upgrade": {
        "description_es": "Mejora el escaneo de hábitats: desplaza 3% de encuentros comunes hacia la rareza más alta disponible.",
        "description_en": "Improves habitat scans: shifts 3% of common encounters toward the highest available rarity.",
        "target": "none",
    },
    "Club Voucher": {
        "description_es": "Extiende el contrato una temporada y elimina la primera advertencia por falta de club.",
        "description_en": "Extends the contract one season and clears the first no-club warning.",
        "target": "none",
    },
    "Press Pass": {
        "description_es": "Una aparición coordinada concede +2 reputación.",
        "description_en": "A coordinated appearance grants +2 reputation.",
        "target": "none",
    },
    "Facility Pass": {
        "description_es": "Acceso al centro de alto rendimiento: +2 desarrollo.",
        "description_en": "High-performance center access: +2 development.",
        "target": "none",
    },
    "Choice Scarf": {
        "description_es": "Trabajo de velocidad: +3 VEL permanentes al Pokémon elegido.",
        "description_en": "Speed work: +3 permanent SPD to the chosen Pokémon.",
        "target": "pokemon",
    },
    "Ranger Kit": {
        "description_es": "Equipo de exploración: +2 scouting y 2 Poké Balls.",
        "description_en": "Exploration equipment: +2 scouting and 2 Poké Balls.",
        "target": "none",
    },
    "Evidence File": {
        "description_es": "Protege la licencia y concede +1 reputación por cooperación con la Liga.",
        "description_en": "Protects the license and grants +1 reputation for League cooperation.",
        "target": "none",
    },
    "Contest Ribbon": {
        "description_es": "Exhibirla en un evento concede +2 reputación.",
        "description_en": "Displaying it at an event grants +2 reputation.",
        "target": "none",
    },
    "Egg Incubator": {
        "description_es": "Plan de crianza asistida: +2 niveles al Pokémon elegido.",
        "description_en": "Assisted breeding plan: +2 levels to the chosen Pokémon.",
        "target": "pokemon",
    },
    "Premier Ball": {
        "description_es": "Se convierte en una Poké Ball disponible para la próxima captura.",
        "description_en": "Converts into one Poké Ball available for the next capture.",
        "target": "none",
    },
    "Mega Stone": {
        "description_es": "Desbloquea Megaevolución para un Pokémon compatible. Sólo puede activarse un gimmick por equipo y combate.",
        "description_en": "Unlocks Mega Evolution for a compatible Pokémon. Only one gimmick can activate per team and battle.",
        "target": "pokemon",
    },
    "Z-Crystal": {
        "description_es": "Desbloquea un Movimiento Z para el Pokémon elegido y potencia su ofensiva en combate.",
        "description_en": "Unlocks a Z-Move for the chosen Pokémon and boosts its offense in battle.",
        "target": "pokemon",
    },
    "Dynamax Band": {
        "description_es": "Desbloquea Dynamax para el Pokémon elegido y aumenta considerablemente sus PS en combate.",
        "description_en": "Unlocks Dynamax for the chosen Pokémon and substantially increases its battle HP.",
        "target": "pokemon",
    },
    "Tera Orb": {
        "description_es": "Desbloquea Teracristalización para el Pokémon elegido y potencia su adaptación ofensiva y defensiva.",
        "description_en": "Unlocks Terastallization for the chosen Pokémon and boosts offensive and defensive adaptation.",
        "target": "pokemon",
    },
}


GIMMICK_ITEMS: Dict[str, str] = {
    "Mega Stone": "mega_evolution",
    "Z-Crystal": "z_move",
    "Dynamax Band": "dynamax",
    "Tera Orb": "terastallization",
}

MEGA_CAPABLE = {
    "venusaur", "charizard", "blastoise", "beedrill", "pidgeot", "alakazam", "slowbro", "gengar",
    "kangaskhan", "pinsir", "gyarados", "aerodactyl", "mewtwo", "ampharos", "steelix", "scizor",
    "heracross", "houndoom", "tyranitar", "sceptile", "blaziken", "swampert", "gardevoir", "sableye",
    "mawile", "aggron", "medicham", "manectric", "sharpedo", "camerupt", "altaria", "banette", "absol",
    "glalie", "salamence", "metagross", "latias", "latios", "rayquaza", "lopunny", "garchomp", "lucario",
    "abomasnow", "gallade", "audino", "diancie",
}


SHOP_CATALOG: Dict[str, Dict[str, Any]] = {
    "pokeball": {
        "label_es": "Poké Ball",
        "label_en": "Poké Ball",
        "description_es": "Añade una Poké Ball disponible para una futura captura.",
        "description_en": "Adds one Poké Ball for a future capture.",
        "price": 30,
        "kind": "pokeball",
    },
    "super_potion": {
        "label_es": "Super Potion",
        "label_en": "Super Potion",
        "description_es": "Se guarda en la mochila y recupera 12 de salud de carrera.",
        "description_en": "Stored in the bag; restores 12 career health.",
        "price": 75,
        "kind": "item",
        "item": "Super Potion",
    },
    "club_resource": {
        "label_es": "Sanear recursos",
        "label_en": "Fund club resources",
        "description_es": "+1 recurso del club. Elimina un nivel de penalización si estás en deuda.",
        "description_en": "+1 club resource. Removes one preparation penalty while in debt.",
        "price": 100,
        "kind": "resource",
    },
    "training_kit": {
        "label_es": "Training Kit",
        "label_en": "Training Kit",
        "description_es": f"Se guarda en la mochila: +2 permanentes al stat elegido. Cada uso consume {TRAINING_KIT_WEAR} de vida útil competitiva del Pokémon y acelera su retiro. No puede retirar al último Pokémon disponible de una carrera activa.",
        "description_en": f"Stored in the bag: +2 permanent points to a chosen stat. Each use costs {TRAINING_KIT_WEAR} Pokémon career health and accelerates retirement. It cannot retire the final available Pokémon in an active career.",
        "price": 125,
        "kind": "item",
        "item": "Training Kit",
        "career_health_cost": TRAINING_KIT_WEAR,
    },
    "facility_pass": {
        "label_es": "Facility Pass",
        "label_en": "Facility Pass",
        "description_es": "Se guarda en la mochila y concede +2 desarrollo al usarlo.",
        "description_en": "Stored in the bag and grants +2 development when used.",
        "price": 180,
        "kind": "item",
        "item": "Facility Pass",
    },
    "pokedex_upgrade": {
        "label_es": "Pokédex Upgrade",
        "label_en": "Pokédex Upgrade",
        "description_es": "Mejora permanentemente la probabilidad de encuentros de mayor rareza.",
        "description_en": "Permanently improves the chance of higher-rarity encounters.",
        "price": 300,
        "kind": "item",
        "item": "Pokédex Upgrade",
    },
}


TRAINING_METHODS: Dict[str, Dict[str, Any]] = {
    "conditioning": {
        "label_es": "Fondo físico",
        "label_en": "Conditioning",
        "description_es": "+2 PS permanentes.",
        "description_en": "+2 permanent HP.",
        "stats": {"hp": 2},
    },
    "power": {
        "label_es": "Potencia mixta",
        "label_en": "Mixed power",
        "description_es": "+1 Ataque y +1 Ataque Especial permanentes.",
        "description_en": "+1 permanent Attack and Special Attack.",
        "stats": {"atk": 1, "spatk": 1},
    },
    "guard": {
        "label_es": "Bloque defensivo",
        "label_en": "Defensive block",
        "description_es": "+1 Defensa y +1 Defensa Especial permanentes.",
        "description_en": "+1 permanent Defense and Special Defense.",
        "stats": {"def": 1, "spdef": 1},
    },
    "agility": {
        "label_es": "Agilidad",
        "label_en": "Agility",
        "description_es": "+2 Velocidad permanentes.",
        "description_en": "+2 permanent Speed.",
        "stats": {"spd": 2},
    },
}


def item_catalog() -> Dict[str, Dict[str, Any]]:
    return {name: dict(details) for name, details in ITEM_CATALOG.items()}


def training_catalog() -> Dict[str, Dict[str, Any]]:
    return {name: dict(details) for name, details in TRAINING_METHODS.items()}


def shop_catalog() -> Dict[str, Dict[str, Any]]:
    return {product_id: dict(details) for product_id, details in SHOP_CATALOG.items()}


def buy_product(run: CareerRun, product_id: str) -> Dict[str, Any]:
    if run.status != "active":
        raise ValueError("Purchases are only available during an active career.")
    canonical = str(product_id).strip().lower()
    product = SHOP_CATALOG.get(canonical)
    if product is None:
        raise ValueError("That market product does not exist.")
    price = int(product["price"])
    if run.money < price:
        raise ValueError(f"Not enough money: this purchase costs ₽ {price}.")

    run.money -= price
    effects: Dict[str, Any] = {"product_id": canonical, "price": price, "money": run.money}
    kind = str(product["kind"])
    if kind == "pokeball":
        run.build.pokeballs = min(30, run.build.pokeballs + 1)
        effects["pokeballs"] = 1
    elif kind == "resource":
        run.finances += 1
        effects["finances"] = 1
    elif kind == "item":
        item = str(product["item"])
        run.inventory[item] = run.inventory.get(item, 0) + 1
        effects.update({"item": item, "quantity": 1})
    else:
        raise ValueError("That market product is not configured.")

    run.timeline.append({
        "type": "market.purchase",
        "season": run.season_number,
        "age": run.age,
        "product_id": canonical,
        "label": str(product["label_en"]),
        "effects": effects,
    })
    return effects


def use_item(run: CareerRun, item: str, *, pokemon_id: str = "", stat: str = "") -> Dict[str, Any]:
    canonical = next((name for name in run.inventory if name.casefold() == str(item).strip().casefold()), "")
    if not canonical or run.inventory.get(canonical, 0) <= 0:
        raise ValueError("That item is not available in the bag.")
    target = next((entry for entry in run.pokemon if entry.id == pokemon_id), None)
    effects: Dict[str, Any] = {"item": canonical}
    if canonical == "Training Kit":
        if target is None:
            raise ValueError("Choose a Pokémon for the Training Kit.")
        available = [entry for entry in run.pokemon if entry.status != "retired" and entry.career_health > 0]
        if run.status == "active" and target in available and len(available) == 1 and target.career_health <= TRAINING_KIT_WEAR:
            raise ValueError("The Training Kit would retire the final available Pokémon. Add another available Pokémon before using it.")
        trained = grant_stat_training(run, target.id, stat, 2, source="item:training_kit")
        if trained is None:
            raise ValueError("Choose a valid stat that has room for more training.")
        effects.update({"pokemon": target.species, "stat": trained["stat"], "amount": trained["amount"]})
    elif canonical in {"Exp. Share", "Egg Incubator"}:
        if target is None:
            raise ValueError("Choose a Pokémon to receive the item.")
        levels = 3 if canonical == "Exp. Share" else 2
        before = target.level
        evolutions = grant_pokemon_levels(run, target.id, levels, source=f"item:{canonical}")
        effects.update({"pokemon": target.species, "levels": target.level - before, "evolutions": evolutions})
    elif canonical == "Choice Scarf":
        if target is None:
            raise ValueError("Choose a Pokémon for the Choice Scarf training.")
        trained = grant_stat_training(run, target.id, "spd", 3, source="item:choice_scarf")
        if trained is None:
            raise ValueError("That Pokémon cannot gain more Speed training.")
        effects.update({"pokemon": target.species, "stat": "spd", "amount": trained["amount"]})
    elif canonical == "Super Potion":
        before = run.health
        run.health = min(100, run.health + 12)
        effects["health"] = run.health - before
    elif canonical == "Pokédex Upgrade":
        run.pokedex_level += 1
        effects["pokedex_level"] = run.pokedex_level
    elif canonical == "Club Voucher":
        run.seasons_without_contract = 0
        if run.contract is None:
            club = REGIONS[run.build.region].clubs[run.season_number % len(REGIONS[run.build.region].clubs)]
            run.contract = ClubContract(
                club_id="-".join(club.lower().split()), club_name=club, region=run.build.region,
                league=run.league, salary=120 * LEAGUES[run.league].weight + max(0, run.reputation * 5),
                seasons_remaining=2, loan_slots=1 + int(run.league in {"regular", "elite"}),
            )
        else:
            run.contract.seasons_remaining += 1
        effects["contract_seasons"] = run.contract.seasons_remaining
    elif canonical == "Press Pass":
        run.reputation += 2
        effects["reputation"] = 2
    elif canonical == "Facility Pass":
        run.development += 2
        effects["development"] = 2
    elif canonical == "Ranger Kit":
        run.scouting += 2
        run.build.pokeballs = min(30, run.build.pokeballs + 2)
        effects.update({"scouting": 2, "pokeballs": 2})
    elif canonical == "Evidence File":
        run.license_status = "active"
        run.reputation += 1
        effects.update({"license_status": "active", "reputation": 1})
    elif canonical == "Contest Ribbon":
        run.reputation += 2
        effects["reputation"] = 2
    elif canonical == "Premier Ball":
        run.build.pokeballs = min(30, run.build.pokeballs + 1)
        effects["pokeballs"] = 1
    elif canonical in GIMMICK_ITEMS:
        if target is None:
            raise ValueError("Choose a Pokémon to receive this battle gimmick.")
        gimmick = GIMMICK_ITEMS[canonical]
        if gimmick == "mega_evolution" and target.species.casefold() not in MEGA_CAPABLE:
            raise ValueError(f"{target.species} does not have a known Mega Evolution.")
        if gimmick in target.gimmicks:
            raise ValueError(f"{target.species} has already unlocked that gimmick.")
        target.gimmicks.append(gimmick)
        effects.update({"pokemon": target.species, "pokemon_id": target.id, "gimmick": gimmick})
    elif canonical.endswith(" Charm"):
        run.pokedex_level += 1
        run.scouting += 1
        effects.update({"pokedex_level": run.pokedex_level, "scouting": 1})
    else:
        raise ValueError("This item does not have a career use yet.")

    remaining = run.inventory[canonical] - 1
    if remaining > 0:
        run.inventory[canonical] = remaining
    else:
        run.inventory.pop(canonical, None)
    run.timeline.append({
        "type": "item.used", "season": run.season_number, "age": run.age,
        "item": canonical, "effects": effects, "label": f"Used {canonical}.",
    })
    return effects


def complete_training(run: CareerRun, method: str, pokemon_id: str) -> Dict[str, Any]:
    if run.status != "active" or run.season is None or run.season.status != "decision":
        raise ValueError("Training is only available before the season calendar is locked.")
    capacity = 1 if run.mode == "simple" else max(1, len(run.active_roster))
    completed_ids = run.season.training_completed_ids
    if run.season.training_completed or len(completed_ids) >= capacity:
        raise ValueError("The training session for this season is already complete.")
    plan = TRAINING_METHODS.get(str(method).strip().lower())
    pokemon = next((entry for entry in run.pokemon if entry.id == pokemon_id), None)
    if plan is None:
        raise ValueError("Unknown training method.")
    if pokemon is None:
        raise ValueError("Choose a Pokémon from your roster.")
    if pokemon.id not in run.active_roster:
        raise ValueError("Season training is reserved for the active team.")
    if pokemon.id in completed_ids:
        raise ValueError("That Pokémon has already trained this season.")
    applied: Dict[str, int] = {}
    for stat, amount in plan["stats"].items():
        trained = grant_stat_training(run, pokemon.id, stat, int(amount), source=f"season_training:{method}")
        if trained:
            applied[stat] = int(trained["amount"])
    if not applied:
        raise ValueError("That Pokémon has no room for this training plan.")
    completed_ids.append(pokemon.id)
    run.season.training_completed = len(completed_ids) >= capacity
    run.season.training_method = str(method).strip().lower()
    event = {
        "type": "training.completed", "season": run.season_number, "age": run.age,
        "method": run.season.training_method, "pokemon_id": pokemon.id,
        "pokemon": pokemon.species, "stats": applied,
        "sessions_completed": len(completed_ids), "sessions_available": capacity,
        "label": f"{pokemon.species} completed {run.season.training_method} training.",
    }
    run.timeline.append(event)
    return event
