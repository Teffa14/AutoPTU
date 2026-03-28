"""Build campaign specs straight from the Fancy PTU CSV bundle."""
from __future__ import annotations

import random
from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from .csv_repository import PTUCsvRepository, SpeciesRecord
from .data_loader import default_campaign
from .data_models import CampaignSpec, GridSpec, PokemonSpec
from .learnsets import normalize_species_key
from .species_filters import is_user_selectable_species_name


class CsvRandomCampaignBuilder:
    """Assemble balanced rosters by sampling directly from the CSV data bundle."""

    def __init__(
        self,
        repo: PTUCsvRepository | None = None,
        seed: Optional[int] = None,
        grid: Optional[GridSpec] = None,
    ) -> None:
        self.random = random.Random(seed)
        self.repo = repo or PTUCsvRepository(rng=self.random)
        base_grid = grid or default_campaign().grid
        self.grid = deepcopy(base_grid)
        self._name_counter = 1
        self._item_pool: Optional[List[object]] = None
        self._form_suffixes = {
            "alola",
            "galar",
            "hisui",
            "paldea",
            "super",
            "large",
            "small",
            "average",
            "origin",
            "altered",
            "incarnate",
            "therian",
            "core",
            "meteor",
            "crowned",
            "hero",
            "dusk",
            "dawn",
            "ultra",
            "male",
            "female",
            "baile",
            "pom",
            "pom-pom",
            "pau",
            "sensu",
            "red",
            "midday",
            "midnight",
            "day",
            "night",
            "school",
            "solo",
            "amped",
            "low",
            "key",
            "hangry",
            "noice",
            "ice",
            "land",
            "sky",
            "attack",
            "defense",
            "speed",
            "normal",
        }

    def build(
        self,
        team_size: int,
        min_level: int = 20,
        max_level: int = 40,
    ) -> CampaignSpec:
        if not self.repo.available():
            raise FileNotFoundError(
                f"CSV bundle not found under {self.repo.root}. Drop the Fancy PTU files there first."
            )
        records = [record for record in self.repo.iter_species() if self._is_playable_species(record)]
        if not records:
            raise ValueError("Failed to load species records from the CSV bundle.")
        players = [self._random_mon(records, min_level, max_level, prefix="Player") for _ in range(team_size)]
        foes = [self._random_mon(records, min_level, max_level, prefix="Foe") for _ in range(team_size)]
        grid = self._build_random_grid(self.grid)
        return CampaignSpec(
            name="CSV Arena",
            description="Random rosters generated from the Fancy PTU CSV dataset.",
            default_weather="Clear",
            grid=grid,
            players=players,
            foes=foes,
            metadata={"source": "csv_random", "min_level": min_level, "max_level": max_level},
        )

    def _random_mon(
        self,
        records: List[SpeciesRecord],
        min_level: int,
        max_level: int,
        prefix: str,
    ) -> PokemonSpec:
        level = self.random.randint(min_level, max_level)
        species_record = self._pick_species_for_level(records, level)
        mon = self.repo.build_pokemon_spec(
            species_record.name,
            level=level,
            assign_abilities=True,
            assign_nature=True,
        )
        self._apply_level_up_stats(mon)
        self._assign_random_items(mon, level)
        mon.tags.append("csv-random")
        mon.name = f"{prefix} {self._name_counter}: {mon.species}"
        self._name_counter += 1
        return mon

    def _pick_species_for_level(self, records: List[SpeciesRecord], level: int) -> SpeciesRecord:
        by_species = self._group_species_forms(records)
        species_rows: List[Tuple[int, str, List[SpeciesRecord]]] = []
        for base_key, forms in by_species.items():
            if not forms:
                continue
            min_level = min(self._recommended_min_level(form) for form in forms)
            species_rows.append((min_level, base_key, forms))
        if not species_rows:
            raise ValueError("No species available for random campaign generation.")
        eligible = [row for row in species_rows if row[0] <= level]
        if not eligible:
            eligible = sorted(species_rows, key=lambda row: row[0])
            _, _, forms = self.random.choice(eligible)
            return self.random.choice(forms)
        eligible.sort(key=lambda row: row[0])
        if level >= 50:
            pool_size = max(1, len(eligible) // 3)
            pool = eligible[-pool_size:]
        elif level >= 30:
            pool_size = max(1, len(eligible) // 2)
            pool = eligible[-pool_size:]
        else:
            pool = eligible
        _, _, forms = self.random.choice(pool)
        return self.random.choice(forms)

    def _group_species_forms(self, records: List[SpeciesRecord]) -> Dict[str, List[SpeciesRecord]]:
        grouped: Dict[str, List[SpeciesRecord]] = {}
        for record in records:
            base_key = self._base_species_key(record.name)
            if not base_key:
                base_key = normalize_species_key(record.name)
            grouped.setdefault(base_key, []).append(record)
        return grouped

    def _base_species_key(self, name: str) -> str:
        key = normalize_species_key(name)
        if not key:
            return ""
        tokens = [token for token in key.split() if token]
        if not tokens:
            return ""
        if tokens[0] in {"mega", "primal", "gmax", "gigantamax"} and len(tokens) > 1:
            tokens = tokens[1:]
        while len(tokens) > 1 and tokens[-1] in self._form_suffixes:
            tokens = tokens[:-1]
        if len(tokens) > 1 and tokens[-1] in {"n", "da", "du"} and tokens[0] == "lycanroc":
            tokens = tokens[:-1]
        return " ".join(tokens)

    def _apply_level_up_stats(self, mon: PokemonSpec) -> None:
        """Apply PTU level-up points using an objective-driven minmax spread."""
        points = max(0, int(mon.level) + 10)
        if points <= 0:
            return
        totals = {
            "hp_stat": int(mon.hp_stat),
            "atk": int(mon.atk),
            "defense": int(mon.defense),
            "spatk": int(mon.spatk),
            "spdef": int(mon.spdef),
            "spd": int(mon.spd),
        }
        primary_attack, secondary_attack, physical_moves, special_moves = self._attack_profile(mon, totals)
        build = self._choose_build(
            totals,
            primary_attack=primary_attack,
            physical_moves=physical_moves,
            special_moves=special_moves,
        )
        repeatable_damaging = self._repeatable_damaging_count(mon.moves or [])
        status_moves = self._status_move_count(mon.moves or [])
        allocation = self._optimize_allocation(
            points=points,
            totals=totals,
            build=build,
            primary_attack=primary_attack,
            secondary_attack=secondary_attack,
            physical_moves=physical_moves,
            special_moves=special_moves,
            repeatable_damaging=repeatable_damaging,
            status_moves=status_moves,
        )
        for stat, amount in allocation.items():
            totals[stat] += int(amount)
        mon.hp_stat = totals["hp_stat"]
        mon.atk = totals["atk"]
        mon.defense = totals["defense"]
        mon.spatk = totals["spatk"]
        mon.spdef = totals["spdef"]
        mon.spd = totals["spd"]

    @staticmethod
    def _stat_order() -> List[str]:
        return ["hp_stat", "atk", "defense", "spatk", "spdef", "spd"]

    @staticmethod
    def _repeatable_damaging_count(moves: List[object]) -> int:
        count = 0
        for move in moves:
            category = str(getattr(move, "category", "") or "").strip().lower()
            db = int(getattr(move, "db", 0) or 0)
            if category == "status" or db <= 0:
                continue
            frequency = str(getattr(move, "freq", "") or "").strip().lower()
            if "at-will" in frequency or "eot" in frequency or frequency in {"standard", "free", "shift", "action"}:
                count += 1
        return count

    @staticmethod
    def _status_move_count(moves: List[object]) -> int:
        count = 0
        for move in moves:
            category = str(getattr(move, "category", "") or "").strip().lower()
            db = int(getattr(move, "db", 0) or 0)
            if category == "status" or db <= 0:
                count += 1
        return count

    def _attack_profile(self, mon: PokemonSpec, totals: dict) -> tuple[str, str, int, int]:
        physical_moves = 0
        special_moves = 0
        for move in mon.moves or []:
            category = str(getattr(move, "category", "") or "").strip().lower()
            db = int(getattr(move, "db", 0) or 0)
            if db <= 0:
                continue
            if category == "physical":
                physical_moves += 1
            elif category == "special":
                special_moves += 1
        if physical_moves > special_moves:
            return "atk", "spatk", physical_moves, special_moves
        if special_moves > physical_moves:
            return "spatk", "atk", physical_moves, special_moves
        if int(totals["atk"]) >= int(totals["spatk"]):
            return "atk", "spatk", physical_moves, special_moves
        return "spatk", "atk", physical_moves, special_moves

    def _choose_build(
        self,
        totals: dict,
        *,
        primary_attack: str,
        physical_moves: int,
        special_moves: int,
    ) -> str:
        offense = int(totals[primary_attack])
        speed = int(totals["spd"])
        hp = int(totals["hp_stat"])
        defense = int(totals["defense"])
        spdef = int(totals["spdef"])
        bulk = max(hp, defense, spdef)
        if physical_moves > 0 and special_moves > 0 and abs(physical_moves - special_moves) <= 1:
            if speed >= offense - 1:
                return "mixed_sweeper"
            return "mixed_bruiser"
        if speed >= offense and speed >= bulk - 1:
            return "sweeper"
        if bulk >= offense + 2:
            return "wall"
        return "bruiser"

    def _build_weights(
        self,
        build: str,
        totals: dict,
        *,
        primary_attack: str,
        secondary_attack: str,
    ) -> dict:
        better_bulk = "defense" if int(totals["defense"]) >= int(totals["spdef"]) else "spdef"
        other_bulk = "spdef" if better_bulk == "defense" else "defense"
        if build == "sweeper":
            return {
                primary_attack: 46,
                "spd": 34,
                "hp_stat": 12,
                better_bulk: 8,
                other_bulk: 0,
                secondary_attack: 0,
            }
        if build == "wall":
            return {
                "hp_stat": 38,
                "defense": 24,
                "spdef": 24,
                "spd": 8,
                primary_attack: 6,
                secondary_attack: 0,
            }
        if build == "mixed_sweeper":
            return {
                "atk": 28,
                "spatk": 28,
                "spd": 24,
                "hp_stat": 12,
                "defense": 4,
                "spdef": 4,
            }
        if build == "mixed_bruiser":
            return {
                "atk": 22,
                "spatk": 22,
                "hp_stat": 26,
                "spd": 14,
                "defense": 8,
                "spdef": 8,
            }
        return {
            primary_attack: 38,
            "hp_stat": 28,
            "spd": 16,
            "defense": 8,
            "spdef": 8,
            secondary_attack: 2,
        }

    def _allocate_points(self, points: int, weights: dict) -> dict:
        order = self._stat_order()
        allocation = {stat: 0 for stat in order}
        weighted_stats = [stat for stat in order if int(weights.get(stat, 0)) > 0]
        if points <= 0 or not weighted_stats:
            return allocation
        ranked = sorted(
            weighted_stats,
            key=lambda stat: (-int(weights.get(stat, 0)), order.index(stat)),
        )
        seeded = 0
        if points >= 2 and len(ranked) >= 2:
            allocation[ranked[0]] += 1
            allocation[ranked[1]] += 1
            seeded = 2
        else:
            allocation[ranked[0]] += 1
            seeded = 1
        remaining = points - seeded
        if remaining <= 0:
            return allocation
        total_weight = sum(int(weights.get(stat, 0)) for stat in weighted_stats)
        raw_shares = {
            stat: (int(weights.get(stat, 0)) / total_weight) * remaining
            for stat in weighted_stats
        }
        floor_shares = {stat: int(raw_shares[stat]) for stat in weighted_stats}
        for stat, value in floor_shares.items():
            allocation[stat] += value
        remainder = remaining - sum(floor_shares.values())
        if remainder <= 0:
            return allocation
        remainder_order = sorted(
            weighted_stats,
            key=lambda stat: (
                -(raw_shares[stat] - floor_shares[stat]),
                -int(weights.get(stat, 0)),
                order.index(stat),
            ),
        )
        for idx in range(remainder):
            allocation[remainder_order[idx % len(remainder_order)]] += 1
        return allocation

    def _optimize_allocation(
        self,
        *,
        points: int,
        totals: dict,
        build: str,
        primary_attack: str,
        secondary_attack: str,
        physical_moves: int,
        special_moves: int,
        repeatable_damaging: int,
        status_moves: int,
    ) -> dict:
        """Choose the best legal level-up distribution under a simple combat objective."""
        min_hp_points = self._minimum_hp_points(points, build)
        base_weights = self._build_weights(
            build,
            totals,
            primary_attack=primary_attack,
            secondary_attack=secondary_attack,
        )
        candidate_weights: List[dict] = []
        candidate_weights.append(base_weights)

        speed_focus = dict(base_weights)
        speed_focus["spd"] = int(speed_focus.get("spd", 0)) + 10
        speed_focus[primary_attack] = int(speed_focus.get(primary_attack, 0)) + 4
        speed_focus["hp_stat"] = max(0, int(speed_focus.get("hp_stat", 0)) - 6)
        candidate_weights.append(speed_focus)

        offense_focus = dict(base_weights)
        offense_focus[primary_attack] = int(offense_focus.get(primary_attack, 0)) + 12
        offense_focus["spd"] = int(offense_focus.get("spd", 0)) + 4
        offense_focus[secondary_attack] = max(0, int(offense_focus.get(secondary_attack, 0)) - 4)
        offense_focus["hp_stat"] = max(0, int(offense_focus.get("hp_stat", 0)) - 4)
        candidate_weights.append(offense_focus)

        bulk_focus = dict(base_weights)
        bulk_focus["hp_stat"] = int(bulk_focus.get("hp_stat", 0)) + 12
        bulk_focus["defense"] = int(bulk_focus.get("defense", 0)) + 6
        bulk_focus["spdef"] = int(bulk_focus.get("spdef", 0)) + 6
        bulk_focus[primary_attack] = max(0, int(bulk_focus.get(primary_attack, 0)) - 8)
        bulk_focus["spd"] = max(0, int(bulk_focus.get("spd", 0)) - 4)
        candidate_weights.append(bulk_focus)

        mixed_pressure = dict(base_weights)
        mixed_pressure["atk"] = int(mixed_pressure.get("atk", 0)) + 4
        mixed_pressure["spatk"] = int(mixed_pressure.get("spatk", 0)) + 4
        mixed_pressure["spd"] = int(mixed_pressure.get("spd", 0)) + 4
        mixed_pressure["hp_stat"] = int(mixed_pressure.get("hp_stat", 0)) + 2
        candidate_weights.append(mixed_pressure)

        best_allocation = None
        best_score = float("-inf")
        for raw_weights in candidate_weights:
            weights = self._normalize_weight_map(raw_weights)
            allocation = self._allocate_points(points, weights)
            allocation = self._rebalance_for_hp_floor(
                allocation,
                min_hp_points=min_hp_points,
                build=build,
                primary_attack=primary_attack,
                secondary_attack=secondary_attack,
            )
            score = self._allocation_objective(
                totals=totals,
                allocation=allocation,
                points=points,
                build=build,
                primary_attack=primary_attack,
                secondary_attack=secondary_attack,
                physical_moves=physical_moves,
                special_moves=special_moves,
                repeatable_damaging=repeatable_damaging,
                status_moves=status_moves,
            )
            if score > best_score:
                best_score = score
                best_allocation = allocation
        return best_allocation or {stat: 0 for stat in self._stat_order()}

    def _normalize_weight_map(self, weights: dict) -> dict:
        cleaned = {}
        for stat in self._stat_order():
            value = int(weights.get(stat, 0) or 0)
            cleaned[stat] = max(0, value)
        if sum(cleaned.values()) <= 0:
            cleaned["hp_stat"] = 1
        return cleaned

    def _allocation_objective(
        self,
        *,
        totals: dict,
        allocation: dict,
        points: int,
        build: str,
        primary_attack: str,
        secondary_attack: str,
        physical_moves: int,
        special_moves: int,
        repeatable_damaging: int,
        status_moves: int,
    ) -> float:
        final_stats = {
            stat: int(totals.get(stat, 0) or 0) + int(allocation.get(stat, 0) or 0)
            for stat in self._stat_order()
        }
        estimated_level = max(1, int(points) - 10)
        max_hp = estimated_level + (3 * final_stats["hp_stat"]) + 10
        primary = float(final_stats.get(primary_attack, 0))
        secondary = float(final_stats.get(secondary_attack, 0))
        speed = float(final_stats.get("spd", 0))
        defense = float(final_stats.get("defense", 0))
        spdef = float(final_stats.get("spdef", 0))
        hp_stat = float(final_stats.get("hp_stat", 0))

        # PTU evasion scales with stat//5, so landing breakpoints matters more than loose +1s.
        breakpoint_score = (
            float(final_stats["spd"] // 5) * 1.1
            + float(final_stats["defense"] // 5) * 0.9
            + float(final_stats["spdef"] // 5) * 0.9
        )
        bulk_linear = (hp_stat * 3.0) + (defense + spdef) * 0.9
        bulk_product = (max_hp * (defense + spdef + 2.0)) ** 0.5
        mixed_usage = 1.0 if physical_moves > 0 and special_moves > 0 else 0.0
        reliability_bonus = 1.0 + (min(2, max(0, repeatable_damaging)) * 0.12)
        setup_bonus = min(2, max(0, status_moves)) * 0.15
        offense = ((primary * 1.0) + (secondary * (0.35 + (0.25 * mixed_usage)))) * reliability_bonus

        key = str(build or "").strip().lower()
        if key == "sweeper":
            return offense * 3.8 + speed * 2.4 + breakpoint_score * 1.6 + bulk_linear * 0.7 + setup_bonus
        if key == "mixed_sweeper":
            return offense * 3.4 + speed * 2.0 + breakpoint_score * 1.7 + bulk_linear * 0.85 + setup_bonus
        if key == "wall":
            return bulk_linear * 3.1 + bulk_product * 0.55 + breakpoint_score * 2.1 + offense * 1.3 + setup_bonus
        if key == "mixed_bruiser":
            return offense * 2.5 + bulk_linear * 2.3 + breakpoint_score * 1.8 + speed * 1.1 + setup_bonus
        return offense * 3.0 + bulk_linear * 1.8 + breakpoint_score * 1.7 + speed * 1.2 + setup_bonus

    def _minimum_hp_points(self, points: int, build: str) -> int:
        """Keep HP investment proportional at every level so high-level fights don't feel paper-thin."""
        ratios = {
            "sweeper": 0.22,
            "mixed_sweeper": 0.20,
            "bruiser": 0.26,
            "mixed_bruiser": 0.28,
            "wall": 0.34,
        }
        ratio = ratios.get(str(build or "").strip().lower(), 0.24)
        # Gradually raise the HP floor as battles scale up so bulk keeps pace at higher levels.
        level_bonus = min(0.05, max(0.0, (float(points) - 20.0) / 90.0 * 0.05))
        ratio = min(0.42, ratio + level_bonus)
        floor = int(round(points * ratio))
        floor = max(1, floor)
        if points >= 4:
            floor = max(2, floor)
        return min(points, floor)

    def _hp_rebalance_donor_order(
        self,
        build: str,
        *,
        primary_attack: str,
        secondary_attack: str,
    ) -> List[str]:
        key = str(build or "").strip().lower()
        if key == "wall":
            base = ["defense", "spdef", "spd", primary_attack, secondary_attack, "atk", "spatk"]
        elif key == "mixed_sweeper":
            base = ["atk", "spatk", "spd", "defense", "spdef", "hp_stat"]
        elif key == "mixed_bruiser":
            base = ["atk", "spatk", "spd", "defense", "spdef", "hp_stat"]
        elif key == "sweeper":
            base = [primary_attack, "spd", "defense", "spdef", secondary_attack, "atk", "spatk"]
        else:
            base = [primary_attack, "spd", "defense", "spdef", secondary_attack, "atk", "spatk"]
        seen: set[str] = set()
        ordered: List[str] = []
        for stat in base:
            cleaned = str(stat or "").strip()
            if not cleaned or cleaned == "hp_stat" or cleaned in seen:
                continue
            seen.add(cleaned)
            ordered.append(cleaned)
        for stat in self._stat_order():
            if stat in {"hp_stat"} or stat in seen:
                continue
            ordered.append(stat)
            seen.add(stat)
        return ordered

    def _rebalance_for_hp_floor(
        self,
        allocation: dict,
        *,
        min_hp_points: int,
        build: str,
        primary_attack: str,
        secondary_attack: str,
    ) -> dict:
        adjusted = {stat: int(allocation.get(stat, 0) or 0) for stat in self._stat_order()}
        current_hp = int(adjusted.get("hp_stat", 0))
        deficit = max(0, int(min_hp_points) - current_hp)
        if deficit <= 0:
            return adjusted
        donors = self._hp_rebalance_donor_order(
            build,
            primary_attack=primary_attack,
            secondary_attack=secondary_attack,
        )
        for stat in donors:
            if deficit <= 0:
                break
            transferable = int(adjusted.get(stat, 0))
            if transferable <= 0:
                continue
            take = min(transferable, deficit)
            adjusted[stat] -= take
            adjusted["hp_stat"] += take
            deficit -= take
        return adjusted

    @staticmethod
    def _recommended_min_level(record: SpeciesRecord) -> int:
        stats_total = sum(record.base_stats.values())
        caps = {cap.lower() for cap in record.capabilities}
        if "underdog" in caps:
            return 1
        if stats_total >= 65:
            return 55  # Legendary/Mythical tier
        if stats_total >= 60:
            return 45  # Pseudo-legendary finales
        if stats_total >= 55:
            return 35  # Fully evolved starters / powerhouses
        if stats_total >= 45:
            return 25  # Stage 1 evolutions
        if stats_total >= 38:
            return 15  # Middle evolutions / stronger basics
        return 1

    @staticmethod
    def _is_playable_species(record: SpeciesRecord) -> bool:
        key = str(record.name or "").strip().lower()
        if not is_user_selectable_species_name(record.name):
            return False
        tokens = [token for token in key.split() if token]
        if "mega" in tokens:
            return False
        if "primal" in tokens:
            return False
        if "gmax" in tokens or "gigantamax" in tokens:
            return False
        if key.startswith("mega "):
            return False
        return True

    def _assign_random_items(self, mon: PokemonSpec, level: int) -> None:
        pool = self._item_pool_entries()
        if not pool:
            return
        count = 1
        if level >= 30 and self.random.random() < 0.25:
            count = 2
        count = min(count, len(pool))
        chosen = self.random.sample(pool, k=count)
        items = [{"name": entry.name} for entry in chosen]
        if items:
            items[0]["equipped"] = True
        mon.items = items

    def _item_pool_entries(self) -> List[object]:
        if self._item_pool is not None:
            return self._item_pool
        try:
            from .rules.item_catalog import load_item_catalog
            from .rules.item_effects import parse_item_effects
        except Exception:
            self._item_pool = []
            return self._item_pool
        catalog = load_item_catalog()
        pool: List[object] = []
        for entry in catalog.values():
            name = str(getattr(entry, "name", "") or "").strip()
            if not name:
                continue
            lower = name.lower()
            desc = str(getattr(entry, "description", "") or "").lower()
            traits = {str(trait).lower() for trait in (getattr(entry, "traits", set()) or set())}
            if "weapon" in traits:
                continue
            if "mega" in lower or "mega stone" in desc or "mega evolves" in desc:
                continue
            effects = parse_item_effects(entry)
            if effects or "held" in traits or "food" in traits or "consumable" in traits or "berry" in lower:
                pool.append(entry)
        self._item_pool = pool
        return self._item_pool

    def _build_random_grid(self, base_grid: GridSpec) -> GridSpec:
        width = self.random.randint(10, 14)
        height = self.random.randint(8, 12)
        blockers: List[Tuple[int, int]] = []
        tiles: Dict[Tuple[int, int], Dict[str, object]] = {}

        def is_reserved(coord: Tuple[int, int]) -> bool:
            x, y = coord
            if x <= 1 and y <= 1:
                return True
            if x >= width - 2 and y >= height - 2:
                return True
            return False

        def place_blockers() -> None:
            target = max(6, int(width * height * 0.08))
            attempts = 0
            while len(blockers) < target and attempts < target * 20:
                attempts += 1
                coord = (self.random.randrange(0, width), self.random.randrange(0, height))
                if coord in blockers or is_reserved(coord):
                    continue
                blockers.append(coord)

        def seed_patch(tile_type: str, size: int) -> None:
            if size <= 0:
                return
            start = (self.random.randrange(0, width), self.random.randrange(0, height))
            frontier = [start]
            seen = {start}
            while frontier and size > 0:
                coord = frontier.pop(0)
                if coord in blockers:
                    continue
                tiles.setdefault(coord, {})["type"] = tile_type
                size -= 1
                x, y = coord
                neighbors = [
                    (x + 1, y),
                    (x - 1, y),
                    (x, y + 1),
                    (x, y - 1),
                ]
                self.random.shuffle(neighbors)
                for nxt in neighbors:
                    if nxt in seen:
                        continue
                    nx, ny = nxt
                    if 0 <= nx < width and 0 <= ny < height:
                        seen.add(nxt)
                        frontier.append(nxt)

        def place_hazards() -> None:
            hazard_names = ["spikes", "toxic_spikes", "sticky_web", "stealth_rock", "fire_hazards"]
            trap_names = ["trap"]
            target = self.random.randint(3, 6)
            attempts = 0
            while target > 0 and attempts < 120:
                attempts += 1
                coord = (self.random.randrange(0, width), self.random.randrange(0, height))
                if coord in blockers:
                    continue
                if is_reserved(coord) and self.random.random() < 0.7:
                    continue
                tile = tiles.setdefault(coord, {})
                if self.random.random() < 0.75:
                    hazard = self.random.choice(hazard_names)
                    layers = 1 + (1 if self.random.random() < 0.35 else 0)
                    hazard_map = dict(tile.get("hazards") or {})
                    hazard_map[hazard] = max(layers, int(hazard_map.get(hazard, 0) or 0))
                    tile["hazards"] = hazard_map
                else:
                    trap = self.random.choice(trap_names)
                    trap_map = dict(tile.get("traps") or {})
                    trap_map[trap] = max(1, int(trap_map.get(trap, 0) or 0))
                    tile["traps"] = trap_map
                target -= 1

        place_blockers()
        for _ in range(self.random.randint(2, 3)):
            seed_patch("water", self.random.randint(4, 8))
        for _ in range(self.random.randint(2, 3)):
            seed_patch("difficult", self.random.randint(4, 7))
        place_hazards()

        return GridSpec(
            width=width,
            height=height,
            scale=float(getattr(base_grid, "scale", 1.0)),
            blockers=blockers,
            tiles=tiles,
        )


__all__ = ["CsvRandomCampaignBuilder"]
