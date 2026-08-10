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
    starters: tuple[str, ...]
    underdogs: tuple[str, ...]
    clubs: tuple[str, ...]
    arena_theme: str

    @property
    def partner_choices(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((*self.starters, *self.underdogs)))


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
        ("Bulbasaur", "Charmander", "Squirtle", "Pikachu", "Eevee"),
        (
            "Caterpie", "Weedle", "Pidgey", "Rattata", "Spearow", "Ekans", "Sandshrew", "Nidoran F",
            "Nidoran M", "Clefairy", "Vulpix", "Jigglypuff", "Zubat", "Oddish", "Paras", "Venonat",
            "Diglett", "Meowth", "Psyduck", "Mankey", "Growlithe", "Poliwag", "Abra", "Machop",
            "Bellsprout", "Tentacool", "Geodude", "Ponyta", "Slowpoke", "Magnemite", "Farfetch'd", "Doduo",
            "Seel", "Grimer", "Shellder", "Gastly", "Onix", "Drowzee", "Krabby", "Voltorb", "Exeggcute",
            "Cubone", "Lickitung", "Koffing", "Rhyhorn", "Tangela", "Horsea", "Goldeen", "Staryu",
            "Magikarp", "Ditto", "Porygon", "Omanyte", "Kabuto", "Dratini",
        ),
        ("Saffron Comets", "Cerulean Current", "Fuchsia Wardens"), "indigo-stone",
    ),
    "johto": RegionDefinition(
        "johto", "Johto",
        ("Chikorita", "Cyndaquil", "Totodile"),
        (
            "Sentret", "Hoothoot", "Ledyba", "Spinarak", "Chinchou", "Pichu", "Cleffa", "Igglybuff",
            "Togepi", "Natu", "Mareep", "Marill", "Sudowoodo", "Hoppip", "Aipom", "Sunkern", "Yanma",
            "Wooper", "Murkrow", "Misdreavus", "Unown", "Pineco", "Dunsparce", "Snubbull", "Teddiursa",
            "Slugma", "Swinub", "Corsola", "Remoraid", "Delibird", "Houndour", "Phanpy", "Smeargle",
            "Tyrogue", "Smoochum", "Elekid", "Magby", "Larvitar",
        ),
        ("Goldenrod Signals", "Ecruteak Bells", "Olivine Breakers"), "cedar-brass",
    ),
    "hoenn": RegionDefinition(
        "hoenn", "Hoenn",
        ("Treecko", "Torchic", "Mudkip"),
        (
            "Poochyena", "Zigzagoon", "Wurmple", "Lotad", "Seedot", "Taillow", "Wingull", "Ralts",
            "Surskit", "Shroomish", "Slakoth", "Nincada", "Whismur", "Makuhita", "Azurill", "Nosepass",
            "Skitty", "Sableye", "Mawile", "Aron", "Meditite", "Electrike", "Plusle", "Minun", "Volbeat",
            "Illumise", "Gulpin", "Carvanha", "Wailmer", "Numel", "Spoink", "Spinda", "Trapinch", "Cacnea",
            "Swablu", "Barboach", "Corphish", "Baltoy", "Lileep", "Anorith", "Feebas", "Castform", "Kecleon",
            "Shuppet", "Duskull", "Wynaut", "Snorunt", "Spheal", "Clamperl", "Luvdisc", "Bagon", "Beldum",
        ),
        ("Slateport Tides", "Mauville Dynamo", "Fortree Canopy"), "ocean-volcanic",
    ),
    "sinnoh": RegionDefinition(
        "sinnoh", "Sinnoh",
        ("Turtwig", "Chimchar", "Piplup"),
        (
            "Starly", "Bidoof", "Kricketot", "Shinx", "Budew", "Cranidos", "Shieldon", "Burmy", "Combee",
            "Pachirisu", "Buizel", "Cherubi", "Shellos", "Drifloon", "Buneary", "Glameow", "Chingling",
            "Stunky", "Bronzor", "Bonsly", "Mime Jr.", "Happiny", "Chatot", "Gible", "Munchlax", "Riolu",
            "Hippopotas", "Skorupi", "Croagunk", "Carnivine", "Finneon", "Mantyke", "Snover", "Rotom",
        ),
        ("Jubilife Press", "Canalave Anchors", "Snowpoint Crown"), "mountain-snow",
    ),
    "unova": RegionDefinition(
        "unova", "Unova",
        ("Snivy", "Tepig", "Oshawott"),
        (
            "Patrat", "Lillipup", "Purrloin", "Pansage", "Pansear", "Panpour", "Munna", "Pidove", "Blitzle",
            "Roggenrola", "Woobat", "Drilbur", "Audino", "Timburr", "Tympole", "Sewaddle", "Venipede",
            "Cottonee", "Petilil", "Sandile", "Darumaka", "Dwebble", "Scraggy", "Yamask", "Tirtouga", "Archen",
            "Trubbish", "Zorua", "Minccino", "Gothita", "Solosis", "Ducklett", "Vanillite", "Deerling", "Emolga",
            "Karrablast", "Foongus", "Frillish", "Joltik", "Ferroseed", "Klink", "Tynamo", "Elgyem", "Litwick",
            "Axew", "Cubchoo", "Shelmet", "Mienfoo", "Golett", "Pawniard", "Rufflet", "Vullaby", "Deino", "Larvesta",
        ),
        ("Castelia Borough", "Nimbasa Voltage", "Driftveil Union"), "metro-steel",
    ),
    "kalos": RegionDefinition(
        "kalos", "Kalos",
        ("Chespin", "Fennekin", "Froakie"),
        (
            "Bunnelby", "Fletchling", "Scatterbug", "Litleo", "Flabebe", "Skiddo", "Pancham", "Espurr",
            "Honedge", "Spritzee", "Swirlix", "Inkay", "Binacle", "Skrelp", "Clauncher", "Helioptile", "Tyrunt",
            "Amaura", "Dedenne", "Goomy", "Phantump", "Bergmite", "Noibat",
        ),
        ("Lumiose Atelier", "Cyllage Peloton", "Laverre Masque"), "prism-garden",
    ),
    "alola": RegionDefinition(
        "alola", "Alola",
        ("Rowlet", "Litten", "Popplio"),
        (
            "Rattata Alolan", "Sandshrew Alolan", "Vulpix Alolan", "Diglett Alolan", "Meowth Alolan", "Geodude Alolan",
            "Grimer Alolan", "Pikipek", "Yungoos", "Grubbin", "Crabrawler", "Cutiefly", "Rockruff", "Mareanie",
            "Mudbray", "Dewpider", "Fomantis", "Morelull", "Salandit", "Stufful", "Bounsweet", "Wimpod",
            "Sandygast", "Pyukumuku", "Togedemaru", "Jangmo-o", "Cosmog", "Poipole", "Meltan",
        ),
        ("Hau'oli Breakers", "Konikoni Forge", "Malie Stars"), "island-sunset",
    ),
    "galar": RegionDefinition(
        "galar", "Galar",
        ("Grookey", "Scorbunny", "Sobble"),
        (
            "Meowth Galar", "Ponyta Galar", "Farfetch'd Galar", "Corsola Galar", "Zigzagoon Galar", "Darumaka Galar",
            "Yamask Galar", "Slowpoke Galar", "Skwovet", "Rookidee", "Blipbug", "Nickit", "Gossifleur", "Wooloo",
            "Chewtle", "Yamper", "Rolycoly", "Applin", "Silicobra", "Arrokuda", "Toxel", "Sizzlipede", "Clobbopus",
            "Sinistea", "Hatenna", "Impidimp", "Milcery", "Pincurchin", "Snom", "Morpeko", "Cufant", "Dreepy", "Kubfu",
        ),
        ("Motostoke Engine", "Hulbury Fleet", "Hammerlocke Keep"), "stadium-industrial",
    ),
    "paldea": RegionDefinition(
        "paldea", "Paldea",
        ("Sprigatito", "Fuecoco", "Quaxly"),
        (
            "Lechonk", "Tarountula", "Nymble", "Pawmi", "Tandemaus", "Fidough", "Smoliv", "Squawkabilly",
            "Nacli", "Charcadet", "Tadbulb", "Wattrel", "Maschiff", "Shroodle", "Bramblin", "Toedscool", "Klawf",
            "Capsakid", "Rellor", "Flittle", "Tinkatink", "Wiglett", "Finizen", "Varoom", "Glimmet", "Greavard",
            "Cetoddle", "Frigibax", "Gimmighoul",
        ),
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
            "starters": list(region.starters),
            "underdogs": list(region.underdogs),
            "partner_choices": list(region.partner_choices),
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
