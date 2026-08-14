from __future__ import annotations

import random
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
        ("Saffron Comets", "Cerulean Current", "Fuchsia Wardens", "Pewter Foundry", "Vermilion Surge", "Celadon Canopy", "Lavender Echoes", "Cinnabar Forge"), "indigo-stone",
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
        ("Goldenrod Signals", "Ecruteak Bells", "Olivine Breakers", "Violet Rooks", "Azalea Hive", "Cianwood Storm", "Mahogany Red", "Blackthorn Drakes"), "cedar-brass",
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
        ("Slateport Tides", "Mauville Dynamo", "Fortree Canopy", "Rustboro Strata", "Lavaridge Caldera", "Lilycove Lights", "Mossdeep Orbit", "Sootopolis Depths"), "ocean-volcanic",
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
        ("Jubilife Press", "Canalave Anchors", "Snowpoint Crown", "Oreburgh Bedrock", "Eterna Grove", "Hearthome Union", "Veilstone Edge", "Sunyshore Current"), "mountain-snow",
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
        ("Castelia Borough", "Nimbasa Voltage", "Driftveil Union", "Striaton Trio", "Nacrene Archive", "Mistralton Wings", "Icirrus Thaw", "Opelucid Axis"), "metro-steel",
    ),
    "kalos": RegionDefinition(
        "kalos", "Kalos",
        ("Chespin", "Fennekin", "Froakie"),
        (
            "Bunnelby", "Fletchling", "Scatterbug", "Litleo", "Flabebe", "Skiddo", "Pancham", "Espurr",
            "Honedge", "Spritzee", "Swirlix", "Inkay", "Binacle", "Skrelp", "Clauncher", "Helioptile", "Tyrunt",
            "Amaura", "Dedenne", "Goomy", "Phantump", "Bergmite", "Noibat",
        ),
        ("Lumiose Atelier", "Cyllage Peloton", "Laverre Masque", "Santalune Silks", "Shalour Aura", "Coumarine Rails", "Anistar Dial", "Snowbelle Guard"), "prism-garden",
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
        ("Hau'oli Breakers", "Konikoni Forge", "Malie Stars", "Iki Kahunas", "Heahea Tides", "Paniola Riders", "Po Town Skulls", "Seafolk Voyagers"), "island-sunset",
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
        ("Motostoke Engine", "Hulbury Fleet", "Hammerlocke Keep", "Turffield Wool", "Stow-on-Side Relics", "Ballonlea Glamour", "Circhester Crown", "Spikemuth Noise"), "stadium-industrial",
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
        ("Mesagoza Scholars", "Levincia Circuit", "Medali Table", "Cortondo Harvest", "Artazon Sunflora", "Cascarrafa Cascades", "Montenevera Choir", "Alfornada Stars"), "terra-mosaic",
    ),
}

# Encounter pools are separate from the academy underdog catalogue.  The
# academy list remains the broad, low-power intake pool; career exploration can
# now surface progressively scarcer species without pretending that every wild
# meeting has the same value.
RARITY_ORDER = ("common", "rare", "very_rare", "epic", "legendary", "mythical")
RARITY_LABELS = {
    "common": ("Común", "Common"),
    "rare": ("Raro", "Rare"),
    "very_rare": ("Muy raro", "Very rare"),
    "epic": ("Épico", "Epic"),
    "legendary": ("Legendario", "Legendary"),
    "mythical": ("Mítico", "Mythical"),
}

REGIONAL_SPECIAL_ENCOUNTERS: Dict[str, Dict[str, tuple[str, ...]]] = {
    "kanto": {
        "rare": ("Scyther", "Pinsir", "Kangaskhan", "Chansey"),
        "very_rare": ("Lapras", "Snorlax", "Aerodactyl", "Dratini"),
        "epic": ("Dragonite", "Gyarados", "Arcanine", "Gengar"),
        "legendary": ("Articuno", "Zapdos", "Moltres", "Mewtwo"),
        "mythical": ("Mew",),
    },
    "johto": {
        "rare": ("Heracross", "Skarmory", "Stantler", "Miltank"),
        "very_rare": ("Larvitar", "Hitmontop", "Kingdra", "Blissey"),
        "epic": ("Tyranitar", "Scizor", "Houndoom", "Donphan"),
        "legendary": ("Raikou", "Entei", "Suicune", "Lugia", "Ho-Oh"),
        "mythical": ("Celebi",),
    },
    "hoenn": {
        "rare": ("Absol", "Tropius", "Chimecho", "Relicanth"),
        "very_rare": ("Bagon", "Beldum", "Feebas", "Spiritomb"),
        "epic": ("Salamence", "Metagross", "Milotic", "Flygon"),
        "legendary": ("Regirock", "Regice", "Registeel", "Latias", "Latios", "Kyogre", "Groudon", "Rayquaza"),
        "mythical": ("Jirachi", "Deoxys"),
    },
    "sinnoh": {
        "rare": ("Heracross", "Skuntank", "Toxicroak", "Drapion"),
        "very_rare": ("Gible", "Riolu", "Rotom", "Spiritomb"),
        "epic": ("Garchomp", "Lucario", "Togekiss", "Electivire"),
        "legendary": ("Uxie", "Mesprit", "Azelf", "Dialga", "Palkia", "Giratina", "Cresselia"),
        "mythical": ("Phione", "Manaphy", "Darkrai", "Shaymin", "Arceus"),
    },
    "unova": {
        "rare": ("Zorua", "Cryogonal", "Druddigon", "Bouffalant"),
        "very_rare": ("Deino", "Larvesta", "Axew", "Tynamo"),
        "epic": ("Hydreigon", "Volcarona", "Haxorus", "Chandelure"),
        "legendary": ("Cobalion", "Terrakion", "Virizion", "Tornadus", "Thundurus", "Reshiram", "Zekrom", "Kyurem"),
        "mythical": ("Victini", "Keldeo", "Meloetta", "Genesect"),
    },
    "kalos": {
        "rare": ("Hawlucha", "Klefki", "Trevenant", "Gourgeist"),
        "very_rare": ("Goomy", "Noibat", "Honedge", "Carbink"),
        "epic": ("Goodra", "Aegislash", "Noivern", "Tyrantrum"),
        "legendary": ("Xerneas", "Yveltal", "Zygarde"),
        "mythical": ("Diancie", "Hoopa", "Volcanion"),
    },
    "alola": {
        "rare": ("Oranguru", "Passimian", "Drampa", "Turtonator"),
        "very_rare": ("Jangmo-o", "Dhelmise", "Type: Null", "Minior"),
        "epic": ("Kommo-o", "Silvally", "Golisopod", "Mimikyu"),
        "legendary": ("Tapu Koko", "Tapu Lele", "Tapu Bulu", "Tapu Fini", "Solgaleo", "Lunala", "Necrozma"),
        "mythical": ("Magearna", "Marshadow", "Zeraora", "Meltan", "Melmetal"),
    },
    "galar": {
        "rare": ("Falinks", "Stonjourner", "Eiscue", "Indeedee"),
        "very_rare": ("Dreepy", "Dracozolt", "Arctozolt", "Dracovish", "Arctovish"),
        "epic": ("Dragapult", "Duraludon", "Grimmsnarl", "Hatterene"),
        "legendary": ("Zacian", "Zamazenta", "Eternatus", "Kubfu", "Urshifu", "Regieleki", "Regidrago"),
        "mythical": ("Zarude",),
    },
    "paldea": {
        "rare": ("Flamigo", "Cyclizar", "Orthworm", "Bombirdier"),
        "very_rare": ("Frigibax", "Gimmighoul", "Dondozo", "Tatsugiri"),
        "epic": ("Baxcalibur", "Gholdengo", "Kingambit", "Palafin"),
        "legendary": ("Wo-Chien", "Chien-Pao", "Ting-Lu", "Chi-Yu", "Koraidon", "Miraidon"),
        "mythical": ("Pecharunt",),
    },
}

_RARITY_WEIGHTS: Dict[str, tuple[int, ...]] = {
    "junior": (70, 25, 5, 0, 0, 0),
    "rookie": (50, 30, 15, 5, 0, 0),
    "regular": (30, 28, 22, 15, 5, 0),
    "elite": (18, 22, 23, 22, 11, 4),
}


def encounter_pool(region_id: str, rarity: str) -> tuple[str, ...]:
    region = REGIONS[region_id]
    if rarity == "common":
        special = {
            species.lower()
            for pool in REGIONAL_SPECIAL_ENCOUNTERS.get(region_id, {}).values()
            for species in pool
        }
        return tuple(species for species in region.underdogs if species.lower() not in special)
    return REGIONAL_SPECIAL_ENCOUNTERS.get(region_id, {}).get(rarity, ())


def all_region_encounters(region_id: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(
        species
        for rarity in RARITY_ORDER
        for species in encounter_pool(region_id, rarity)
    ))


def choose_encounter_rarity(
    region_id: str,
    league: str,
    rng: random.Random,
    *,
    minimum: str = "common",
    pokedex_level: int = 0,
) -> str:
    weights = list(_RARITY_WEIGHTS.get(league, _RARITY_WEIGHTS["junior"]))
    boost = min(12, max(0, int(pokedex_level)) * 3)
    weights[0] = max(1, weights[0] - boost)
    highest_unlocked = max(index for index, value in enumerate(weights) if value > 0)
    weights[highest_unlocked] += boost
    minimum_index = min(RARITY_ORDER.index(minimum), highest_unlocked)
    for index in range(minimum_index):
        weights[minimum_index] += weights[index]
        weights[index] = 0
    available = [
        index
        for index, weight in enumerate(weights)
        if weight > 0 and encounter_pool(region_id, RARITY_ORDER[index])
    ]
    if not available:
        return "common"
    picked = rng.choices(available, weights=[weights[index] for index in available], k=1)[0]
    return RARITY_ORDER[picked]
EVENT_DOMAINS = (
    "capture", "evolution", "breeding", "contest", "research", "health",
    "economy", "media", "crime", "friendship", "rivalry", "conservation",
    "regional_culture", "contract", "training",
)
RISK_TIERS = ("safe", "calculated", "gamble")
TRANSPARENCY_TIERS = ("full", "estimated", "hidden")
NPC_ARCHETYPES = ("mentor", "rival", "owner")

# Canonical trainers keep every regional relationship anchored in the games.
# The suffix remains machine-readable so relationship effects and old saves
# continue to use the same deterministic contract.
FRANCHISE_TRAINERS: Dict[str, Dict[str, tuple[str, ...]]] = {
    "kanto": {
        "mentor": ("Professor Oak", "Brock", "Misty"),
        "rival": ("Blue", "Red", "Trace"),
        "owner": ("Lance", "Erika", "Lt. Surge"),
    },
    "johto": {
        "mentor": ("Professor Elm", "Falkner", "Jasmine"),
        "rival": ("Silver", "Ethan", "Lyra"),
        "owner": ("Clair", "Morty", "Whitney"),
    },
    "hoenn": {
        "mentor": ("Professor Birch", "Roxanne", "Brawly"),
        "rival": ("Brendan", "May", "Wally"),
        "owner": ("Steven Stone", "Wallace", "Winona"),
    },
    "sinnoh": {
        "mentor": ("Professor Rowan", "Roark", "Gardenia"),
        "rival": ("Barry", "Lucas", "Dawn"),
        "owner": ("Cynthia", "Volkner", "Fantina"),
    },
    "unova": {
        "mentor": ("Professor Juniper", "Cheren", "Lenora"),
        "rival": ("Bianca", "Hilbert", "Hilda"),
        "owner": ("Alder", "Iris", "Elesa"),
    },
    "kalos": {
        "mentor": ("Professor Sycamore", "Korrina", "Viola"),
        "rival": ("Serena", "Calem", "Shauna"),
        "owner": ("Diantha", "Clemont", "Olympia"),
    },
    "alola": {
        "mentor": ("Professor Kukui", "Hala", "Olivia"),
        "rival": ("Hau", "Gladion", "Selene"),
        "owner": ("Lusamine", "Guzma", "Nanu"),
    },
    "galar": {
        "mentor": ("Professor Magnolia", "Sonia", "Milo"),
        "rival": ("Hop", "Bede", "Marnie"),
        "owner": ("Leon", "Raihan", "Rose"),
    },
    "paldea": {
        "mentor": ("Professor Sada", "Professor Turo", "Jacq"),
        "rival": ("Nemona", "Arven", "Penny"),
        "owner": ("Geeta", "Clavell", "Larry"),
    },
}


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
