from __future__ import annotations

from typing import Any, Dict

from .catalogs import LEAGUES, REGIONS
from .models import CareerRun, ClubContract
from .roster import grant_pokemon_levels, grant_stat_training


ITEM_CATALOG: Dict[str, Dict[str, str]] = {
    "Training Kit": {
        "description_es": "Sesión individual: +2 permanentes al stat elegido de un Pokémon.",
        "description_en": "Individual session: +2 permanent points to one chosen Pokémon stat.",
        "target": "pokemon_stat",
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


def item_catalog() -> Dict[str, Dict[str, str]]:
    return {name: dict(details) for name, details in ITEM_CATALOG.items()}


def training_catalog() -> Dict[str, Dict[str, Any]]:
    return {name: dict(details) for name, details in TRAINING_METHODS.items()}


def use_item(run: CareerRun, item: str, *, pokemon_id: str = "", stat: str = "") -> Dict[str, Any]:
    canonical = next((name for name in run.inventory if name.casefold() == str(item).strip().casefold()), "")
    if not canonical or run.inventory.get(canonical, 0) <= 0:
        raise ValueError("That item is not available in the bag.")
    target = next((entry for entry in run.pokemon if entry.id == pokemon_id), None)
    effects: Dict[str, Any] = {"item": canonical}
    if canonical == "Training Kit":
        if target is None:
            raise ValueError("Choose a Pokémon for the Training Kit.")
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
    if run.season.training_completed:
        raise ValueError("The training session for this season is already complete.")
    plan = TRAINING_METHODS.get(str(method).strip().lower())
    pokemon = next((entry for entry in run.pokemon if entry.id == pokemon_id), None)
    if plan is None:
        raise ValueError("Unknown training method.")
    if pokemon is None:
        raise ValueError("Choose a Pokémon from your roster.")
    applied: Dict[str, int] = {}
    for stat, amount in plan["stats"].items():
        trained = grant_stat_training(run, pokemon.id, stat, int(amount), source=f"season_training:{method}")
        if trained:
            applied[stat] = int(trained["amount"])
    if not applied:
        raise ValueError("That Pokémon has no room for this training plan.")
    run.season.training_completed = True
    run.season.training_method = str(method).strip().lower()
    event = {
        "type": "training.completed", "season": run.season_number, "age": run.age,
        "method": run.season.training_method, "pokemon_id": pokemon.id,
        "pokemon": pokemon.species, "stats": applied,
        "label": f"{pokemon.species} completed {run.season.training_method} training.",
    }
    run.timeline.append(event)
    return event
