from __future__ import annotations

import hashlib
import random
from typing import Dict

from .catalogs import EVENT_DOMAINS, NPC_ARCHETYPES, RISK_TIERS, TRANSPARENCY_TIERS
from .models import CareerDecision, CareerDecisionOption, CareerRun


_COPY = {
    "en": {
        "capture": ("A lead beyond the training ground", "A scout has found tracks from a Pokémon the club overlooked."),
        "health": ("The season is leaving marks", "The medical staff asks how much recovery the next result is worth."),
        "contract": ("An offer with sharp edges", "A club from another region has made contact before the table settles."),
        "training": ("One week, one priority", "There is only enough time to change one part of the squad before the next fixture."),
        "default": ("The world moves around the league", "A choice away from the arena will shape the next season."),
    },
    "es": {
        "capture": ("Una pista fuera del campo", "Un ojeador encontró rastros de un Pokémon que el club había pasado por alto."),
        "health": ("La temporada está dejando marcas", "El cuerpo médico pregunta cuánto descanso merece el próximo resultado."),
        "contract": ("Una oferta con aristas", "Un club de otra región contactó antes de que cierre la clasificación."),
        "training": ("Una semana, una prioridad", "Sólo hay tiempo para cambiar una parte del equipo antes del próximo cruce."),
        "default": ("El mundo se mueve alrededor de la liga", "Una decisión fuera de la arena cambiará la próxima temporada."),
    },
}


def _stable_seed(*parts: object) -> int:
    digest = hashlib.sha256(":".join(str(part) for part in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def build_season_decision(run: CareerRun, slot: int = 0) -> CareerDecision:
    rng = random.Random(_stable_seed(run.seed, run.season_number, slot, "decision"))
    family = EVENT_DOMAINS[(run.season_number - 1 + slot) % len(EVENT_DOMAINS)]
    risk = RISK_TIERS[rng.randrange(len(RISK_TIERS))]
    transparency = TRANSPARENCY_TIERS[rng.randrange(len(TRANSPARENCY_TIERS))]
    npc_kind = NPC_ARCHETYPES[rng.randrange(len(NPC_ARCHETYPES))]
    npc_name = _npc_name(run.build.region, npc_kind, rng)
    locale = "es" if run.locale.lower().startswith("es") else "en"
    title, body = _COPY[locale].get(family, _COPY[locale]["default"])
    effects = _effect_sets(family, run.mode)
    labels = (
        ("Proteger el proyecto", "Invertir en el futuro", "Apostarlo todo")
        if locale == "es"
        else ("Protect the project", "Invest in the future", "Risk everything")
    )
    descriptions = (
        ("Resultado estable y menor desgaste.", "Cede recursos ahora para crecer.", "Mayor techo, con una consecuencia real si falla.")
        if locale == "es"
        else ("A stable outcome with less strain.", "Spend resources now to grow.", "A higher ceiling with a real consequence on failure.")
    )
    options = []
    for index, effect in enumerate(effects):
        option_risk = RISK_TIERS[index]
        gamble: Dict[str, object] = {}
        if index == 2:
            gamble = {
                "chance": 0.55 if run.mode == "simple" else 0.5,
                "success": {"reputation": 6, "development": 4},
                "failure": {"health": -8, "reputation": -3},
            }
        options.append(
            CareerDecisionOption(
                id=f"{family}:{run.season_number}:{slot}:{index}",
                label=labels[index],
                description=descriptions[index],
                risk=option_risk,
                transparency=transparency if index == 2 else "full",
                guaranteed=effect,
                gamble=gamble,
            )
        )
    return CareerDecision(
        id=f"decision:{run.id}:{run.season_number}:{slot}",
        family=family,
        title=title,
        body=body,
        npc_name=npc_name,
        options=options,
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


def _npc_name(region: str, kind: str, rng: random.Random) -> str:
    first = ("Mara", "Ivo", "Sena", "Tomas", "Nia", "Rei", "Asha", "Milo")
    last = ("Vale", "Ortega", "Reed", "Kwan", "Moss", "Arden", "Sato", "Bell")
    return f"{first[rng.randrange(len(first))]} {last[rng.randrange(len(last))]} · {kind} · {region.title()}"
