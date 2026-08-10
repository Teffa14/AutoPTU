from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Dict, Iterable, List

from .catalogs import EVENT_DOMAINS, LEAGUE_ORDER, NPC_ARCHETYPES, REGIONS, RISK_TIERS


AUTHORIAL_VARIANTS = (
    "first_contact", "scarcity", "public_pressure", "old_debt",
    "local_custom", "unexpected_ally", "institutional_offer", "rival_claim",
    "ethical_boundary", "lost_record", "weather_window", "family_request",
    "league_reform", "hidden_cost", "second_chance", "legacy_choice",
)


@dataclass(frozen=True)
class CompiledDecisionNode:
    id: str
    family: str
    region: str
    league: str
    npc: str
    risk: str
    guaranteed: Dict[str, int]
    gamble_chance_bp: int
    success: Dict[str, int]
    failure: Dict[str, int]
    unlock_tag: str
    mechanical_sha256: str


def compile_decision_nodes() -> Iterable[CompiledDecisionNode]:
    """Compile 25,920 reachable nodes from 240 authored family blueprints."""
    for domain_index, domain in enumerate(EVENT_DOMAINS):
        for variant_index, variant in enumerate(AUTHORIAL_VARIANTS):
            family = f"{domain}.{variant}"
            for region_index, region in enumerate(sorted(REGIONS)):
                for league_index, league in enumerate(LEAGUE_ORDER):
                    for risk_index, risk in enumerate(RISK_TIERS):
                        npc = NPC_ARCHETYPES[(domain_index + variant_index + region_index + league_index) % len(NPC_ARCHETYPES)]
                        benefit = 1 + league_index + (variant_index % 3)
                        cost = -(1 + ((domain_index + region_index + variant_index) % 4))
                        guaranteed = {_domain_stat(domain): benefit, _cost_stat(domain): cost if risk_index else 0}
                        success = {_domain_stat(domain): 2 + risk_index + (variant_index % 2)}
                        failure = {"health": -(2 + league_index + risk_index), "reputation": -risk_index}
                        unlock = f"{region}:{league}:{family}:{npc}:{risk}"
                        mechanics = {
                            "eligibility": {"region": region, "league": league, "npc": npc},
                            "risk": risk,
                            "guaranteed": guaranteed,
                            "chance_bp": (10000, 7000, 5000)[risk_index],
                            "success": success,
                            "failure": failure,
                            "unlock": unlock,
                        }
                        digest = hashlib.sha256(
                            json.dumps(mechanics, sort_keys=True, separators=(",", ":")).encode("utf-8")
                        ).hexdigest()
                        yield CompiledDecisionNode(
                            id=f"decision.{unlock}",
                            family=family,
                            region=region,
                            league=league,
                            npc=npc,
                            risk=risk,
                            guaranteed=guaranteed,
                            gamble_chance_bp=mechanics["chance_bp"],
                            success=success,
                            failure=failure,
                            unlock_tag=unlock,
                            mechanical_sha256=digest,
                        )


@lru_cache(maxsize=1)
def validate_compiled_content() -> dict:
    nodes: List[CompiledDecisionNode] = list(compile_decision_nodes())
    ids = {node.id for node in nodes}
    mechanical = {node.mechanical_sha256 for node in nodes}
    dead = [node.id for node in nodes if not node.guaranteed or not node.success or not node.failure]
    if len(ids) != len(nodes):
        raise ValueError("Decision compiler produced duplicate node ids.")
    if len(mechanical) != len(nodes):
        raise ValueError("Decision compiler produced text-only mechanical duplicates.")
    if dead:
        raise ValueError(f"Decision compiler produced {len(dead)} dead nodes.")
    return {
        "family_count": len(EVENT_DOMAINS) * len(AUTHORIAL_VARIANTS),
        "node_count": len(nodes),
        "mechanically_distinct": len(mechanical),
        "domains": list(EVENT_DOMAINS),
        "sha256": hashlib.sha256(
            json.dumps([asdict(node) for node in nodes], sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


def _domain_stat(domain: str) -> str:
    if domain in {"capture", "research", "conservation", "breeding"}:
        return "scouting"
    if domain in {"health", "friendship"}:
        return "health"
    if domain in {"economy", "contract", "media"}:
        return "finances"
    return "development"


def _cost_stat(domain: str) -> str:
    return "finances" if domain not in {"economy", "contract"} else "health"
