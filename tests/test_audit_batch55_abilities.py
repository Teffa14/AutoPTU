import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, TurnPhase


class SequenceRNG(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    def randint(self, a, b):
        if self._values:
            return self._values.pop(0)
        return b

    def choice(self, seq):
        return seq[0]


def _pokemon_spec(
    name,
    *,
    ability=None,
    abilities=None,
    types=None,
    moves=None,
    hp_stat=10,
    atk=10,
    defense=10,
    spatk=10,
    spdef=10,
    spd=10,
    level=20,
    weight=5,
):
    ability_list = abilities if abilities is not None else ([ability] if ability else [])
    return PokemonSpec(
        species=name,
        level=level,
        types=types or ["Normal"],
        hp_stat=hp_stat,
        atk=atk,
        defense=defense,
        spatk=spatk,
        spdef=spdef,
        spd=spd,
        moves=moves or [],
        abilities=[{"name": entry} for entry in ability_list],
        items=[],
        movement={"overland": 4},
        weight=weight,
        gender="",
    )


def _build_battle(attacker_spec, defender_spec, *, attacker_pos=(2, 2), defender_pos=(2, 3)):
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="foes")
    attacker = PokemonState(
        spec=attacker_spec,
        controller_id=trainer_a.identifier,
        position=attacker_pos,
        active=True,
    )
    defender = PokemonState(
        spec=defender_spec,
        controller_id=trainer_b.identifier,
        position=defender_pos,
        active=True,
    )
    battle = BattleState(
        trainers={trainer_a.identifier: trainer_a, trainer_b.identifier: trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=10, height=10),
    )
    battle.rng = SequenceRNG([19] * 200)
    return battle, "a-1", "b-1"


class AuditBatch55AbilityTests(unittest.TestCase):
    def test_magma_armor_errata_melee_tick(self):
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[tackle])
        defender_spec = _pokemon_spec("Armor", abilities=["Magma Armor [Errata]"], moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, tackle, defender_id, battle.pokemon[defender_id].position)
        self.assertLess(attacker.hp, before)

    def test_magma_armor_errata_grapple_tick(self):
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Grappler", moves=[tackle])
        defender_spec = _pokemon_spec("Armor", abilities=["Magma Armor [Errata]"], moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle._set_grapple_link(attacker_id, defender_id, dominant_id=attacker_id)
        attacker = battle.pokemon[attacker_id]
        before = attacker.hp
        events = attacker._handle_status_phase_effects(battle, TurnPhase.END, attacker_id)
        self.assertLess(attacker.hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Magma Armor [Errata]"
                and event.get("effect") == "grapple_tick"
                for event in events
            )
        )

    def test_magnet_pull_errata_forces_movement_and_restricts(self):
        magnet_pull = MoveSpec(
            name="Magnet Pull [Errata]",
            type="Steel",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Magnet", abilities=["Magnet Pull [Errata]"], moves=[magnet_pull])
        defender_spec = _pokemon_spec("Steel", moves=[magnet_pull], types=["Steel"], weight=5)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec, defender_pos=(2, 4))
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        attacker.add_temporary_effect(
            "magnet_pull_errata_choice",
            effects=["move", "max_range"],
            direction="pull",
        )
        battle.resolve_move_targets(attacker_id, magnet_pull, defender_id, defender.position)
        self.assertEqual(defender.position, (2, 3))
        entries = defender.get_temporary_effects("magnet_pull")
        self.assertTrue(entries)
        entry = entries[0]
        self.assertEqual(entry.get("max_range"), 6)

    def test_memory_wipe_errata_swift_disables_last_move(self):
        memory_wipe = MoveSpec(
            name="Memory Wipe [Errata]",
            type="Psychic",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_text="Range 10, 1 Target",
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Wiper", abilities=["Memory Wipe [Errata]"], moves=[memory_wipe, tackle])
        defender_spec = _pokemon_spec("Target", moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.add_temporary_effect("last_move", name="Tackle", round=battle.round)
        battle.resolve_move_targets(attacker_id, memory_wipe, defender_id, defender.position)
        disabled = [s for s in defender.statuses if defender._normalized_status_name(s) == "disabled"]
        self.assertTrue(disabled)
        self.assertEqual(disabled[0].get("move"), "Tackle")

    def test_memory_wipe_errata_standard_flinch_paralyze(self):
        memory_wipe = MoveSpec(
            name="Memory Wipe [Errata]",
            type="Psychic",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_text="Range 10, 1 Target",
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Wiper", abilities=["Memory Wipe [Errata]"], moves=[memory_wipe, tackle])
        defender_spec = _pokemon_spec("Target", moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.add_temporary_effect(
            "action_override",
            action="standard",
            move="Memory Wipe [Errata]",
        )
        battle.resolve_move_targets(attacker_id, memory_wipe, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.has_status("Flinched"))
        self.assertTrue(defender.has_status("Paralyzed"))

    def test_migraine_errata_confusion_crit_limited(self):
        confusion = MoveSpec(
            name="Confusion",
            type="Psychic",
            category="Special",
            db=5,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
            effects_text="No effect.",
        )
        attacker_spec = _pokemon_spec("Migraine", abilities=["Migraine [Errata]"], moves=[confusion])
        defender_spec = _pokemon_spec("Target", moves=[confusion])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        attacker.hp = attacker.max_hp() // 2
        battle.rng = SequenceRNG([19] * 200)

        for idx in range(3):
            battle.resolve_move_targets(attacker_id, confusion, defender_id, defender.position)
            move_events = [
                event
                for event in battle.log
                if event.get("type") == "move" and event.get("move") == "Confusion"
            ]
            self.assertTrue(move_events)
            last_event = move_events[-1]
            if idx < 2:
                self.assertTrue(last_event.get("crit"))
                self.assertTrue(defender.has_status("Confused"))
            else:
                self.assertFalse(last_event.get("crit"))
                self.assertFalse(defender.has_status("Confused"))
            defender.statuses = []

    def test_moody_errata_adjusts_stats(self):
        spec = _pokemon_spec("Moody", abilities=["Moody [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.rng = SequenceRNG([1, 6])
        events = mon._handle_ability_phase_effects(battle, TurnPhase.END, "a-1")
        self.assertEqual(mon.combat_stages.get("atk"), 2)
        self.assertEqual(mon.combat_stages.get("accuracy"), -1)
        self.assertTrue(
            any(
                event.get("type") == "combat_stage"
                and event.get("effect") == "moody_errata_up"
                for event in events
            )
        )

    def test_normalize_errata_forces_neutral_damage(self):
        flame = MoveSpec(
            name="Flame Burst",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Normalizer", abilities=["Normalize [Errata]"], moves=[flame])
        defender_spec = _pokemon_spec("Grass", moves=[flame], types=["Grass"], hp_stat=15)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, flame, defender_id, battle.pokemon[defender_id].position)
        move_event = next(
            event for event in reversed(battle.log) if event.get("type") == "move" and event.get("move") == "Flame Burst"
        )
        self.assertEqual(move_event.get("type_multiplier"), 1.0)

        attacker_spec = _pokemon_spec("Attacker", moves=[flame])
        defender_spec = _pokemon_spec("Shield", abilities=["Normalize [Errata]"], moves=[flame], types=["Grass"], hp_stat=15)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, flame, defender_id, battle.pokemon[defender_id].position)
        move_event = next(
            event for event in reversed(battle.log) if event.get("type") == "move" and event.get("move") == "Flame Burst"
        )
        self.assertEqual(move_event.get("type_multiplier"), 1.0)

        normal = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[normal])
        defender_spec = _pokemon_spec(
            "Ghost",
            abilities=["Normalize [Errata]"],
            moves=[normal],
            types=["Ghost"],
            hp_stat=15,
        )
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, normal, defender_id, battle.pokemon[defender_id].position)
        move_event = next(
            event for event in reversed(battle.log) if event.get("type") == "move" and event.get("move") == "Tackle"
        )
        self.assertEqual(move_event.get("type_multiplier"), 0.0)


if __name__ == "__main__":
    unittest.main()
