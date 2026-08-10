from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class LeagueDefinition:
    id: str
    label: str
    weight: int
    matches: int
    min_level: int


@dataclass(frozen=True)
class RegionDefinition:
    id: str
    label: str
    underdogs: tuple[str, ...]
    clubs: tuple[str, ...]
    arena_theme: str


LEAGUES: Dict[str, LeagueDefinition] = {
    "junior": LeagueDefinition("junior", "Junior", 1, 6, 5),
    "rookie": LeagueDefinition("rookie", "Rookie", 2, 8, 10),
    "regular": LeagueDefinition("regular", "Regular", 4, 10, 20),
    "elite": LeagueDefinition("elite", "Elite", 8, 12, 35),
}

LEAGUE_ORDER = tuple(LEAGUES)

REGIONS: Dict[str, RegionDefinition] = {
    "kanto": RegionDefinition(
        "kanto", "Kanto",
        ("Rattata", "Caterpie", "Weedle", "Spearow", "Paras", "Venonat", "Krabby", "Cubone", "Horsea", "Goldeen", "Magikarp"),
        ("Saffron Comets", "Cerulean Current", "Fuchsia Wardens"), "indigo-stone",
    ),
    "johto": RegionDefinition(
        "johto", "Johto",
        ("Sentret", "Hoothoot", "Ledyba", "Spinarak", "Chinchou", "Natu", "Wooper", "Snubbull", "Slugma", "Remoraid", "Delibird"),
        ("Goldenrod Signals", "Ecruteak Bells", "Olivine Breakers"), "cedar-brass",
    ),
    "hoenn": RegionDefinition(
        "hoenn", "Hoenn",
        ("Poochyena", "Zigzagoon", "Wurmple", "Lotad", "Seedot", "Taillow", "Surskit", "Whismur", "Skitty", "Gulpin", "Spoink"),
        ("Slateport Tides", "Mauville Dynamo", "Fortree Canopy"), "ocean-volcanic",
    ),
    "sinnoh": RegionDefinition(
        "sinnoh", "Sinnoh",
        ("Bidoof", "Kricketot", "Shinx", "Burmy", "Combee", "Buizel", "Cherubi", "Shellos", "Stunky", "Chatot", "Finneon"),
        ("Jubilife Press", "Canalave Anchors", "Snowpoint Crown"), "mountain-snow",
    ),
    "unova": RegionDefinition(
        "unova", "Unova",
        ("Patrat", "Lillipup", "Purrloin", "Pidove", "Blitzle", "Roggenrola", "Woobat", "Tympole", "Sewaddle", "Venipede", "Dwebble"),
        ("Castelia Borough", "Nimbasa Voltage", "Driftveil Union"), "metro-steel",
    ),
    "kalos": RegionDefinition(
        "kalos", "Kalos",
        ("Bunnelby", "Fletchling", "Scatterbug", "Litleo", "Flabebe", "Skiddo", "Pancham", "Furfrou", "Espurr", "Spritzee", "Swirlix", "Inkay"),
        ("Lumiose Atelier", "Cyllage Peloton", "Laverre Masque"), "prism-garden",
    ),
    "alola": RegionDefinition(
        "alola", "Alola",
        ("Pikipek", "Yungoos", "Grubbin", "Crabrawler", "Cutiefly", "Rockruff", "Wishiwashi", "Mudbray", "Dewpider", "Fomantis", "Morelull", "Salandit"),
        ("Hau'oli Breakers", "Konikoni Forge", "Malie Stars"), "island-sunset",
    ),
    "galar": RegionDefinition(
        "galar", "Galar",
        ("Skwovet", "Rookidee", "Blipbug", "Nickit", "Gossifleur", "Wooloo", "Chewtle", "Yamper", "Rolycoly", "Silicobra", "Arrokuda", "Clobbopus"),
        ("Motostoke Engine", "Hulbury Fleet", "Hammerlocke Keep"), "stadium-industrial",
    ),
    "paldea": RegionDefinition(
        "paldea", "Paldea",
        ("Lechonk", "Tarountula", "Nymble", "Pawmi", "Tandemaus", "Fidough", "Smoliv", "Squawkabilly", "Nacli", "Charcadet", "Tadbulb", "Wattrel"),
        ("Mesagoza Scholars", "Levincia Circuit", "Medali Table"), "terra-mosaic",
    ),
}

EVENT_DOMAINS = (
    "capture", "evolution", "breeding", "contest", "research", "health",
    "economy", "media", "crime", "friendship", "rivalry", "conservation",
    "regional_culture", "contract", "training",
)
RISK_TIERS = ("safe", "calculated", "gamble")
TRANSPARENCY_TIERS = ("full", "estimated", "hidden")
NPC_ARCHETYPES = ("mentor", "rival", "owner")


def region_catalog() -> List[dict]:
    return [
        {
            "id": region.id,
            "label": region.label,
            "underdogs": list(region.underdogs),
            "clubs": list(region.clubs),
            "arena_theme": region.arena_theme,
        }
        for region in (REGIONS[key] for key in sorted(REGIONS))
    ]


def compiled_decision_signatures() -> Iterable[str]:
    """Enumerate mechanically distinct, versioned decision contexts."""
    for region_id in sorted(REGIONS):
        for league_id in LEAGUE_ORDER:
            for domain in EVENT_DOMAINS:
                for risk in RISK_TIERS:
                    for transparency in TRANSPARENCY_TIERS:
                        for npc in NPC_ARCHETYPES:
                            yield f"{region_id}:{league_id}:{domain}:{risk}:{transparency}:{npc}"


def compiled_decision_count() -> int:
    return sum(1 for _ in compiled_decision_signatures())
