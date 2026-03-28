import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, TurnPhase, UseMoveAction
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
        weight=5,
    )


def _build_battle(attacker_spec, defender_spec):
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
        grid=GridState(width=10, height=10),
    )
    battle.rng = SequenceRNG([20] * 200)
    battle.round = 1
    return battle, "a-1", "b-1"


class AuditBatch42AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_soothing_tone_errata_heals_on_heal_bell(self):
        heal_bell = MoveSpec(
            name="Heal Bell",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Field",
            range_text="Field",
        )
        attacker_spec = _pokemon_spec("Singer", abilities=["Soothing Tone [Errata]"], moves=[heal_bell])
        ally_spec = _pokemon_spec("Ally", moves=[heal_bell])
        battle, attacker_id, _ = _build_battle(attacker_spec, ally_spec)
        ally = PokemonState(spec=ally_spec, controller_id="a", position=(2, 4), active=True)
        ally.hp = max(1, ally.hp - ally.tick_value())
        ally.statuses.append({"name": "Burned"})
        battle.pokemon["a-2"] = ally

        battle.resolve_move_targets(attacker_id, heal_bell, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Soothing Tone"
                and event.get("effect") == "heal"
                for event in battle.log
            )
        )

    def test_sorcery_adds_special_attack_bonus(self):
        spec = _pokemon_spec("Mage", ability="Sorcery", level=30)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        bonus = [
            entry
            for entry in mon.get_temporary_effects("stat_modifier")
            if entry.get("stat") == "spatk" and entry.get("source") == "Sorcery"
        ]
        self.assertTrue(bonus)

    def test_soul_heart_triggers_on_faint(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        soul_spec = _pokemon_spec("Heart", ability="Soul Heart", moves=[move], hp_stat=12)
        ally_spec = _pokemon_spec("Ally", moves=[move], hp_stat=1)
        foe_spec = _pokemon_spec("Foe", moves=[move], atk=14)
        battle = BattleState(
            trainers={
                "a": TrainerState(identifier="a", name="A", team="players"),
                "b": TrainerState(identifier="b", name="B", team="foes"),
            },
            pokemon={},
            grid=GridState(width=6, height=6),
        )
        heart = PokemonState(spec=soul_spec, controller_id="a", position=(2, 2), active=True)
        ally = PokemonState(spec=ally_spec, controller_id="a", position=(2, 3), active=True)
        foe = PokemonState(spec=foe_spec, controller_id="b", position=(2, 4), active=True)
        battle.pokemon.update({"a-1": heart, "a-2": ally, "b-1": foe})
        ally.hp = 1
        battle.resolve_move_targets("b-1", move, "a-2", ally.position)
        self.assertEqual(heart.combat_stages.get("spatk"), 2)

    def test_soulstealer_errata_heals_on_hit(self):
        move = MoveSpec(
            name="Shadow Claw",
            type="Ghost",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Soul", abilities=["Soulstealer [Errata]"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].hp = max(1, battle.pokemon[attacker_id].hp - battle.pokemon[attacker_id].tick_value())
        before = battle.pokemon[attacker_id].hp
        battle.rng = SequenceRNG([20] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertGreater(battle.pokemon[attacker_id].hp, before)

    def test_sound_lance_errata_deals_damage_on_miss(self):
        sound_lance = MoveSpec(
            name="Sound Lance [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        supersonic = MoveSpec(
            name="Supersonic",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Lancer", abilities=["Sound Lance [Errata]"], moves=[sound_lance, supersonic], spatk=14)
        defender_spec = _pokemon_spec("Target", moves=[supersonic])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, sound_lance, attacker_id, battle.pokemon[attacker_id].position)
        battle.rng = SequenceRNG([1] + [3] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, supersonic, defender_id, battle.pokemon[defender_id].position)
        self.assertLess(battle.pokemon[defender_id].hp, before)

    def test_speed_boost_increases_speed_stage(self):
        spec = _pokemon_spec("Speedy", ability="Speed Boost")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon._handle_ability_phase_effects(battle, TurnPhase.END, "a-1")
        self.assertEqual(mon.combat_stages.get("spd"), 1)

    def test_spike_shot_extends_melee_range(self):
        move = MoveSpec(
            name="Scratch",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Spiker", ability="Spike Shot", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        action = UseMoveAction(actor_id=attacker_id, move_name=move.name)
        effective = action._apply_ability_move_tweaks(battle, battle.pokemon[attacker_id], move)
        self.assertEqual(effective.range_kind, "Ranged")
        self.assertEqual(effective.range_value, 8)

    def test_spiteful_intervention_disables_attacker_move(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        defender_spec = _pokemon_spec("Defender", moves=[move])
        holder_spec = _pokemon_spec("Holder", ability="Spiteful Intervention", moves=[move])
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        battle = BattleState(
            trainers={
                "a": TrainerState(identifier="a", name="A", team="players"),
                "b": TrainerState(identifier="b", name="B", team="foes"),
            },
            pokemon={},
            grid=GridState(width=6, height=6),
        )
        defender = PokemonState(spec=defender_spec, controller_id="a", position=(2, 2), active=True)
        holder = PokemonState(spec=holder_spec, controller_id="a", position=(2, 4), active=True)
        attacker = PokemonState(spec=attacker_spec, controller_id="b", position=(2, 3), active=True)
        battle.pokemon.update({"a-1": defender, "a-2": holder, "b-1": attacker})
        battle.pokemon["b-1"].add_temporary_effect("last_move", name="Tackle")
        battle.rng = SequenceRNG([20] + [3] * 20)
        battle.resolve_move_targets("b-1", move, "a-1", defender.position)
        self.assertTrue(attacker.has_status("Disabled"))

    def test_splendorous_rider_borrows_mount_move(self):
        rider = MoveSpec(
            name="Splendorous Rider",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        mount_move = MoveSpec(
            name="Charge",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Rider", ability="Splendorous Rider", moves=[rider])
        defender_spec = _pokemon_spec("Target", moves=[mount_move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].add_temporary_effect("mount_moves", moves=[mount_move])
        battle.resolve_move_targets(attacker_id, rider, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(
            any(mv.name == "Charge" for mv in battle.pokemon[attacker_id].spec.moves)
        )
