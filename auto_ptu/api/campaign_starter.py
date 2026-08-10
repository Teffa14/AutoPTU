"""Deterministic, full-journey starter campaign content.

The blueprint is data-only. CampaignService sends every entry through the
normal command boundary so creation produces the same audit trail as play.
"""

from __future__ import annotations

from typing import Any, Dict


_POINT_DETAILS: Dict[str, Dict[str, Any]] = {
    "lab-starter-pods": {
        "interaction": "Meet the starters",
        "description": "Five habitat pods stand open. Each young Pokemon watches the Trainers and chooses whether to come closer.",
        "result": "The starter candidates answer in their own ways: curiosity, caution, courage, play, and bright-eyed trust. The starter roster is ready for a mutual choice.",
    },
    "lab-alder-desk": {
        "interaction": "Review Alder's research",
        "description": "Alder's desk holds field maps, starter care notes, and a Prism League passport printer.",
        "result": "The field notes mark unusual prism activity in Glasswood and a safe first route through Sunpath. Alder has already prepared the party's League passports.",
        "once": True,
    },
    "lab-sealed-drawer": {
        "interaction": "Open the archive",
        "description": "A violet League seal locks this old archive drawer. Its prism pattern predates the current badge circuit.",
        "result": "Inside is a copied covenant clause: the Champion's prism answers to freely chosen bonds, not League rank. Someone has crossed out Ilyra's signature.",
        "failure_result": "The seal flashes and refuses the attempt, but its resonance matches the old Glasswood crystals.",
        "available": False,
        "once": True,
        "check": {"label": "Technology Education", "expression": "3d6+1", "difficulty": 12},
    },
    "sunpath-sign": {
        "interaction": "Read the route marker",
        "description": "A weathered League marker records trail etiquette, ranger signals, and the distance to Brookfall.",
        "result": "A fresh challenge ribbon tied beneath the sign bears Cassian Vale's crest. He expects the party farther along Sunpath.",
    },
    "sunpath-prism-tracks": {
        "interaction": "Study the tracks",
        "description": "Clawed tracks glitter as though powdered glass has fused to the soil.",
        "result": "The tracks belong to no local species. Boot prints follow them toward Glasswood, carrying the angular tread used by Team Cinder.",
        "failure_result": "Wind smears the trail, leaving only the certainty that Pokemon and people passed here together.",
        "once": True,
        "check": {"label": "Survival", "expression": "3d6+1", "difficulty": 11},
    },
    "brookfall-center": {
        "interaction": "Visit the Pokemon Center",
        "description": "A canal-side Pokemon Center offers treatment, warm food, and dry towels to travelling teams.",
        "result": "The Center staff welcome the party. Recovery actions are available from the location controls.",
    },
    "brookfall-gym": {
        "interaction": "Enter Brookfall Gym",
        "description": "Glass bridges shift above a deep practice pool while Leader Maris watches every approach.",
        "result": "Maris opens the arena and asks one question: who will the team protect when victory and safety pull in different directions?",
    },
    "ember-cooperative": {
        "interaction": "Browse the cooperative",
        "description": "Local trainers and artisans share a lantern-lit counter packed with route supplies.",
        "result": "The cooperative opens its stock to the party. Available purchases appear in the location controls.",
    },
    "ember-workbench": {
        "interaction": "Use the workbench",
        "description": "Apricorn tools, presses, and drying racks make this a safe place for careful field crafting.",
        "result": "The bench is prepared. Any recipe the party knows can now be crafted from the location controls.",
    },
    "ember-whisper": {
        "interaction": "Listen unnoticed",
        "description": "Two hooded buyers trade clipped phrases behind a curtain of spice smoke.",
        "result": "The buyers name a Copperline lookout and say the stolen medicine is payment for a living Glasswood crystal.",
        "failure_result": "The exchange ends as one buyer notices movement, leaving only the word 'Copperline.'",
        "once": True,
        "check": {"label": "Stealth", "expression": "3d6", "difficulty": 10},
    },
    "copper-cart": {
        "interaction": "Inspect the stranded cart",
        "description": "A maintenance cart hangs crooked across the rail bridge, its brake cable burned through.",
        "result": "The cart can be made safe with teamwork. Its cargo manifest proves Team Cinder diverted medical supplies toward Glasswood.",
        "once": True,
    },
    "copper-cinder": {
        "interaction": "Confront the lookout",
        "description": "A Team Cinder lookout signals toward the storm ridge, unaware the party has closed in.",
        "result": "The lookout drops a coded route slate linking Copperline operations to a League contact at Moonmere.",
        "failure_result": "The lookout escapes into the storm but drops a slate bearing Moonmere tide coordinates.",
        "once": True,
        "check": {"label": "Command", "expression": "3d6+1", "difficulty": 11},
    },
    "voltspire-lift": {
        "interaction": "Ride the skyline lift",
        "description": "An open lift climbs through humming turbines and gives a clear view of Voltspire's layered streets.",
        "result": "The lift conductor points out the Gym circuit and warns that today's storm has made every conduit unpredictable.",
    },
    "voltspire-gym": {
        "interaction": "Enter Voltspire Gym",
        "description": "A modular electric arena rewires itself around every moving combatant.",
        "result": "Leader Kael powers the arena and invites the party to solve the circuit with movement, timing, and trust.",
    },
    "moonmere-archive": {
        "interaction": "Read the covenant archive",
        "description": "Tide-proof cases preserve testimony from Pokemon, Rangers, and the founders of the Prism League.",
        "result": "The original covenant confirms that Pokemon consent—not victory alone—legitimizes the Champion's prism. The modern League omitted that promise.",
        "once": True,
        "complete_objectives": ["Learn the Moonmere covenant"],
    },
    "moonmere-gym": {
        "interaction": "Enter Moonmere Gym",
        "description": "Moonlit water rises and falls across an arena built into the ruins.",
        "result": "Leader Neris opens the final Gym trial and asks the challenger to defend the truth they intend to carry to the League.",
    },
    "moonmere-tablet": {
        "interaction": "Raise the tablet",
        "description": "A carved stone tablet flickers beneath the shallow tide, too heavy to read without exposing it.",
        "result": "The tablet records Pokemon as equal witnesses to the covenant and bears the same living prism pattern found in Glasswood.",
        "failure_result": "The current wins this attempt, but a traced symbol reveals Pokemon pawprints beside every founder's name.",
        "once": True,
        "check": {"label": "Athletics", "expression": "4d6", "difficulty": 13},
        "complete_objectives": ["Learn the Moonmere covenant"],
    },
    "league-gate": {
        "interaction": "Register at the badge gate",
        "description": "The Prism badge gate reads a team's League record before opening the tournament road.",
        "result": "The gate recognizes the party's earned badges and records every Pokemon partner as a named member of the League team.",
    },
    "league-arena": {
        "interaction": "Enter the Champion arena",
        "description": "A many-colored arena waits above the plateau, surrounded by every route the party travelled.",
        "result": "The arena answers the team's approach with the colors of their bonds. The League challenge is ready when the active chapter permits it.",
    },
    "glasswood-camp": {
        "interaction": "Check the ranger camp",
        "description": "A hastily abandoned ranger camp contains empty medicine cases and a map pinned beneath a lantern.",
        "result": "The map shows a rescue route through the singing trees and circles the place where a wild Pokemon's voice disappeared.",
    },
    "glasswood-echo": {
        "interaction": "Listen to the stolen voice",
        "description": "A crystal tree repeats a frightened Pokemon's cry in a voice that does not belong to it.",
        "result": "Patient listening releases the trapped voice. It names Team Cinder, remembers kindness from Cassian, and reveals a path to the missing medicine.",
        "failure_result": "The echo fractures into directions and colors; enough remains to point toward the stolen medicine.",
        "once": True,
        "check": {"label": "Pokemon Education", "expression": "3d6+1", "difficulty": 11},
        "complete_objectives": ["Investigate Glasswood"],
    },
}

for _discoverable_point_id in (
    "sunpath-prism-tracks",
    "ember-whisper",
    "copper-cinder",
    "moonmere-tablet",
    "glasswood-echo",
):
    _POINT_DETAILS[_discoverable_point_id]["discoverable"] = True


def _exploration(
    theme: str,
    *,
    spawn: tuple[int, int] = (1, 3),
    blocked: tuple[tuple[int, int], ...] = (),
    terrain: tuple[tuple[int, int, str], ...] = (),
    points: tuple[tuple[str, str, str, int, int, bool], ...] = (),
) -> Dict[str, Any]:
    """Build one stable scene floor without consuming runtime RNG."""
    return {
        "width": 10,
        "height": 7,
        "theme": theme,
        "spawn": list(spawn),
        "blocked": [list(value) for value in blocked],
        "terrain": [{"x": x, "y": y, "kind": kind} for x, y, kind in terrain],
        "points": [
            {
                "id": point_id,
                "label": label,
                "kind": kind,
                "x": x,
                "y": y,
                "revealed": revealed,
                **_POINT_DETAILS.get(point_id, {}),
            }
            for point_id, label, kind, x, y, revealed in points
        ],
    }


def _pokemon(
    actor_id: str,
    name: str,
    species: str,
    level: int,
    location_id: str,
    *,
    owner: str = "",
    controller: str = "ai",
    battle_group: str = "",
    starter_candidate: bool = False,
) -> Dict[str, Any]:
    return {
        "id": actor_id,
        "name": name,
        "kind": "pokemon",
        "species": species,
        "level": level,
        "owner_participant_id": owner,
        "controller": controller,
        "location_id": location_id,
        "persona": f"A distinct {species} partner whose choices reflect its bond, instincts, and lived experience.",
        "sheet": {
            "battle_group": battle_group,
            "starter_candidate": starter_candidate,
            "current_hp": 1,
            "max_hp": 1,
            "conditions": [],
        },
    }


def build_starter_blueprint(gm_name: str, *, player_owner_id: str = "gm") -> Dict[str, Any]:
    locations = [
        {"id": "lumenfall-lab", "name": "Professor Alder's Lab", "kind": "town", "neighbors": ["sunpath-route"], "danger": 0, "travel_hours": 0, "map_x": 10, "map_y": 55, "services": ["healing", "starter_selection", "research"], "description": "A bright glass laboratory overlooking Lumenfall's prism canals."},
        {"id": "sunpath-route", "name": "Sunpath Route", "kind": "route", "neighbors": ["lumenfall-lab", "brookfall-city", "glasswood-crossing"], "danger": 2, "travel_hours": 4, "map_x": 27, "map_y": 49, "services": ["forage"], "description": "Warm grasslands where new Trainers traditionally meet their first rivals."},
        {"id": "brookfall-city", "name": "Brookfall City", "kind": "gym_city", "neighbors": ["sunpath-route", "embermarket"], "danger": 0, "travel_hours": 3, "map_x": 43, "map_y": 25, "services": ["healing", "shop", "gym"], "description": "A canal city whose gym teaches positioning and patience."},
        {"id": "embermarket", "name": "Embermarket", "kind": "town", "neighbors": ["brookfall-city", "copperline-route"], "danger": 1, "travel_hours": 3, "map_x": 58, "map_y": 32, "services": ["shop", "crafting", "downtime"], "description": "An evening bazaar of Apricorn artisans, cooks, and travelling battlers."},
        {"id": "copperline-route", "name": "Copperline Route", "kind": "route", "neighbors": ["embermarket", "voltspire-city", "glasswood-crossing"], "danger": 4, "travel_hours": 6, "map_x": 68, "map_y": 56, "services": ["camp", "forage"], "description": "Old rail bridges cross storm valleys full of Electric Pokémon."},
        {"id": "voltspire-city", "name": "Voltspire City", "kind": "gym_city", "neighbors": ["copperline-route", "moonmere"], "danger": 0, "travel_hours": 3, "map_x": 78, "map_y": 31, "services": ["healing", "shop", "gym"], "description": "A vertical city powered by wind turbines and ambitious inventors."},
        {"id": "moonmere", "name": "Moonmere Coast", "kind": "gym_city", "neighbors": ["voltspire-city", "league-road"], "danger": 3, "travel_hours": 7, "map_x": 88, "map_y": 49, "services": ["healing", "gym", "research"], "description": "Tidal ruins conceal the region's oldest League covenant."},
        {"id": "league-road", "name": "Prism League Plateau", "kind": "league", "neighbors": ["moonmere"], "danger": 5, "travel_hours": 8, "map_x": 93, "map_y": 16, "services": ["healing", "shop", "league"], "description": "The badge gates, tournament halls, and Champion's prism arena."},
        {"id": "glasswood-crossing", "name": "Glasswood Crossing", "kind": "wilds", "neighbors": ["sunpath-route", "copperline-route"], "danger": 5, "travel_hours": 5, "map_x": 46, "map_y": 70, "services": ["camp", "forage"], "description": "Crystal trees sing before storms and preserve voices in their bark."},
    ]
    exploration_by_location = {
        "lumenfall-lab": _exploration("laboratory", blocked=((0, 0), (0, 1), (9, 0), (9, 1), (4, 0), (5, 0)), terrain=((3, 2, "glass"), (4, 2, "glass"), (5, 2, "glass"), (6, 2, "glass")), points=(("lab-starter-pods", "Starter habitat pods", "story", 4, 2, True), ("lab-alder-desk", "Professor Alder's research desk", "npc", 7, 3, True), ("lab-sealed-drawer", "Sealed prism archive", "secret", 8, 1, False))),
        "sunpath-route": _exploration("sunlit-grass", blocked=((3, 0), (3, 1), (6, 5), (6, 6)), terrain=((2, 2, "tall-grass"), (3, 2, "tall-grass"), (6, 3, "trail"), (7, 3, "trail")), points=(("sunpath-sign", "League route marker", "route", 2, 3, True), ("sunpath-prism-tracks", "Unfamiliar prism tracks", "clue", 7, 5, False))),
        "brookfall-city": _exploration("canal-city", blocked=((4, 0), (4, 1), (4, 2), (4, 4), (4, 5), (4, 6)), terrain=((4, 3, "bridge"), (7, 1, "water"), (7, 2, "water")), points=(("brookfall-center", "Brookfall Pokemon Center", "healing", 2, 1, True), ("brookfall-gym", "Brookfall Gym", "gym", 8, 3, True))),
        "embermarket": _exploration("night-market", blocked=((2, 1), (5, 1), (8, 1), (2, 5), (5, 5), (8, 5)), terrain=((3, 3, "lantern"), (5, 3, "lantern"), (7, 3, "lantern")), points=(("ember-cooperative", "Embermarket Cooperative", "shop", 5, 2, True), ("ember-workbench", "Apricorn workbench", "crafting", 7, 4, True), ("ember-whisper", "A whispered Cinder exchange", "secret", 9, 5, False))),
        "copperline-route": _exploration("storm-rail", blocked=((3, 1), (3, 2), (3, 4), (3, 5), (8, 0), (8, 6)), terrain=((3, 3, "rail-bridge"), (6, 2, "charged"), (6, 4, "charged")), points=(("copper-cart", "Stranded rail cart", "story", 6, 3, True), ("copper-cinder", "Team Cinder lookout", "danger", 8, 2, False))),
        "voltspire-city": _exploration("electric-city", blocked=((2, 0), (2, 1), (5, 5), (5, 6), (8, 0), (8, 1)), terrain=((4, 2, "conduit"), (5, 2, "conduit"), (6, 2, "conduit")), points=(("voltspire-lift", "Skyline lift", "route", 3, 3, True), ("voltspire-gym", "Voltspire Gym", "gym", 8, 3, True))),
        "moonmere": _exploration("tidal-ruins", blocked=((4, 0), (4, 1), (4, 5), (4, 6), (7, 2), (7, 4)), terrain=((4, 2, "shallow-water"), (4, 3, "shallow-water"), (4, 4, "shallow-water")), points=(("moonmere-archive", "Covenant archive", "story", 6, 1, True), ("moonmere-gym", "Moonmere Gym", "gym", 8, 5, True), ("moonmere-tablet", "Submerged covenant tablet", "secret", 6, 5, False))),
        "league-road": _exploration("league-plateau", blocked=((3, 0), (3, 1), (6, 0), (6, 1), (3, 5), (3, 6), (6, 5), (6, 6)), terrain=((4, 3, "prism"), (5, 3, "prism")), points=(("league-gate", "Prism badge gate", "league", 3, 3, True), ("league-arena", "Champion arena", "league", 8, 3, True))),
        "glasswood-crossing": _exploration("crystal-forest", blocked=((3, 1), (3, 2), (6, 0), (6, 1), (7, 5), (7, 6)), terrain=((4, 3, "crystal"), (5, 2, "crystal"), (6, 4, "crystal")), points=(("glasswood-camp", "Ranger camp", "camp", 2, 4, True), ("glasswood-echo", "Tree holding a stolen voice", "clue", 7, 3, False))),
    }
    for location in locations:
        location["exploration"] = exploration_by_location[location["id"]]

    scenes = [
        {"id": "scene-starter-day", "order": 1, "title": "Choose Your Partner", "kind": "roleplay", "location": "Professor Alder's Lab", "summary": "Meet Professor Alder, choose a starter, learn what kind of Trainer you want to become, and receive a League passport.", "activate": True, "metadata": {"location_id": "lumenfall-lab", "chapter": "Beginnings", "npc_actor_ids": ["npc-alder"]}},
        {"id": "scene-first-rival", "order": 2, "title": "Cassian's First Challenge", "kind": "combat", "location": "Sunpath Route", "summary": "Rival Cassian Vale challenges the new team—not out of cruelty, but to decide whether you are serious about the League.", "metadata": {"location_id": "sunpath-route", "opponent_actor_ids": ["pokemon-riolu"], "rival_id": "npc-cassian"}},
        {"id": "scene-glasswood-voices", "order": 3, "title": "Voices in Glasswood", "kind": "exploration", "location": "Glasswood Crossing", "summary": "Track stolen medicine through crystal trees, negotiate with wild Pokémon, and uncover Team Cinder's interest in the Champion prism.", "metadata": {"location_id": "glasswood-crossing", "complete_objectives_on_exit": ["Investigate Glasswood"]}},
        {"id": "scene-brookfall-gym", "order": 4, "title": "Brookfall Gym", "kind": "combat", "location": "Brookfall City", "summary": "Leader Maris tests movement, protection, and restraint in a shifting water arena.", "metadata": {"location_id": "brookfall-city", "opponent_actor_ids": ["pokemon-shellos", "pokemon-wooper"], "badge": "Cascade Glass Badge", "leader_id": "npc-maris"}},
        {"id": "scene-embermarket", "order": 5, "title": "An Evening in Embermarket", "kind": "downtime", "location": "Embermarket", "summary": "Shop for supplies, craft medicine, train, recover, and learn what your companions want beyond the League.", "metadata": {"location_id": "embermarket"}},
        {"id": "scene-copperline", "order": 6, "title": "The Broken Copperline", "kind": "travel", "location": "Copperline Route", "summary": "Cross the storm valley, repair a stranded rail cart, and decide whether to help Cassian when Team Cinder corners him.", "metadata": {"location_id": "copperline-route"}},
        {"id": "scene-voltspire-gym", "order": 7, "title": "Voltspire Gym", "kind": "combat", "location": "Voltspire City", "summary": "Inventor Kael turns the arena into a circuit puzzle where every action changes the field.", "metadata": {"location_id": "voltspire-city", "opponent_actor_ids": ["pokemon-magnemite", "pokemon-pikachu"], "badge": "Dynamo Prism Badge", "leader_id": "npc-kael"}},
        {"id": "scene-moonmere-truth", "order": 8, "title": "The Moonmere Covenant", "kind": "roleplay", "location": "Moonmere Coast", "summary": "Question the League archivist, confront Champion Ilyra's hidden bargain, and decide which truth to reveal publicly.", "metadata": {"location_id": "moonmere", "npc_actor_ids": ["npc-neris", "npc-ilyra"], "complete_objectives_on_npc_reply": {"npc-neris": ["Learn the Moonmere covenant"], "npc-ilyra": ["Learn the Moonmere covenant"]}}},
        {"id": "scene-moonmere-gym", "order": 9, "title": "Moonmere Gym", "kind": "combat", "location": "Moonmere Coast", "summary": "Leader Neris tests adaptability in moonlit tides before granting the final circuit badge.", "metadata": {"location_id": "moonmere", "opponent_actor_ids": ["pokemon-horsea", "pokemon-frillish"], "badge": "Tidal Moon Badge", "leader_id": "npc-neris"}},
        {"id": "scene-badge-gate", "order": 10, "title": "The Badge Gate", "kind": "roleplay", "location": "Prism League Plateau", "summary": "Register the team, speak with defeated rivals and Gym Leaders, and declare what your League run stands for.", "metadata": {"location_id": "league-road", "npc_actor_ids": ["npc-cassian", "npc-maris", "npc-kael", "npc-neris", "npc-orin", "npc-ilyra"], "complete_objectives_on_exit": ["Decide what to reveal at the Badge Gate"]}},
        {"id": "scene-league-qualifier", "order": 11, "title": "League Qualifier", "kind": "combat", "location": "Prism League Plateau", "summary": "Face veteran Ranger Orin in an official full-contact qualifier.", "metadata": {"location_id": "league-road", "opponent_actor_ids": ["pokemon-noctowl", "pokemon-luxio"], "league_rank": "Top 16", "leader_id": "npc-orin"}},
        {"id": "scene-league-rival", "order": 12, "title": "League Semifinal: Cassian", "kind": "combat", "location": "Prism League Plateau", "summary": "Cassian returns with a stronger partner and a fully realized philosophy. Only one rival reaches the Champion.", "metadata": {"location_id": "league-road", "opponent_actor_ids": ["pokemon-lucario", "pokemon-corvisquire"], "league_rank": "Finalist", "rival_id": "npc-cassian"}},
        {"id": "scene-champion", "order": 13, "title": "The Champion's Prism", "kind": "combat", "location": "Prism League Plateau", "summary": "Champion Ilyra battles without holding back while the prism reacts to every bond formed on the journey.", "metadata": {"location_id": "league-road", "opponent_actor_ids": ["pokemon-absol", "pokemon-gardevoir", "pokemon-altaria"], "league_rank": "Champion", "leader_id": "npc-ilyra"}},
        {"id": "scene-champion-dawn", "order": 14, "title": "Champion's Dawn", "kind": "downtime", "location": "Prism League Plateau", "summary": "Celebrate, settle every companion and rival relationship, choose the region's next promise, and record the team that changed the League.", "metadata": {"location_id": "league-road", "chapter": "Legacy", "npc_actor_ids": ["npc-cassian", "npc-maris", "npc-kael", "npc-neris", "npc-orin", "npc-ilyra"]}},
    ]
    completion_gates = {
        "scene-starter-day": [{"kind": "starter", "label": "Choose a starter partner"}],
        "scene-first-rival": [{"kind": "battle", "label": "Win Cassian's challenge"}],
        "scene-glasswood-voices": [{"kind": "point", "point_id": "glasswood-echo", "label": "Find and free the stolen voice"}],
        "scene-brookfall-gym": [{"kind": "battle", "label": "Earn the Cascade Glass Badge"}],
        "scene-embermarket": [{"kind": "activity", "event_type": "downtime.activity", "label": "Complete a downtime activity"}],
        "scene-copperline": [{"kind": "point", "point_id": "copper-cart", "label": "Inspect and secure the stranded rail cart"}],
        "scene-voltspire-gym": [{"kind": "battle", "label": "Earn the Dynamo Prism Badge"}],
        "scene-moonmere-truth": [{"kind": "point", "point_id": "moonmere-archive", "label": "Read the original covenant"}],
        "scene-moonmere-gym": [{"kind": "battle", "label": "Earn the Tidal Moon Badge"}],
        "scene-badge-gate": [{"kind": "point", "point_id": "league-gate", "label": "Register the team at the badge gate"}],
        "scene-league-qualifier": [{"kind": "battle", "label": "Win the League qualifier"}],
        "scene-league-rival": [{"kind": "battle", "label": "Defeat Cassian in the semifinal"}],
        "scene-champion": [{"kind": "battle", "label": "Defeat Champion Ilyra"}],
    }
    for scene in scenes:
        scene["metadata"]["completion_gate"] = list(completion_gates.get(scene["id"], []))

    actors = [
        {"id": "trainer-player", "name": gm_name, "kind": "trainer", "owner_participant_id": player_owner_id, "controller": "human", "level": 1, "location_id": "lumenfall-lab", "currency": 3000, "inventory": {"Apricorn": 3, "Herb": 3, "Potion": 2, "Poke Ball": 5}, "persona": "A new Trainer whose principles emerge through the player's decisions.", "goals": ["Choose a partner", "Earn three badges", "Challenge the Prism League"], "sheet": {"max_hp": 50, "current_hp": 50, "conditions": [], "trainer_classes": []}},
        {"id": "trainer-nova", "name": "Nova Vale", "kind": "trainer", "owner_participant_id": "agent-nova", "controller": "ai", "level": 1, "location_id": "lumenfall-lab", "currency": 2200, "inventory": {"Potion": 2, "Poke Ball": 4}, "persona": "A bold Ace Trainer who protects others first and loves tactical risks.", "voice": "Energetic, direct, and quick to challenge fear.", "goals": ["Become a Gym battler", "Prove courage can be kind"]},
        {"id": "trainer-milo", "name": "Milo Reed", "kind": "trainer", "owner_participant_id": "agent-milo", "controller": "ai", "level": 1, "location_id": "lumenfall-lab", "currency": 1800, "inventory": {"Antidote": 2, "Poke Ball": 3}, "persona": "A careful Pokémon Researcher who follows evidence and respects wild habitats.", "voice": "Curious, precise, and delighted by unexpected evidence.", "goals": ["Document Glasswood", "Publish ethical field research"]},
        {"id": "trainer-sera", "name": "Sera Moss", "kind": "trainer", "owner_participant_id": "agent-sera", "controller": "ai", "level": 1, "location_id": "lumenfall-lab", "currency": 1900, "inventory": {"Bandage": 3, "Poke Ball": 3}, "persona": "An empathetic Ranger who de-escalates danger and never abandons a trail.", "voice": "Quiet, grounded, and attentive to what others avoid saying.", "goals": ["Protect route communities", "Join the Ranger Union"]},
        _pokemon("starter-bulbasaur", "Bulbasaur", "Bulbasaur", 5, "lumenfall-lab", starter_candidate=True),
        _pokemon("starter-charmander", "Charmander", "Charmander", 5, "lumenfall-lab", starter_candidate=True),
        _pokemon("starter-squirtle", "Squirtle", "Squirtle", 5, "lumenfall-lab", starter_candidate=True),
        _pokemon("starter-pikachu", "Pikachu", "Pikachu", 5, "lumenfall-lab", starter_candidate=True),
        _pokemon("starter-eevee", "Eevee", "Eevee", 5, "lumenfall-lab", starter_candidate=True),
        _pokemon("pokemon-growlithe", "Cinder", "Growlithe", 6, "lumenfall-lab", owner="agent-nova"),
        _pokemon("pokemon-shinx", "Lumen", "Shinx", 6, "lumenfall-lab", owner="agent-milo"),
        _pokemon("pokemon-chikorita", "Moss", "Chikorita", 6, "lumenfall-lab", owner="agent-sera"),
        {"id": "npc-alder", "name": "Professor Alder", "kind": "npc", "controller": "ai", "location_id": "lumenfall-lab", "persona": "The region's warm but exacting Pokémon ecology professor. Alder never chooses for a Trainer and treats starter consent as essential.", "voice": "Patient questions, precise scientific language, dry humor.", "goals": ["Match partners by temperament", "Protect Glasswood from exploitation"], "knowledge": ["Starter temperaments", "League registration", "Champion prism history"]},
        {"id": "npc-cassian", "name": "Cassian Vale", "kind": "rival", "controller": "ai", "location_id": "sunpath-route", "persona": "A disciplined rival who believes strength creates responsibility. Competitive, never pointlessly cruel, and capable of changing his mind when shown evidence.", "voice": "Controlled confidence, clipped challenges, rare sincere praise.", "goals": ["Become Champion", "Reform weak League protections"], "knowledge": ["Rival battle strategy", "Team Cinder recruiting", "League politics"]},
        {"id": "npc-maris", "name": "Leader Maris", "kind": "gym_leader", "controller": "ai", "location_id": "brookfall-city", "persona": "A rescue diver and Gym Leader who rewards protection, positioning, and mercy more than raw damage.", "voice": "Calm instructions with nautical metaphors.", "goals": ["Train responsible battlers", "Keep Brookfall canals safe"], "knowledge": ["Brookfall Gym puzzle", "Team Cinder canal routes"]},
        {"id": "npc-kael", "name": "Leader Kael", "kind": "gym_leader", "controller": "ai", "location_id": "voltspire-city", "persona": "An inventor who treats battles as collaborative engineering problems and admits mistakes openly.", "voice": "Fast, technical, enthusiastic, never condescending.", "goals": ["Build resilient power grids", "Find creative challengers"], "knowledge": ["Voltspire circuit arena", "Prism energy signatures"]},
        {"id": "npc-neris", "name": "Leader Neris", "kind": "gym_leader", "controller": "ai", "location_id": "moonmere", "persona": "A historian and tide-reader who tests adaptability and asks challengers to defend their public choices.", "voice": "Measured, ceremonial, incisive.", "goals": ["Preserve the Moonmere covenant", "Expose dishonest League history"], "knowledge": ["Moonmere covenant", "Champion Ilyra's bargain", "Final badge trial"]},
        {"id": "npc-orin", "name": "Ranger Orin", "kind": "league", "controller": "ai", "location_id": "league-road", "persona": "A veteran Ranger and League qualifier judge who battles to test preparation under pressure.", "voice": "Brief field commands and generous post-battle analysis.", "goals": ["Approve only safe League teams", "Recruit thoughtful Rangers"], "knowledge": ["League qualifier rules", "Plateau hazards"]},
        {"id": "npc-ilyra", "name": "Champion Ilyra", "kind": "champion", "controller": "ai", "location_id": "league-road", "persona": "The reigning Champion: compassionate, politically burdened, and afraid that revealing the prism covenant will destabilize the region. She fights to learn whether the challenger can carry consequences.", "voice": "Elegant, candid, and increasingly vulnerable when challenged with truth.", "goals": ["Protect the region", "Find a worthy successor", "Resolve the prism covenant"], "knowledge": ["Complete prism covenant", "League council secrets", "Champion arena"]},
        _pokemon("pokemon-riolu", "Vow", "Riolu", 6, "sunpath-route", battle_group="rival-first"),
        _pokemon("pokemon-shellos", "Ripple", "Shellos", 10, "brookfall-city", battle_group="gym-brookfall"),
        _pokemon("pokemon-wooper", "Lock", "Wooper", 10, "brookfall-city", battle_group="gym-brookfall"),
        _pokemon("pokemon-magnemite", "Relay", "Magnemite", 16, "voltspire-city", battle_group="gym-voltspire"),
        _pokemon("pokemon-pikachu", "Spark", "Pikachu", 16, "voltspire-city", battle_group="gym-voltspire"),
        _pokemon("pokemon-horsea", "Current", "Horsea", 22, "moonmere", battle_group="gym-moonmere"),
        _pokemon("pokemon-frillish", "Vesper", "Frillish", 22, "moonmere", battle_group="gym-moonmere"),
        _pokemon("pokemon-noctowl", "Watch", "Noctowl", 28, "league-road", battle_group="league-qualifier"),
        _pokemon("pokemon-luxio", "Beacon", "Luxio", 28, "league-road", battle_group="league-qualifier"),
        _pokemon("pokemon-lucario", "Vow", "Lucario", 34, "league-road", battle_group="league-rival"),
        _pokemon("pokemon-corvisquire", "Edict", "Corvisquire", 34, "league-road", battle_group="league-rival"),
        _pokemon("pokemon-absol", "Omen", "Absol", 40, "league-road", battle_group="champion"),
        _pokemon("pokemon-gardevoir", "Covenant", "Gardevoir", 40, "league-road", battle_group="champion"),
        _pokemon("pokemon-altaria", "Dawn", "Altaria", 40, "league-road", battle_group="champion"),
    ]

    return {
        "locations": locations,
        "scenes": scenes,
        "actors": actors,
        "recipes": [
            {"id": "recipe-field-poultice", "name": "Field Poultice", "ingredients": {"Herb": 2}, "output_item": "Poultice", "output_quantity": 1, "hours": 1},
            {"id": "recipe-apricorn-ball", "name": "Apricorn Ball", "ingredients": {"Apricorn": 2}, "output_item": "Poke Ball", "output_quantity": 1, "hours": 2},
        ],
        "shops": [
            {"id": "shop-brookfall", "name": "Brookfall Supply", "location_id": "brookfall-city", "stock": {"Potion": {"price": 200, "quantity": 20}, "Antidote": {"price": 100, "quantity": 12}, "Poke Ball": {"price": 250, "quantity": 30}}},
            {"id": "shop-embermarket", "name": "Embermarket Cooperative", "location_id": "embermarket", "stock": {"Herb": {"price": 40, "quantity": 30}, "Apricorn": {"price": 60, "quantity": 30}, "Bandage": {"price": 80, "quantity": 20}}},
            {"id": "shop-league", "name": "League Commissary", "location_id": "league-road", "stock": {"Super Potion": {"price": 700, "quantity": 20}, "Full Heal": {"price": 600, "quantity": 12}, "Revive": {"price": 1500, "quantity": 6}}},
        ],
        "quests": [
            {"id": "quest-badge-circuit", "name": "Complete the Prism Badge Circuit", "objectives": [{"text": "Choose a starter partner", "reveal_order": 1}, {"text": "Earn the Cascade Glass Badge", "reveal_order": 2}, {"text": "Earn the Dynamo Prism Badge", "reveal_order": 5}, {"text": "Earn the Tidal Moon Badge", "reveal_order": 8}], "reward": "Prism League qualification"},
            {"id": "quest-cinder-truth", "name": "Follow the Prism Mystery", "reveal_order": 3, "objectives": [{"text": "Investigate Glasswood", "reveal_order": 3}, {"text": "Learn the Moonmere covenant", "reveal_order": 8}, {"text": "Decide what to reveal at the Badge Gate", "reveal_order": 10}], "reward": "The trust of the region's Pokémon communities"},
            {"id": "quest-prism-league", "name": "Challenge the Prism League", "reveal_order": 10, "objectives": [{"text": "Win the League qualifier", "reveal_order": 10}, {"text": "Defeat Cassian in the semifinal", "reveal_order": 11}, {"text": "Face Champion Ilyra", "reveal_order": 12}], "reward": "The Prism Champion title"},
        ],
    }
