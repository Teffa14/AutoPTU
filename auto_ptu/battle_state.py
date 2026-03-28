"""Shared helpers for interactive battle sessions."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from . import ptu_engine
from .engine import MatchEngine


def format_move_event(
    label: str,
    attacker: ptu_engine.Combatant,
    defender: ptu_engine.Combatant,
    move: ptu_engine.Move,
    terrain: ptu_engine.Terrain,
    rng: random.Random,
) -> Dict[str, Any]:
    """Resolve a single move and present a text summary."""
    outcome = ptu_engine.resolve_hit(attacker, defender, move, terrain, rng)
    event: Dict[str, Any] = {
        "by": label.lower(),
        "attacker": attacker.mon.name,
        "target": defender.mon.name,
        "move": move.name,
        "hit": bool(outcome.get("hit")),
        "crit": bool(outcome.get("crit")),
        "damage": int(outcome.get("damage", 0)),
        "target_hp": defender.hp,
    }
    if not event["hit"]:
        event["text"] = f"{label}'s {attacker.mon.name} used {move.name} but missed!"
    else:
        text = f"{label}'s {attacker.mon.name} used {move.name}"
        if event["crit"]:
            text += " (CRIT!)"
        text += f" for {event['damage']} damage. {defender.mon.name} HP {defender.hp}/{defender.mon.max_hp()}"
        event["text"] = text
    return event


def _format_range_label(move: ptu_engine.Move) -> str:
    kind = move.range_kind or "Melee"
    value = move.range_value
    if value in ("", None, 0):
        return kind
    return f"{kind} {value}"


def _normalize_range_kind(kind: Optional[str]) -> str:
    if not kind:
        return "melee"
    return "".join(ch for ch in kind.lower() if ch.isalpha())


def _chebyshev_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _movement_allowance(combatant: ptu_engine.Combatant) -> int:
    """Derive a loose travel budget from the mon's Speed."""
    speed = int(getattr(combatant.mon, "spd", 6) or 6)
    return max(4, min(10, speed // 2 or 4))


def _move_payload(move: ptu_engine.Move, targeting: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "name": move.name,
        "type": move.type,
        "category": move.category,
        "db": move.db,
        "freq": move.freq,
        "range_kind": move.range_kind,
        "range_value": move.range_value,
        "range_text": _format_range_label(move),
        "description": move.effects_text,
    }
    if targeting:
        payload["targeting"] = targeting
    return payload


def _combatant_payload(combatant: ptu_engine.Combatant) -> Dict[str, Any]:
    mon = combatant.mon
    return {
        "name": mon.name,
        "species": mon.species,
        "hp": combatant.hp,
        "max_hp": mon.max_hp(),
        "types": list(mon.types),
        "stats": {
            "atk": mon.atk,
            "def": mon.def_,
            "spatk": mon.spatk,
            "spdef": mon.spdef,
            "spd": mon.spd,
            "hp_stat": mon.hp_stat,
        },
        "moves": [_move_payload(mv) for mv in mon.known_moves],
    }


@dataclass
class InteractiveBattleState:
    """State container for interactive grid play with lightweight initiative."""

    plan: Any
    matchup: Any
    engine: MatchEngine
    seed: Optional[int] = None
    log: List[Dict[str, Any]] = field(default_factory=list)
    winner: Optional[str] = None

    def __post_init__(self) -> None:
        self.grid = self.plan.grid
        self.terrain = self.engine.build_terrain(self.plan.weather)
        base_seed = self.seed or self.engine.seed_for_match(1)
        self.rng = random.Random(base_seed)
        self.status = "player-turn"
        self.tokens: List[Dict[str, Any]] = []
        self._token_lookup: Dict[str, Dict[str, Any]] = {}
        self.trainers: List[Dict[str, Any]] = []
        self._trainer_map: Dict[str, Dict[str, Any]] = {}
        self.turn_queue: List[str] = []
        self._movement_limits: Dict[str, int] = {}
        self._movement_used: Dict[str, bool] = {}
        self._current_trainer_id: Optional[str] = None
        self._turn_index: int = -1
        self._build_trainer_roster()
        self._initialize_turn_order()

    def _build_trainer_roster(self) -> None:
        used_positions: Set[Tuple[int, int]] = set()
        sides = self.matchup.sides_or_default()
        for side in sides:
            trainer_id = side.identifier or f"trainer-{len(self.trainers) + 1}"
            trainer_entry = {
                "id": trainer_id,
                "name": side.name or trainer_id.title(),
                "controller": side.controller or "ai",
                "team": side.team or side.controller or trainer_id,
                "pokemon": [],
            }
            self.trainers.append(trainer_entry)
            self._trainer_map[trainer_id] = trainer_entry
            self.turn_queue.append(trainer_id)
            for idx, spec in enumerate(side.pokemon):
                token_id = f"{trainer_id}-{idx + 1}"
                pos = self._starting_position(side, idx, used_positions)
                controller_label = side.controller.title() if side.controller else trainer_entry["name"]
                combatant = self.engine.build_combatant(
                    spec,
                    controller=controller_label,
                    pos=pos,
                    identifier=token_id,
                )
                used_positions.add((combatant.x, combatant.y))
                role = "player" if trainer_entry["controller"] == "player" else "foe"
                token_entry = {
                    "id": token_id,
                    "label": combatant.mon.name,
                    "role": role,
                    "trainer_id": trainer_id,
                    "team": trainer_entry["team"],
                    "controller": trainer_entry["controller"],
                    "combatant": combatant,
                    "color": self._color_for_team(role),
                }
                self.tokens.append(token_entry)
                self._token_lookup[token_id] = token_entry
                trainer_entry["pokemon"].append(token_id)
        if not self.tokens:
            raise ValueError("Matchup did not provide any combatants.")

    @staticmethod
    def _color_for_team(role: str) -> str:
        if role == "player":
            return "#4ade80"
        if role == "foe":
            return "#f87171"
        return "#60a5fa"

    def _starting_position(
        self, side: Any, index: int, occupied: Set[Tuple[int, int]]
    ) -> Tuple[int, int]:
        if index < len(side.start_positions):
            raw = side.start_positions[index]
            return self._clamp_to_grid((int(raw[0]), int(raw[1])))
        base = self.plan.default_you_start if side.controller == "player" else self.plan.default_foe_start
        candidate = self._clamp_to_grid((base[0], base[1] + index))
        while candidate in occupied:
            candidate = self._clamp_to_grid((candidate[0], candidate[1] + 1))
        return candidate

    def _clamp_to_grid(self, coord: Tuple[int, int]) -> Tuple[int, int]:
        width = getattr(self.grid, "width", 0)
        height = getattr(self.grid, "height", 0)
        x = coord[0]
        y = coord[1]
        if width:
            x = max(0, min(width - 1, x))
        if height:
            y = max(0, min(height - 1, y))
        return (x, y)

    def _initialize_turn_order(self) -> None:
        if not self.turn_queue:
            self.status = "finished"
            return
        preferred = next(
            (tid for tid in self.turn_queue if self._trainer_map[tid]["controller"] == "player" and self._active_token_for_trainer(tid)),
            None,
        )
        if preferred is None:
            preferred = next((tid for tid in self.turn_queue if self._active_token_for_trainer(tid)), None)
        if preferred is None:
            self.status = "finished"
            return
        self._turn_index = self.turn_queue.index(preferred)
        self._set_current_trainer(preferred)

    def _set_current_trainer(self, trainer_id: Optional[str]) -> None:
        self._current_trainer_id = trainer_id
        if trainer_id is None:
            self.status = "finished"
            return
        trainer = self._trainer_map.get(trainer_id)
        if not trainer:
            self.status = "finished"
            return
        self.status = "player-turn" if trainer["controller"] == "player" else "ai-turn"
        if self.status == "player-turn":
            token = self._active_token_for_trainer(trainer_id)
            if token:
                self._reset_movement_for_token(token["id"])

    def snapshot(self) -> Dict[str, Any]:
        player_token = self._active_player_token() or self._first_token_by_controller("player")
        foe_token = self._first_token_by_controller("foe")
        player_payload = self._combatant_snapshot(player_token) if player_token else {}
        foe_payload = self._combatant_snapshot(foe_token) if foe_token else {}
        return {
            "status": self.status,
            "winner": self.winner,
            "player": player_payload,
            "foe": foe_payload,
            "trainers": self._trainer_snapshots(),
            "turn": self._turn_snapshot(),
            "log": list(self.log),
            "weather": self.plan.weather,
            "matchup": self.matchup.label or "",
            "board": self._board_snapshot(),
        }

    def _trainer_snapshots(self) -> List[Dict[str, Any]]:
        snapshots: List[Dict[str, Any]] = []
        for trainer in self.trainers:
            active_token = self._active_token_for_trainer(trainer["id"])
            mons: List[Dict[str, Any]] = []
            for token_id in trainer["pokemon"]:
                token = self._token_lookup.get(token_id)
                if not token:
                    continue
                combatant = token["combatant"]
                mons.append(
                    {
                        "token_id": token_id,
                        "name": combatant.mon.name,
                        "hp": combatant.hp,
                        "max_hp": combatant.mon.max_hp(),
                        "active": active_token is not None and token_id == active_token["id"],
                    }
                )
            snapshots.append(
                {
                    "id": trainer["id"],
                    "name": trainer["name"],
                    "controller": trainer["controller"],
                    "team": trainer["team"],
                    "pokemon": mons,
                }
            )
        return snapshots

    def _turn_snapshot(self) -> Dict[str, Any]:
        trainer = self._trainer_map.get(self._current_trainer_id) if self._current_trainer_id else None
        token = self._active_token_for_trainer(self._current_trainer_id) if self._current_trainer_id else None
        return {
            "trainer_id": self._current_trainer_id,
            "controller": trainer["controller"] if trainer else None,
            "token_id": token["id"] if token else None,
        }

    def _combatant_snapshot(self, token: Dict[str, Any]) -> Dict[str, Any]:
        payload = _combatant_payload(token["combatant"])
        payload["token_id"] = token["id"]
        payload["trainer_id"] = token["trainer_id"]
        return payload

    def available_moves(self) -> Sequence[ptu_engine.Move]:
        token = self._active_player_token()
        if not token:
            return []
        return list(token["combatant"].mon.known_moves)

    def play_turn(self, move_name: str, target: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if self.status == "finished":
            return []
        trainer = self._trainer_map.get(self._current_trainer_id or "")
        if not trainer or trainer["controller"] != "player":
            raise ValueError("Hold on! It's not your turn.")
        actor_token = self._active_token_for_trainer(trainer["id"])
        if actor_token is None:
            raise ValueError("No trainer-controlled Pokémon available.")
        combatant = actor_token["combatant"]
        move = next((mv for mv in combatant.mon.known_moves if mv.name == move_name), None)
        if not move:
            raise ValueError(f"Move '{move_name}' not found on {combatant.mon.name}")
        targeting = self._move_targeting_payload(move, actor_token)
        defender_token = self._resolve_target_token(actor_token, targeting, target)
        if targeting["requires_target"] and defender_token is None:
            raise ValueError("Select a valid target inside the highlighted range.")
        if defender_token is None:
            raise ValueError("No valid targets remain.")
        events: List[Dict[str, Any]] = []
        event = format_move_event(trainer["name"], combatant, defender_token["combatant"], move, self.terrain, self.rng)
        events.append(event)
        self.log.append(event)
        if self._check_for_winner():
            return events
        self._advance_turn()
        events.extend(self._run_ai_turns_until_player())
        return events

    def _resolve_target_token(
        self, actor_token: Dict[str, Any], targeting: Dict[str, Any], target: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        allowed = {(tile["x"], tile["y"]) for tile in targeting["tiles"]}
        if target and target.get("token_id"):
            token = self._token_lookup.get(target["token_id"])
            if token and token["combatant"].hp > 0:
                coord = (token["combatant"].x, token["combatant"].y)
                if not targeting["requires_target"] or coord in allowed:
                    return token
        coord = self._resolve_target_coordinate(target, targeting)
        if coord is not None:
            if targeting["requires_target"] and coord not in allowed:
                return None
            token = self._token_at_coordinate(coord, exclude=actor_token["id"])
            if token:
                return token
        fallback = self._default_target_for_token(actor_token)
        if fallback is None:
            return None
        if not targeting["requires_target"]:
            return fallback
        coord = (fallback["combatant"].x, fallback["combatant"].y)
        return fallback if coord in allowed else None

    def _run_ai_turns_until_player(self) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        while self.status == "ai-turn" and self._current_trainer_id:
            trainer = self._trainer_map.get(self._current_trainer_id)
            if not trainer:
                break
            token = self._active_token_for_trainer(trainer["id"])
            if token is None:
                self._advance_turn()
                continue
            event = self._execute_ai_turn(trainer, token)
            if event:
                events.append(event)
                self.log.append(event)
                if self._check_for_winner():
                    break
            self._advance_turn()
        return events

    def _execute_ai_turn(self, trainer: Dict[str, Any], token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        defender = self._default_target_for_token(token)
        if defender is None:
            return None
        move = ptu_engine.best_move_by_ev(token["combatant"], defender["combatant"])
        return format_move_event(trainer["name"], token["combatant"], defender["combatant"], move, self.terrain, self.rng)

    def _advance_turn(self) -> None:
        if not self.turn_queue:
            self._set_current_trainer(None)
            return
        for _ in range(len(self.turn_queue)):
            self._turn_index = (self._turn_index + 1) % len(self.turn_queue)
            trainer_id = self.turn_queue[self._turn_index]
            if self._active_token_for_trainer(trainer_id):
                self._set_current_trainer(trainer_id)
                return
        self._set_current_trainer(None)

    def _check_for_winner(self) -> bool:
        teams = self._living_teams()
        if len(teams) <= 1:
            if not teams:
                self.winner = None
            else:
                team = next(iter(teams))
                self.winner = "player" if self._team_has_player(team) else team
            self.status = "finished"
            return True
        return False

    def _living_teams(self) -> Set[str]:
        teams: Set[str] = set()
        for token in self.tokens:
            if token["combatant"].hp > 0:
                team_id = token.get("team") or token.get("trainer_id")
                teams.add(team_id)
        return teams

    def _team_has_player(self, team: str) -> bool:
        for trainer in self.trainers:
            team_id = trainer.get("team") or trainer.get("id")
            if team_id == team and trainer["controller"] == "player":
                return True
        return False

    def _active_token_for_trainer(self, trainer_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if trainer_id is None:
            return None
        trainer = self._trainer_map.get(trainer_id)
        if not trainer:
            return None
        for token_id in trainer["pokemon"]:
            token = self._token_lookup.get(token_id)
            if token and token["combatant"].hp > 0:
                return token
        return None

    def _active_player_token(self) -> Optional[Dict[str, Any]]:
        trainer = self._trainer_map.get(self._current_trainer_id or "")
        if not trainer or trainer["controller"] != "player":
            return None
        return self._active_token_for_trainer(trainer["id"])

    def _first_token_by_controller(self, role: str) -> Optional[Dict[str, Any]]:
        for token in self.tokens:
            if token["role"] == role and token["combatant"].hp > 0:
                return token
        return None

    def _default_target_for_token(self, actor_token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for token in self.tokens:
            if token["team"] != actor_token["team"] and token["combatant"].hp > 0:
                return token
        return None

    def _token_at_coordinate(self, coord: Tuple[int, int], exclude: Optional[str] = None) -> Optional[Dict[str, Any]]:
        for token in self.tokens:
            if exclude and token["id"] == exclude:
                continue
            combatant = token["combatant"]
            if (combatant.x, combatant.y) == coord and combatant.hp > 0:
                return token
        return None

    def _board_snapshot(self) -> Dict[str, Any]:
        grid = self.plan.grid
        blockers = [{"x": int(a), "y": int(b)} for (a, b) in grid.blockers]
        tiles = {f"{key[0]},{key[1]}": value for key, value in grid.tiles.items()}
        tokens = []
        for token in self.tokens:
            combatant = token["combatant"]
            tokens.append(
                {
                    "id": token["id"],
                    "label": token["label"],
                    "role": token["role"],
                    "trainer_id": token["trainer_id"],
                    "x": combatant.x,
                    "y": combatant.y,
                    "color": token.get("color"),
                    "hp": combatant.hp,
                    "max_hp": combatant.mon.max_hp(),
                }
            )
        movement = {"steps": 0, "used": False}
        active = self._active_player_token()
        if active:
            token_id = active["id"]
            movement = {
                "steps": self._movement_limits.get(token_id, _movement_allowance(active["combatant"])),
                "used": self._movement_used.get(token_id, False),
            }
        return {
            "width": grid.width,
            "height": grid.height,
            "blockers": blockers,
            "tiles": tiles,
            "tokens": tokens,
            "movement": movement,
        }

    def move_token(self, token_id: str, target: Tuple[int, int]) -> None:
        if self.status != "player-turn":
            raise ValueError("Hold on! It's not your turn to reposition.")
        trainer = self._trainer_map.get(self._current_trainer_id or "")
        if not trainer or trainer["controller"] != "player":
            raise ValueError("Only trainer-controlled Pokémon can be moved.")
        token = self._token_lookup.get(token_id)
        if not token or token["trainer_id"] != trainer["id"]:
            raise ValueError("Unknown combatant.")
        grid = self.plan.grid
        x, y = target
        if not (0 <= x < grid.width and 0 <= y < grid.height):
            raise ValueError("That tile is outside the arena.")
        if (x, y) in grid.blockers:
            raise ValueError("That tile is blocked.")
        combatant = token["combatant"]
        limit = self._movement_limits.get(token_id, _movement_allowance(combatant))
        if self._movement_used.get(token_id):
            raise ValueError("You've already spent your movement this turn.")
        origin = (combatant.x, combatant.y)
        distance = _chebyshev_distance(origin, target)
        if distance > limit:
            raise ValueError(f"{combatant.mon.name} can only move {limit} tiles this turn.")
        combatant.x = x
        combatant.y = y
        self._movement_limits[token_id] = limit
        self._movement_used[token_id] = True

    def _reset_movement_for_token(self, token_id: str) -> None:
        token = self._token_lookup.get(token_id)
        if not token:
            return
        combatant = token["combatant"]
        self._movement_limits[token_id] = _movement_allowance(combatant)
        self._movement_used[token_id] = False
    def _range_distance(self, move: ptu_engine.Move, normalized_kind: Optional[str] = None) -> int:
        kind = normalized_kind or _normalize_range_kind(move.range_kind)
        defaults = {
            "melee": 1,
            "ranged": 6,
            "burst": 2,
            "closeblast": 2,
            "cone": 3,
            "line": 6,
        }
        if kind in {"self", "field"}:
            return 0
        if move.range_value is not None:
            return max(int(move.range_value), 1)
        return defaults.get(kind, 3)

    def _range_tiles(self, move: ptu_engine.Move, origin: Tuple[int, int]) -> List[Tuple[int, int]]:
        kind = _normalize_range_kind(move.range_kind)
        grid = self.plan.grid
        ox, oy = origin
        tiles: Set[Tuple[int, int]] = set()
        if kind in {"self"}:
            if 0 <= ox < grid.width and 0 <= oy < grid.height:
                tiles.add((ox, oy))
            return sorted(tiles)
        if kind in {"field", "arena", "global"}:
            for y in range(grid.height):
                for x in range(grid.width):
                    tiles.add((x, y))
            return sorted(tiles)
        distance = self._range_distance(move, kind)
        if kind == "line":
            for step in range(1, distance + 1):
                for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
                    x = ox + dx
                    y = oy + dy
                    if 0 <= x < grid.width and 0 <= y < grid.height:
                        tiles.add((x, y))
            return sorted(tiles)
        for x in range(ox - distance, ox + distance + 1):
            for y in range(oy - distance, oy + distance + 1):
                if not (0 <= x < grid.width and 0 <= y < grid.height):
                    continue
                if kind == "melee" and (x, y) == (ox, oy):
                    continue
                if _chebyshev_distance((ox, oy), (x, y)) > distance:
                    continue
                tiles.add((x, y))
        return sorted(tiles)

    def _move_targeting_payload(self, move: ptu_engine.Move, actor_token: Dict[str, Any]) -> Dict[str, Any]:
        origin = (actor_token["combatant"].x, actor_token["combatant"].y)
        tiles = self._range_tiles(move, origin)
        coords = {(x, y) for (x, y) in tiles}
        normalized_kind = _normalize_range_kind(move.range_kind)
        requires_target = normalized_kind not in {"self", "field"}
        payload = {
            "shape": normalized_kind,
            "origin": {"x": origin[0], "y": origin[1]},
            "tiles": [{"x": x, "y": y} for (x, y) in tiles],
            "requires_target": requires_target,
            "allow_tiles": requires_target,
            "allow_tokens": requires_target,
            "valid_tokens": [
                token["id"]
                for token in self.tokens
                if token["id"] != actor_token["id"]
                and (token["combatant"].x, token["combatant"].y) in coords
            ],
            "summary": self._range_summary(move),
            "max_distance": self._range_distance(move, normalized_kind),
        }
        if not requires_target:
            payload["allow_tiles"] = False
            payload["allow_tokens"] = normalized_kind == "self"
        return payload

    @staticmethod
    def _range_summary(move: ptu_engine.Move) -> str:
        label = _format_range_label(move)
        kind = _normalize_range_kind(move.range_kind)
        extra = {
            "melee": "Adjacent tiles.",
            "ranged": "Pick any tile within range.",
            "burst": "Explodes around you.",
            "closeblast": "Sweeps nearby tiles.",
            "cone": "Fans outward from you.",
            "line": "Extends straight from you.",
            "field": "Covers the arena.",
            "self": "Only affects your PokAcmon.",
        }.get(kind, "Targets inside range.")
        return f"{label} - {extra}"

    def _resolve_target_coordinate(
        self, target: Optional[Dict[str, Any]], targeting: Dict[str, Any]
    ) -> Optional[Tuple[int, int]]:
        if not target:
            return None
        token_id = target.get("token_id")
        if token_id:
            token = next((entry for entry in self.tokens if entry["id"] == token_id), None)
            if token:
                return (int(token["combatant"].x), int(token["combatant"].y))
        x = target.get("x")
        y = target.get("y")
        if x is None or y is None:
            return None
        return (int(x), int(y))


__all__ = ["InteractiveBattleState", "format_move_event"]
