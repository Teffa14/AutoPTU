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
    atk=12,
    defense=10,
    spatk=12,
    spdef=10,
    spd=10,
    level=20,
    items=None,
    movement=None,
    gender="",
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
        items=items or [],
        movement=movement or {"overland": 4},
        weight=5,
        gender=gender,
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
    battle.rng = SequenceRNG([20] * 200)
    return battle, "a-1", "b-1"


class AuditBatch49AbilityTests(unittest.TestCase):
    def test_abominable_errata_increases_max_hp_and_blocks_recoil(self):
        recoil_move = MoveSpec(
            name="Take Down",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            effects_text="Recoil 1/3",
        )
        base_spec = _pokemon_spec("Base", moves=[recoil_move])
        errata_spec = _pokemon_spec("Abom", abilities=["Abominable [Errata]"], moves=[recoil_move])
        base_mon = PokemonState(spec=base_spec, controller_id="a", position=(0, 0), active=True)
        errata_mon = PokemonState(spec=errata_spec, controller_id="a", position=(0, 0), active=True)
        self.assertEqual(errata_mon.max_hp() - base_mon.max_hp(), 15)

        defender_spec = _pokemon_spec("Target", moves=[recoil_move])
        battle, attacker_id, defender_id = _build_battle(errata_spec, defender_spec)
        before = battle.pokemon[attacker_id].hp
        battle.resolve_move_targets(attacker_id, recoil_move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[attacker_id].hp, before)

    def test_adaptability_errata_adds_d10_to_stab_damage(self):
        move = MoveSpec(
            name="Flame Wheel",
            type="Fire",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        errata_spec = _pokemon_spec("Boost", abilities=["Adaptability [Errata]"], moves=[move], types=["Fire"])
        base_spec = _pokemon_spec("Base", moves=[move], types=["Fire"])
        defender_spec = _pokemon_spec("Target", moves=[move])

        battle, attacker_id, defender_id = _build_battle(errata_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [6] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        errata_damage = before - battle.pokemon[defender_id].hp

        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [6] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(
            attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position
        )
        base_damage = before_base - battle_base.pokemon[defender_base_id].hp
        self.assertGreater(errata_damage, base_damage)

    def test_aftermath_errata_bursts_for_three_ticks(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Striker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Boom", abilities=["Aftermath [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        ally = PokemonState(
            spec=_pokemon_spec("Ally", moves=[move]),
            controller_id="b",
            position=(3, 3),
            active=True,
        )
        battle.pokemon["b-2"] = ally
        battle.pokemon[defender_id].hp = 1
        before_attacker = battle.pokemon[attacker_id].hp
        before_ally = ally.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        tick = battle.pokemon[attacker_id].tick_value() * 3
        self.assertEqual(before_attacker - battle.pokemon[attacker_id].hp, tick)
        self.assertEqual(before_ally - ally.hp, ally.tick_value() * 3)

    def test_ambush_errata_flutches_and_penalizes_accuracy(self):
        move = MoveSpec(
            name="Quick Jab",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        ambush = MoveSpec(
            name="Ambush [Errata]",
            type="Dark",
            category="Status",
            ac=None,
            range_kind="Self",
            target_kind="Self",
        )
        attacker_spec = _pokemon_spec("Sneak", abilities=["Ambush [Errata]"], moves=[move, ambush])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, ambush, attacker_id, battle.pokemon[attacker_id].position)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.has_status("Flinch"))
        self.assertTrue(defender.get_temporary_effects("accuracy_penalty"))

    def test_arena_trap_errata_slows_and_traps(self):
        trap = MoveSpec(
            name="Arena Trap [Errata]",
            type="Ground",
            category="Status",
            ac=None,
            range_kind="Self",
            target_kind="Self",
        )
        attacker_spec = _pokemon_spec("Trap", abilities=["Arena Trap [Errata]"], moves=[trap])
        defender_spec = _pokemon_spec("Target", moves=[trap])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, trap, attacker_id, battle.pokemon[attacker_id].position)
        battle.start_round()
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.has_status("Slowed"))
        self.assertTrue(defender.has_status("Trapped"))

    def test_aroma_veil_errata_blocks_adjacent_only(self):
        move = MoveSpec(
            name="Confuse Ray",
            type="Ghost",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        holder_spec = _pokemon_spec("Veil", abilities=["Aroma Veil [Errata]"], moves=[move])
        target_spec = _pokemon_spec("Target", moves=[move])
        battle, _, defender_id = _build_battle(holder_spec, target_spec, attacker_pos=(2, 2), defender_pos=(2, 3))
        battle._apply_status(
            [],
            attacker_id="a-1",
            target_id=defender_id,
            move=move,
            target=battle.pokemon[defender_id],
            status="Confused",
            effect="test",
            description="",
        )
        self.assertFalse(battle.pokemon[defender_id].has_status("Confused"))

        battle.pokemon["a-1"].position = (2, 0)
        battle._apply_status(
            [],
            attacker_id="a-1",
            target_id=defender_id,
            move=move,
            target=battle.pokemon[defender_id],
            status="Confused",
            effect="test",
            description="",
        )
        self.assertTrue(battle.pokemon[defender_id].has_status("Confused"))

    def test_aura_break_errata_inverts_adaptability(self):
        aura_break = MoveSpec(
            name="Aura Break [Errata]",
            type="Dark",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        breaker_spec = _pokemon_spec("Breaker", abilities=["Aura Break [Errata]"], moves=[aura_break])
        target_spec = _pokemon_spec("Adapt", abilities=["Adaptability"], moves=[move], types=["Water"])
        defender_spec = _pokemon_spec("Dummy", moves=[move], hp_stat=20)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A"), "b": TrainerState(identifier="b", name="B")},
            pokemon={
                "a-1": PokemonState(spec=breaker_spec, controller_id="a", position=(2, 2), active=True),
                "b-1": PokemonState(spec=target_spec, controller_id="b", position=(2, 3), active=True),
                "b-2": PokemonState(spec=defender_spec, controller_id="b", position=(2, 4), active=True),
            },
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([20] * 200)
        battle.resolve_move_targets("a-1", aura_break, "b-1", battle.pokemon["b-1"].position)
        battle.resolve_move_targets("b-1", move, "b-2", battle.pokemon["b-2"].position)
        inverted_event = next(
            entry
            for entry in battle.log
            if entry.get("type") == "move" and entry.get("move") == "Water Gun" and entry.get("actor") == "b-1"
        )

        battle_base, attacker_id, defender_id = _build_battle(target_spec, defender_spec)
        battle_base.rng = SequenceRNG([20] * 200)
        battle_base.resolve_move_targets(attacker_id, move, defender_id, battle_base.pokemon[defender_id].position)
        base_event = next(
            entry
            for entry in battle_base.log
            if entry.get("type") == "move" and entry.get("move") == "Water Gun" and entry.get("actor") == attacker_id
        )
        self.assertLess(inverted_event.get("effective_db", 0), base_event.get("effective_db", 0))

    def test_aura_storm_errata_scales_with_injuries(self):
        move = MoveSpec(
            name="Shadow Ball",
            type="Ghost",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Storm", abilities=["Aura Storm [Errata]"], moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].injuries = 2
        battle.rng = SequenceRNG([20] + [4] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        boosted = before - battle.pokemon[defender_id].hp

        base_battle, base_attacker_id, base_defender_id = _build_battle(
            _pokemon_spec("Base", moves=[move], spatk=14), defender_spec
        )
        base_battle.rng = SequenceRNG([20] + [4] * 20)
        base_before = base_battle.pokemon[base_defender_id].hp
        base_battle.resolve_move_targets(
            base_attacker_id, move, base_defender_id, base_battle.pokemon[base_defender_id].position
        )
        base_damage = base_before - base_battle.pokemon[base_defender_id].hp
        self.assertEqual(boosted - base_damage, 6)

    def test_bad_dreams_errata_drains_sleeping_targets(self):
        bad_dreams = MoveSpec(
            name="Bad Dreams [Errata]",
            type="Dark",
            category="Status",
            ac=None,
            range_kind="Self",
            target_kind="Self",
        )
        attacker_spec = _pokemon_spec("Night", abilities=["Bad Dreams [Errata]"], moves=[bad_dreams])
        defender_spec = _pokemon_spec("Sleeper", moves=[bad_dreams])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.statuses.append({"name": "Sleep"})
        before = defender.hp
        battle.resolve_move_targets(attacker_id, bad_dreams, attacker_id, battle.pokemon[attacker_id].position)
        self.assertEqual(before - defender.hp, defender.tick_value())
        self.assertGreater(battle.pokemon[attacker_id].temp_hp, 0)

    def test_beautiful_errata_boosts_spatk_and_cures_enraged(self):
        beautiful = MoveSpec(
            name="Beautiful [Errata]",
            type="Fairy",
            category="Status",
            ac=None,
            range_kind="Self",
            target_kind="Self",
        )
        attacker_spec = _pokemon_spec("Pretty", abilities=["Beautiful [Errata]"], moves=[beautiful])
        ally_spec = _pokemon_spec("Ally", moves=[beautiful])
        battle, attacker_id, _ = _build_battle(attacker_spec, ally_spec)
        ally = PokemonState(spec=ally_spec, controller_id="a", position=(3, 2), active=True)
        ally.statuses.append({"name": "Enraged"})
        battle.pokemon["a-2"] = ally
        before = battle.pokemon[attacker_id].combat_stages.get("spatk", 0)
        battle.resolve_move_targets(attacker_id, beautiful, attacker_id, battle.pokemon[attacker_id].position)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("spatk", 0), before + 1)
        self.assertFalse(ally.has_status("Enraged"))
