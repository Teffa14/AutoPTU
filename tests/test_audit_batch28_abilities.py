import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules.hooks import move_specials


class SequenceRNG(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    def randint(self, a, b):
        if self._values:
            return self._values.pop(0)
        return b


def _pokemon_spec(
    name,
    *,
    ability=None,
    types=None,
    moves=None,
    hp_stat=10,
    atk=12,
    defense=10,
    spatk=12,
    spdef=10,
    spd=10,
):
    abilities = [{"name": ability}] if ability else []
    return PokemonSpec(
        species=name,
        level=20,
        types=types or ["Normal"],
        hp_stat=hp_stat,
        atk=atk,
        defense=defense,
        spatk=spatk,
        spdef=spdef,
        spd=spd,
        moves=moves or [],
        abilities=abilities,
        movement={"overland": 4},
    )


def _build_battle(attacker_spec, defender_spec, *, grid=True):
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="foes")
    attacker = PokemonState(
        spec=attacker_spec,
        controller_id="a",
        position=(2, 2),
        active=True,
    )
    defender = PokemonState(
        spec=defender_spec,
        controller_id="b",
        position=(2, 3),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=10, height=10) if grid else None,
    )
    battle.rng = SequenceRNG([20] * 200)
    battle.round = 1
    return battle, "a-1", "b-1"


class AuditBatch28AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_disguise_blocks_first_hit(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Mimikyu", ability="Disguise", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertEqual(defender.hp, before)
        self.assertTrue(defender.get_temporary_effects("disguise_used"))
        self.assertEqual(defender.combat_stages.get("def"), 1)

    def test_download_adds_damage_bonus_against_weaker_defense(self):
        download = MoveSpec(
            name="Download",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        beam = MoveSpec(
            name="Psybeam",
            type="Psychic",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Porygon", ability="Download", moves=[download, beam])
        defender_spec = _pokemon_spec("Target", moves=[beam], defense=12, spdef=6)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] * 50)
        battle.resolve_move_targets(attacker_id, download, defender_id, battle.pokemon[defender_id].position)
        battle.resolve_move_targets(attacker_id, beam, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Download"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_dream_smoke_puts_attacker_to_sleep(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Dreamy", ability="Dream Smoke", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[attacker_id].has_status("Sleep"))

    def test_dreamspinner_heals_per_sleeping_foe(self):
        move = MoveSpec(
            name="Dreamspinner",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Spinner", ability="Dreamspinner", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        sleeper1 = PokemonState(
            spec=_pokemon_spec("Sleepy1", moves=[move]),
            controller_id="b",
            position=(2, 6),
            active=True,
        )
        sleeper2 = PokemonState(
            spec=_pokemon_spec("Sleepy2", moves=[move]),
            controller_id="b",
            position=(6, 2),
            active=True,
        )
        sleeper1.statuses.append({"name": "Sleep"})
        sleeper2.statuses.append({"name": "Sleep"})
        battle.pokemon["b-2"] = sleeper1
        battle.pokemon["b-3"] = sleeper2
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.hp - 2 * attacker.tick_value())
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, attacker_id, attacker.position)
        self.assertEqual(attacker.hp - before, 2 * attacker.tick_value())

    def test_drizzle_sets_rain(self):
        move = MoveSpec(
            name="Drizzle",
            type="Water",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Politoed", ability="Drizzle", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.weather, "Rain")

    def test_drought_sets_sun(self):
        move = MoveSpec(
            name="Drought",
            type="Fire",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Torkoal", ability="Drought", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.weather, "Sunny")

    def test_drown_out_blocks_sonic_move(self):
        move = MoveSpec(
            name="Sonic Boom",
            type="Normal",
            category="Special",
            db=5,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
            keywords=["Sonic"],
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Drowner", ability="Drown Out", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertEqual(defender.hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Drown Out"
                and event.get("effect") == "block_sonic"
                for event in battle.log
            )
        )

    def test_dust_cloud_expands_powder_move(self):
        move = MoveSpec(
            name="Sleep Powder",
            type="Grass",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
            effects_text="The target falls Asleep on 16+.",
        )
        attacker_spec = _pokemon_spec("Dusty", ability="Dust Cloud", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].position = (2, 3)
        extra = PokemonState(
            spec=_pokemon_spec("Extra", moves=[move]),
            controller_id="b",
            position=(3, 2),
            active=True,
        )
        battle.pokemon["b-2"] = extra
        battle.rng = SequenceRNG([20] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Sleep"))
        self.assertTrue(extra.has_status("Sleep"))

    def test_early_bird_grants_save_bonus(self):
        spec = _pokemon_spec("Bird", ability="Early Bird")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        self.assertEqual(mon.save_bonus(battle), 3)

    def test_eggscellence_boosts_effectiveness_on_high_roll(self):
        move = MoveSpec(
            name="Egg Bomb",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Chansey", ability="Eggscellence", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([16] + [1] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Eggscellence"
                and event.get("effect") == "type_boost"
                for event in battle.log
            )
        )
