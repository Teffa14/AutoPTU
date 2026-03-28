import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.random_campaign import CsvRandomCampaignBuilder


class StubSpecies:
    def __init__(self, name: str, stats_total: int, capabilities: list[str] | None = None) -> None:
        self.name = name
        self.capabilities = capabilities or []
        base_keys = ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]
        base = stats_total // len(base_keys)
        remainder = stats_total - (base * len(base_keys))
        values = [base for _ in base_keys]
        for idx in range(remainder):
            values[idx % len(values)] += 1
        self.base_stats = dict(zip(base_keys, values))


class FakeRepo:
    def __init__(self) -> None:
        self.root = "fake-root"
        self.records = [
            StubSpecies("Beginner", 30, ["Underdog"]),
            StubSpecies("StageOne", 44, []),
            StubSpecies("FinalBoss", 60, []),
        ]

    def available(self) -> bool:
        return True

    def iter_species(self):
        return list(self.records)

    def build_pokemon_spec(self, name: str, level: int = 20, **_kwargs):
        return PokemonSpec(
            species=name,
            level=level,
            types=["Electric"],
            hp_stat=10,
            atk=8,
            defense=7,
            spatk=6,
            spdef=7,
            spd=9,
        )


class RandomCampaignTests(unittest.TestCase):
    def test_random_campaign_builder_creates_rosters(self) -> None:
        builder = CsvRandomCampaignBuilder(repo=FakeRepo(), seed=123)
        campaign = builder.build(team_size=2, min_level=5, max_level=5)
        self.assertTrue(campaign.players and campaign.foes)
        self.assertEqual(len(campaign.players), len(campaign.foes))
        self.assertEqual(2, len(campaign.players))
        self.assertIn("csv-random", campaign.players[0].tags)
        self.assertEqual("csv_random", campaign.metadata["source"])

    def test_random_campaign_respects_min_level_hints(self) -> None:
        builder = CsvRandomCampaignBuilder(repo=FakeRepo(), seed=7)
        low = builder.build(team_size=1, min_level=5, max_level=5)
        self.assertNotEqual("FinalBoss", low.players[0].species)
        high = builder.build(team_size=1, min_level=55, max_level=55)
        self.assertEqual("FinalBoss", high.players[0].species)

    def test_random_campaign_pool_counts_base_species_once(self) -> None:
        repo = FakeRepo()
        repo.records = [
            StubSpecies("Lycanroc Midday", 40, []),
            StubSpecies("Lycanroc Midnight", 40, []),
            StubSpecies("Pikachu", 40, []),
        ]
        builder = CsvRandomCampaignBuilder(repo=repo, seed=19)
        grouped = builder._group_species_forms(repo.records)
        self.assertEqual({"lycanroc", "pikachu"}, set(grouped.keys()))
        picks = [builder._pick_species_for_level(repo.records, level=20) for _ in range(500)]
        base_counts = {"lycanroc": 0, "pikachu": 0}
        form_seen = set()
        for record in picks:
            base = builder._base_species_key(record.name)
            base_counts[base] += 1
            if base == "lycanroc":
                form_seen.add(record.name.lower())
        ratio = base_counts["lycanroc"] / max(1, sum(base_counts.values()))
        self.assertGreater(ratio, 0.40)
        self.assertLess(ratio, 0.60)
        self.assertIn("lycanroc midday", form_seen)
        self.assertIn("lycanroc midnight", form_seen)

    def test_random_campaign_skips_placeholder_species(self) -> None:
        repo = FakeRepo()
        repo.records = [StubSpecies("Egg", 30), StubSpecies("MEGAS", 30), StubSpecies("Validmon", 30)]
        builder = CsvRandomCampaignBuilder(repo=repo, seed=9)
        campaign = builder.build(team_size=1, min_level=5, max_level=5)
        self.assertEqual("Validmon", campaign.players[0].species)
        self.assertEqual("Validmon", campaign.foes[0].species)

    def test_random_campaign_skips_unsupported_custom_species(self) -> None:
        repo = FakeRepo()
        repo.records = [StubSpecies("Illuseon", 30), StubSpecies("Validmon", 30)]
        builder = CsvRandomCampaignBuilder(repo=repo, seed=9)
        campaign = builder.build(team_size=1, min_level=5, max_level=5)
        self.assertEqual("Validmon", campaign.players[0].species)
        self.assertEqual("Validmon", campaign.foes[0].species)

    def test_level_up_stats_use_minmax_spread_not_single_stat(self) -> None:
        builder = CsvRandomCampaignBuilder(repo=FakeRepo(), seed=11)
        mon = PokemonSpec(
            species="Spreadmon",
            level=50,
            types=["Electric"],
            hp_stat=9,
            atk=6,
            defense=6,
            spatk=10,
            spdef=7,
            spd=9,
            moves=[
                MoveSpec(name="Thunderbolt", type="Electric", category="Special", db=8),
                MoveSpec(name="Discharge", type="Electric", category="Special", db=7),
                MoveSpec(name="Nasty Plot", type="Dark", category="Status", db=0),
            ],
        )
        before = {
            "hp_stat": mon.hp_stat,
            "atk": mon.atk,
            "defense": mon.defense,
            "spatk": mon.spatk,
            "spdef": mon.spdef,
            "spd": mon.spd,
        }
        builder._apply_level_up_stats(mon)
        after = {
            "hp_stat": mon.hp_stat,
            "atk": mon.atk,
            "defense": mon.defense,
            "spatk": mon.spatk,
            "spdef": mon.spdef,
            "spd": mon.spd,
        }
        gains = {stat: after[stat] - before[stat] for stat in before}
        self.assertEqual(sum(gains.values()), mon.level + 10)
        self.assertGreaterEqual(sum(1 for value in gains.values() if value > 0), 2)
        self.assertGreater(gains["spatk"], 0)
        self.assertGreater(gains["spd"], 0)

    def test_level_up_stats_enforce_scaled_hp_floor(self) -> None:
        builder = CsvRandomCampaignBuilder(repo=FakeRepo(), seed=13)
        mon = PokemonSpec(
            species="GlassCannon",
            level=100,
            types=["Electric"],
            hp_stat=8,
            atk=5,
            defense=5,
            spatk=15,
            spdef=5,
            spd=16,
            moves=[
                MoveSpec(name="Thunderbolt", type="Electric", category="Special", db=8),
                MoveSpec(name="Volt Switch", type="Electric", category="Special", db=7),
                MoveSpec(name="Discharge", type="Electric", category="Special", db=7),
                MoveSpec(name="Shock Wave", type="Electric", category="Special", db=6),
            ],
        )
        before_hp = mon.hp_stat
        total_points = mon.level + 10
        min_hp_points = builder._minimum_hp_points(total_points, "sweeper")
        builder._apply_level_up_stats(mon)
        hp_gain = mon.hp_stat - before_hp
        self.assertGreaterEqual(hp_gain, min_hp_points)

    def test_minimum_hp_floor_scales_consistently_by_level(self) -> None:
        builder = CsvRandomCampaignBuilder(repo=FakeRepo(), seed=21)
        levels = [5, 20, 40, 60, 80, 100]
        floors = [builder._minimum_hp_points(level + 10, "sweeper") for level in levels]
        self.assertEqual(sorted(floors), floors)

    def test_objective_optimizer_balances_exact_points_and_role_bias(self) -> None:
        builder = CsvRandomCampaignBuilder(repo=FakeRepo(), seed=34)
        totals = {
            "hp_stat": 8,
            "atk": 7,
            "defense": 6,
            "spatk": 15,
            "spdef": 7,
            "spd": 14,
        }
        points = 110
        sweeper = builder._optimize_allocation(
            points=points,
            totals=totals,
            build="sweeper",
            primary_attack="spatk",
            secondary_attack="atk",
            physical_moves=1,
            special_moves=3,
            repeatable_damaging=2,
            status_moves=1,
        )
        wall = builder._optimize_allocation(
            points=points,
            totals=totals,
            build="wall",
            primary_attack="spatk",
            secondary_attack="atk",
            physical_moves=1,
            special_moves=3,
            repeatable_damaging=2,
            status_moves=1,
        )
        self.assertEqual(points, sum(int(v) for v in sweeper.values()))
        self.assertEqual(points, sum(int(v) for v in wall.values()))
        self.assertGreaterEqual(
            int(sweeper.get("hp_stat", 0)),
            builder._minimum_hp_points(points, "sweeper"),
        )
        self.assertGreaterEqual(
            int(wall.get("hp_stat", 0)),
            builder._minimum_hp_points(points, "wall"),
        )
        self.assertGreaterEqual(int(wall.get("hp_stat", 0)), int(sweeper.get("hp_stat", 0)))
