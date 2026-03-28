# ptu_engine.py  —  Self-contained PTU battle engine for Discord play (no server needed)
# Usage in Code Interpreter:
#  1) Upload your two sheets (or paste JSON with mons).
#  2) from ptu_engine import *
#  3) mons = load_party_from_excel("SheetA.xlsx","SheetB.xlsx")   # or build_mons_from_dict(...)
#  4) res = expectimax_battle(mons['you'], mons['foe'], terrain=Terrain.rain(), depth=6, ruleset="ptu_core_1_05")
#  5) print(res["discord_post"])
#
# Optional: Upload PDFs (CoreRulebook.pdf, Pokedex 1.05.pdf, Erratas.pdf, Super Pokémon Online Player's Guide 2.0.pdf)
# for auto-citations in outputs.

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
import random, math, json, re, os
from pathlib import Path
from collections import deque, defaultdict

############################
# Rules & Tables (PTU 1.05)
############################

# Damage Base (DB) → dice + flat. (PTU 1.05)
DB_TABLE = {
    2:(1,6,3), 3:(1,6,5), 4:(1,8,6), 5:(1,8,8),
    6:(2,6,8), 7:(2,6,10), 8:(2,8,10), 9:(2,10,10),
    10:(3,8,10), 11:(3,10,10), 12:(3,12,10),
    13:(4,10,10), 14:(4,10,15), 15:(4,10,20),
}

def db_to_dice(db:int)->Tuple[int,int,int]:
    if db in DB_TABLE: return DB_TABLE[db]
    # Beyond 15: +5 flat per step (common table extension)
    n,s,p = DB_TABLE[15]; return (n,s,p + 5*(db-15))

# Type chart (step system → multiplier: -2=0.25, -1=0.5, 0=1, +1=1.5, ≥+2=2.0)
TYPE_STEPS: Dict[Tuple[str,str], int] = {}
def _add(atk, defs, step): 
    for d in defs: TYPE_STEPS[(atk,d)] = step

# Weak
_add("Fire",["Grass","Ice","Bug","Steel"],+1)
_add("Water",["Fire","Ground","Rock"],+1)
_add("Electric",["Water","Flying"],+1)
_add("Grass",["Water","Ground","Rock"],+1)
_add("Ice",["Grass","Ground","Flying","Dragon"],+1)
_add("Fighting",["Normal","Ice","Rock","Dark","Steel"],+1)
_add("Poison",["Grass","Fairy"],+1)
_add("Ground",["Fire","Electric","Poison","Rock","Steel"],+1)
_add("Flying",["Grass","Fighting","Bug"],+1)
_add("Psychic",["Fighting","Poison"],+1)
_add("Bug",["Grass","Psychic","Dark"],+1)
_add("Rock",["Fire","Ice","Flying","Bug"],+1)
_add("Ghost",["Psychic","Ghost"],+1)
_add("Dragon",["Dragon"],+1)
_add("Dark",["Psychic","Ghost"],+1)
_add("Steel",["Ice","Rock","Fairy"],+1)
_add("Fairy",["Fighting","Dragon","Dark"],+1)
# Resist
_add("Fire",["Fire","Water","Rock","Dragon"],-1)
_add("Water",["Water","Grass","Dragon"],-1)
_add("Electric",["Electric","Grass","Dragon"],-1)
_add("Grass",["Fire","Grass","Poison","Flying","Bug","Dragon","Steel"],-1)
_add("Ice",["Fire","Water","Ice","Steel"],-1)
_add("Fighting",["Poison","Flying","Psychic","Bug","Fairy"],-1)
_add("Poison",["Poison","Ground","Rock","Ghost"],-1)
_add("Ground",["Grass","Bug"],-1)
_add("Flying",["Electric","Rock","Steel"],-1)
_add("Psychic",["Psychic","Steel"],-1)
_add("Bug",["Fire","Fighting","Poison","Flying","Ghost","Steel","Fairy"],-1)
_add("Rock",["Fighting","Ground","Steel"],-1)
_add("Ghost",["Dark"],-1)
_add("Dragon",["Steel"],-1)
_add("Dark",["Fighting","Dark","Fairy"],-1)
_add("Steel",["Fire","Water","Electric","Steel"],-1)
_add("Fairy",["Fire","Poison","Steel"],-1)
# Immunities
_add("Normal",["Ghost"],0)
_add("Fighting",["Ghost"],0)
_add("Poison",["Steel"],0)
_add("Ground",["Flying"],0)
_add("Psychic",["Dark"],0)
_add("Ghost",["Normal"],0)
_add("Electric",["Ground"],0)
_add("Dragon",["Fairy"],0)

def type_multiplier(move_type:str, target_types:List[str])->float:
    step=0
    for t in target_types:
        s=TYPE_STEPS.get((move_type,t))
        if s == 0: return 0.0
        step += 0 if s is None else s
    return {-2:0.25,-1:0.5,0:1.0,1:1.5}.get(step, 2.0 if step>=2 else 1.0)

############################
# Data Structures
############################

@dataclass
class Capability:
    name:str; value:int=0

@dataclass
class Item:
    name:str; slot:str="Held"; effects:List[str]=field(default_factory=list)

@dataclass
class AbilityHook:
    when:str; effect:str

@dataclass
class Ability:
    name:str; hooks:List[AbilityHook]=field(default_factory=list)

@dataclass
class Status:
    name:str; kind:str="Persistent"  # or Volatile
    effects:List[str]=field(default_factory=list)  # e.g., "physical_mult:0.5", "spd_mult:0.5"
    duration:str="save_ends"

@dataclass
class Move:
    name:str; type:str; category:str; db:int
    ac:Optional[int]=2
    range_kind:str="Melee"   # Melee|Ranged|CloseBlast|Burst|Cone|Line|Field|Self
    range_value:Optional[int]=None
    keywords:List[str]=field(default_factory=list)  # e.g., ["Priority"]
    priority:int=0
    crit_range:int=20
    freq:str="EOT"
    effects_text:str=""

@dataclass
class TrainerFeature:
    name:str; when:str; effect:str  # simple hook

@dataclass
class Pokemon:
    name:str; species:str; level:int; types:List[str]
    hp_stat:int; atk:int; def_:int; spatk:int; spdef:int; spd:int
    accuracy_cs:int=0
    evasion_bonus_phys:int=0; evasion_bonus_spec:int=0; evasion_bonus_spd:int=0
    capabilities:List[Capability]=field(default_factory=list)
    abilities:List[Ability]=field(default_factory=list)
    items:List[Item]=field(default_factory=list)
    statuses:List[Status]=field(default_factory=list)
    trainer_features:List[TrainerFeature]=field(default_factory=list)
    known_moves:List[Move]=field(default_factory=list)

    def max_hp(self)->int:
        # Core PTU: Total HP = Level + 3×HP + 10
        return self.level + 3*self.hp_stat + 10

    def phys_evasion(self)->int:
        return (self.def_//5) + self.evasion_bonus_phys
    def spec_evasion(self)->int:
        return (self.spdef//5) + self.evasion_bonus_spec
    def speed_evasion(self)->int:
        return (self.spd//5) + self.evasion_bonus_spd

@dataclass
class Combatant:
    id:str; controller:str; mon:Pokemon
    x:int=0; y:int=0
    hp:int=-1; injuries:int=0
    temp_mods:List[str]=field(default_factory=list)

    def init_hp(self): 
        if self.hp<0: self.hp=self.mon.max_hp()

@dataclass
class Grid:
    width:int; height:int; scale:float=1.0
    blockers:List[Tuple[int,int]] = field(default_factory=list)

@dataclass
class Terrain:
    name:str="Standard"
    weather:Optional[str]=None
    modifiers:List[str]=field(default_factory=list)  # e.g., "electric_db:+1"
    tiles:Dict[Tuple[int,int], str]=field(default_factory=dict)  # (x,y)->"difficult,water,cover2"

    @staticmethod
    def rain():
        return Terrain(name="Rain", weather="Rain", modifiers=["electric_db:+1","fire_db:-1"])

############################
# Utility: PDF citations (if uploaded)
############################

_BASE_PDFS = [
    "Super PokAcmon Online Player's Guide 2.0.pdf",
    "PTU Downloads Megadoc.pdf",
    "CoreRulebook.pdf",
    "Pokedex 1.05.pdf",
    "Erratas.pdf",
]

try:
    from .config import FILES_DIR as _FILES_DIR
except Exception:  # pragma: no cover - fallback for standalone usage
    _FILES_DIR = Path(__file__).resolve().parent.parent / "files"
else:
    _FILES_DIR = Path(_FILES_DIR)

_RULEBOOK_PDFS: List[str] = []
_rulebook_dir = _FILES_DIR / "rulebook"
if _rulebook_dir.exists():
    for pdf in _rulebook_dir.glob("*.pdf"):
        _RULEBOOK_PDFS.append(str(pdf))

PDFS = _BASE_PDFS + _RULEBOOK_PDFS


def find_quote(query:str, max_hits=2)->List[str]:
    hits=[]
    try:
        try:
            from pypdf import PdfReader
        except Exception:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                import PyPDF2
            PdfReader = PyPDF2.PdfReader
    except Exception:
        return hits
    for fname in PDFS:
        if not os.path.exists(fname): continue
        try:
            with open(fname,"rb") as f:
                r=PdfReader(f)
                for i,pg in enumerate(r.pages):
                    txt=pg.extract_text() or ""
                    if re.search(query, txt, flags=re.I):
                        snippet=" ".join(re.findall(rf".{{0,80}}{re.escape(query)}.{{0,80}}", txt, flags=re.I))
                        hits.append(f"{fname} p.{i+1}: {snippet[:180]}…")
                        if len(hits)>=max_hits: return hits
        except Exception:
            continue
    return hits

############################
# Mechanics
############################

def stab_db(move:Move, mon:Pokemon)->int:
    return move.db + (2 if move.type in mon.types else 0)

def acc_hit_crit(att:Pokemon, dfd:Pokemon, move:Move, rng:random.Random)->Tuple[int,bool,bool,int]:
    if move.ac is None:
        r = rng.randint(1,20)
        return r, True, (r>=move.crit_range), 1  # threshold dummy
    ev = dfd.spec_evasion() if move.category=="Special" else dfd.phys_evasion()
    needed = move.ac + ev - att.accuracy_cs
    roll = rng.randint(1,20)
    hit = True if (roll==20 or roll >= needed) else False
    crit = hit and (roll>=move.crit_range)
    return roll, hit, crit, needed

def apply_status_mods(att:Pokemon, dfd:Pokemon, move:Move, base:int)->int:
    mult=1.0
    # Burn halves Physical damage from the burned attacker
    if any(s.name.lower()=="burned" for s in att.statuses) and move.category=="Physical":
        mult *= 0.5
    # Light Screen/Reflect could be modeled here if present via temp_mods
    return int(math.floor(base*mult+1e-6))

def ability_item_hooks(mon:Pokemon, when:str, ctx:Dict[str,Any]):
    # Minimal demo hooks; extend as needed
    for ab in mon.abilities:
        for h in ab.hooks:
            if h.when==when:
                if h.effect.startswith("immune:"):
                    ctx.setdefault("immune_types",set()).add(h.effect.split(":",1)[1])
                if h.effect.startswith("add_flat:"):
                    amt=int(h.effect.split(":",1)[1].split(";")[0]); ctx["flat"] = ctx.get("flat",0)+amt
    for it in mon.items:
        for eff in it.effects:
            if when=="before_damage" and eff.startswith("special_flat:+") and ctx.get("category")=="Special":
                ctx["flat"]=ctx.get("flat",0)+int(eff.split("+")[1])

def calc_damage(att:Pokemon, dfd:Pokemon, move:Move, crit:bool, terrain:Terrain, rng:random.Random)->Dict[str,Any]:
    # Immunities via abilities (e.g., Volt Absorb as "immune:Electric")
    ctx={"category":move.category}
    ability_item_hooks(dfd, "on_targeted", ctx)
    if "immune_types" in ctx and move.type in ctx["immune_types"]:
        return {"damage":0,"why":"immunity (ability)","type_mult":0.0,"stab_db":stab_db(move,att)}
    # DB + STAB (+2 DB)
    sdb = stab_db(move, att)
    n,s,p = db_to_dice(sdb)
    dice = sum(rng.randint(1,s) for _ in range(n)) + p
    if crit: dice += sum(rng.randint(1,s) for _ in range(n))  # crit adds the damage dice again
    atk = att.atk if move.category=="Physical" else att.spatk
    dfs = dfd.def_ if move.category=="Physical" else dfd.spdef
    base = max(0, dice + atk - dfs)

    # Terrain/weather DB mods (e.g., Rain +1 Elec DB)
    db_bonus = 0
    for m in terrain.modifiers:
        if m.endswith("_db:+1") and move.type.lower().startswith(m.split("_db:+1")[0]):
            db_bonus += 1
        if m.endswith("_db:-1") and move.type.lower().startswith(m.split("_db:-1")[0]):
            db_bonus -= 1
    if db_bonus:
        n2,s2,p2 = db_to_dice(sdb+db_bonus)
        # approximate: +5 per DB step after dice expectation; simple flat adjust
        base += ( (n2*(s2+1)/2 + p2) - (n*(s+1)/2 + p) )

    # Item/Ability flats
    hook_ctx={"category":move.category}
    ability_item_hooks(att,"before_damage",hook_ctx)
    flat = hook_ctx.get("flat",0)

    # Status multipliers (Burn etc.)
    base = apply_status_mods(att, dfd, move, int(round(base+flat)))

    # Type multiplier
    tmult = type_multiplier(move.type, dfd.types)
    if tmult==0.0: 
        return {"damage":0,"why":"type immunity","type_mult":0.0,"stab_db":sdb}

    dmg = int(math.floor(base * tmult + 1e-6))
    return {"damage":max(0,dmg),"type_mult":tmult,"stab_db":sdb}

############################
# Range, Movement, Terrain
############################

def manhattan(a:Tuple[int,int], b:Tuple[int,int])->int:
    return abs(a[0]-b[0])+abs(a[1]-b[1])

def pathfind(grid:Grid, terrain:Terrain, start:Tuple[int,int], goal:Tuple[int,int], overland:int)->Tuple[bool,List[Tuple[int,int]],int]:
    # Simple BFS with difficult terrain costing 2
    W,H = grid.width, grid.height
    blocks=set(grid.blockers)
    get_cost=lambda x,y: 2 if "difficult" in terrain.tiles.get((x,y),"") else 1
    q=deque([(start,0,[])])
    seen={(start,0)}
    best=None
    while q:
        (x,y),cost,path = q.popleft()
        if (x,y)==goal:
            best=(True,path+[(x,y)],cost); break
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx,ny = x+dx, y+dy
            if not (0<=nx<W and 0<=ny<H): continue
            if (nx,ny) in blocks: continue
            step=get_cost(nx,ny)
            nc=cost+step
            if nc>overland: continue
            key=((nx,ny),nc)
            if key in seen: continue
            seen.add(key)
            q.append(((nx,ny),nc,path+[(x,y)]))
    if best is None: return (False,[],0)
    ok, path, cost = best
    return ok, path, cost

def check_range(grid:Grid, attacker_xy:Tuple[int,int], targets:List[Tuple[int,int]], move:Move)->Dict[str,Any]:
    # Minimal legality: Melee (adjacent), Ranged N (distance<=N), AoE shapes simplified to radius/length checks
    out={"legal":False,"targets":[],"notes":""}
    if move.range_kind=="Melee":
        for t in targets:
            if manhattan(attacker_xy,t)==1:
                out["legal"]=True; out["targets"].append(t)
    elif move.range_kind=="Ranged":
        maxr = move.range_value or 6
        for t in targets:
            if manhattan(attacker_xy,t)<=maxr:
                out["legal"]=True; out["targets"].append(t)
    else:
        # Simplified shapes; refine as needed
        maxr = move.range_value or 3
        for t in targets:
            if manhattan(attacker_xy,t)<=maxr:
                out["legal"]=True; out["targets"].append(t)
        out["notes"]="AoE simplified"
    return out

############################
# Turn, Priority, Initiative
############################

def initiative_value(cbt:Combatant)->int:
    # Simple: SPD governs; add temp mods or features here
    return cbt.mon.spd

def accuracy_roll(att:Combatant, dfd:Combatant, move:Move, rng)->Dict[str,Any]:
    r,hit,crit,need = acc_hit_crit(att.mon, dfd.mon, move, rng)
    return {"roll":r,"hit":hit,"crit":crit,"threshold":need}

def resolve_hit(att:Combatant, dfd:Combatant, move:Move, terrain:Terrain, rng)->Dict[str,Any]:
    acc = accuracy_roll(att, dfd, move, rng)
    if not acc["hit"]:
        return {"hit":False,"crit":False,"damage":0,"acc":acc}
    dmg = calc_damage(att.mon, dfd.mon, move, acc["crit"], terrain, rng)
    dfd.hp = max(0, dfd.hp - dmg["damage"])
    return {"hit":True,"crit":acc["crit"],"damage":dmg["damage"],"acc":acc,"type_mult":dmg.get("type_mult",1.0),"stab_db":dmg.get("stab_db",move.db)}

def discord_turn_post(att:Combatant, dfd:Combatant, move:Move, outcome:Dict[str,Any], extra_notes:str="", citations:List[str]=None)->str:
    p = []
    p.append(f"**Turn – {att.mon.name} (Init {initiative_value(att)})**")
    rng_desc = f"{move.range_kind} {move.range_value}" if move.range_kind=="Ranged" else move.range_kind
    p.append(f"Action: {move.name} @ {dfd.mon.name} ({rng_desc}) • {move.freq}")
    acc = outcome["acc"]; crit_note = " (Crit)" if acc.get("crit") else ""
    p.append(f"Accuracy: d20 vs AC{move.ac} – Evasion ⇒ {acc['roll']} → {'Hit' if acc['hit'] else 'Miss'}{crit_note}")
    if outcome["hit"]:
        p.append(f"Damage: DB{move.db} → STAB {('+2 DB' if move.type in att.mon.types else '—')} → **{outcome['damage']}** (×{outcome.get('type_mult',1.0)})")
        p.append(f"{dfd.mon.name} HP: {dfd.hp}/{dfd.mon.max_hp()}")
    if extra_notes: p.append(f"Notes: {extra_notes}")
    if citations:
        for c in citations[:2]:
            p.append(f"Ref: {c}")
    return "\n".join(p)

############################
# Expectimax & Monte Carlo
############################

def expected_damage(att:Pokemon, dfd:Pokemon, move:Move)->float:
    # Approx EV: expected dice + stats, crit adds dice again weighted by crit chance
    # Hit probability:
    if move.ac is None:
        p_hit=1.0; p_crit= (21-move.crit_range)/20.0
    else:
        ev = dfd.spec_evasion() if move.category=="Special" else dfd.phys_evasion()
        need = move.ac + ev - att.accuracy_cs
        hit=0; crit=0
        for r in range(1,21):
            if r==20 or r>=need:
                hit+=1
                if r>=move.crit_range: crit+=1
        p_hit=hit/20.0; p_crit=crit/20.0
    db = stab_db(move, att)
    n,s,p = db_to_dice(db)
    exp_dice = n*(s+1)/2 + p
    atk = att.atk if move.category=="Physical" else att.spatk
    dfs = dfd.def_ if move.category=="Physical" else dfd.spdef
    base = max(0.0, exp_dice + atk - dfs)
    tmult = type_multiplier(move.type, dfd.types)
    if tmult==0.0: return 0.0
    exp_on_hit = base*tmult + (n*(s+1)/2)*tmult*(p_crit/max(p_hit,1e-9))  # extra dice on crit
    return p_hit*exp_on_hit


_PHASE_TURN_LIMITS: Dict[int, int] = {1: 2, 2: 2}
_SETUP_TOKENS: Tuple[str, ...] = (
    "set-up", "setup", "set up", "boost", "raise", "screen", "guard", "protect",
    "barrier", "fortify", "field", "zone", "zoning", "cover", "shield", "aura",
    "defend", "buff",
)
_SWAP_TOKENS: Tuple[str, ...] = (
    "switch", "swap", "draw in", "pull", "push", "redirect", "force", "trip",
    "accuracy", "miss", "burn", "poison", "paral", "sleep", "confus", "flinch",
    "drain", "resource", "distract",
)
_STATUS_TOKENS: Tuple[str, ...] = ("burn", "poison", "paral", "sleep", "confus", "flinch", "stun")
_AI_CONTROLLERS: Set[str] = {"ai", "foe", "enemy"}


def _normalize_move_text(move:Move)->str:
    parts = [move.name or "", move.effects_text or "", move.range_kind or "", move.freq or ""]
    return " ".join(parts).lower()


def _move_keywords(move:Move)->Set[str]:
    return {str(keyword).strip().lower() for keyword in move.keywords if keyword}


def _has_tokens(text:str, keywords:Set[str], tokens:Tuple[str,...])->bool:
    for token in tokens:
        if token in keywords:  # keyword matches first to avoid false positives
            return True
        if token in text:
            return True
    return False


def _calc_setup_score(text:str, keywords:Set[str], move:Move)->float:
    score = 0.0
    if _has_tokens(text, keywords, _SETUP_TOKENS):
        score += 1.0
    if move.category == "Status":
        score += 0.4
    return score


def _calc_swap_score(text:str, keywords:Set[str], move:Move)->float:
    score = 0.0
    if _has_tokens(text, keywords, _SWAP_TOKENS):
        score += 1.0
    if move.category == "Status":
        score += 0.4
    if _has_tokens(text, keywords, _STATUS_TOKENS):
        score += 0.35
    return score


def _read_phase_state(temp_mods:List[str])->Tuple[int, int]:
    phase = 1
    turns = 0
    for entry in temp_mods:
        if entry.startswith("ai_phase:"):
            try:
                phase = max(1, min(3, int(entry.split(":",1)[1])))
            except Exception:
                continue
        elif entry.startswith("ai_phase_turns:"):
            try:
                turns = max(0, int(entry.split(":",1)[1]))
            except Exception:
                continue
    return phase, turns


def _write_phase_state(temp_mods:List[str], phase:int, turns:int)->None:
    filtered = [
        entry
        for entry in temp_mods
        if not entry.startswith("ai_phase:") and not entry.startswith("ai_phase_turns:")
    ]
    filtered.append(f"ai_phase:{phase}")
    filtered.append(f"ai_phase_turns:{turns}")
    temp_mods[:] = filtered


def _is_ai_controller(controller:Optional[str])->bool:
    if not controller:
        return False
    return controller.strip().lower() in _AI_CONTROLLERS


def best_move_by_ev(att:Combatant, dfd:Combatant)->Move:
    moves = att.mon.known_moves
    if not moves:
        raise ValueError("No known moves available for attacker.")
    if not _is_ai_controller(att.controller):
        return max(moves, key=lambda m: expected_damage(att.mon, dfd.mon, m))

    phase, turns = _read_phase_state(att.temp_mods)
    phase = max(1, min(3, phase))
    moves_context = []
    for move in moves:
        ed = expected_damage(att.mon, dfd.mon, move)
        text = _normalize_move_text(move)
        keywords = _move_keywords(move)
        setup_score = _calc_setup_score(text, keywords, move)
        swap_score = _calc_swap_score(text, keywords, move)
        moves_context.append(
            {
                "move": move,
                "ed": ed,
                "setup": setup_score,
                "swap": swap_score,
            }
        )

    phase_candidates = {
        1: sorted(
            (entry for entry in moves_context if entry["setup"] >= 0.6),
            key=lambda entry: (-entry["setup"], -entry["ed"], entry["move"].name or ""),
        ),
        2: sorted(
            (entry for entry in moves_context if entry["swap"] >= 0.6),
            key=lambda entry: (-entry["swap"], -entry["ed"], entry["move"].name or ""),
        ),
        3: sorted(
            moves_context,
            key=lambda entry: (-entry["ed"], entry["move"].name or ""),
        ),
    }

    while phase < 3 and not phase_candidates[phase]:
        phase += 1
        turns = 0

    candidates = phase_candidates.get(phase) or phase_candidates[3]
    chosen_entry = candidates[0]
    chosen_move = chosen_entry["move"]

    turns += 1
    limit = _PHASE_TURN_LIMITS.get(phase)
    if limit and turns >= limit and phase < 3:
        phase = min(3, phase + 1)
        turns = 0

    _write_phase_state(att.temp_mods, phase, turns)
    return chosen_move

def expectimax_battle(you:Combatant, foe:Combatant, terrain:Terrain, grid:Grid=None, depth:int=6, seed:int=1337, ruleset:str="ptu_core_1_05")->Dict[str,Any]:
    """Return best turn-1 action and principal variation under perfect play (expected values)."""
    rng = random.Random(seed)
    you.init_hp(); foe.init_hp()
    # Principal variation collector
    pv=[]
    A = Combatant(you.id, you.controller, you.mon, you.x, you.y, you.hp, you.injuries, you.temp_mods.copy())
    B = Combatant(foe.id, foe.controller, foe.mon, foe.x, foe.y, foe.hp, foe.injuries, foe.temp_mods.copy())
    to_move = "A"
    for d in range(depth):
        if A.hp<=0 or B.hp<=0: break
        if to_move=="A":
            mv = best_move_by_ev(A, B)
            ev = expected_damage(A.mon, B.mon, mv)
            B.hp = max(0, B.hp - int(round(ev)))
            pv.append(f"A uses {mv.name} (EV {ev:.1f}) → B:{B.hp}/{B.mon.max_hp()}")
            to_move="B"
        else:
            mv = best_move_by_ev(B, A)
            ev = expected_damage(B.mon, A.mon, mv)
            A.hp = max(0, A.hp - int(round(ev)))
            pv.append(f"B uses {mv.name} (EV {ev:.1f}) → A:{A.hp}/{A.mon.max_hp()}")
            to_move="A"
    # Recommend first move actually rolled (not EV) to give Discord post
    first = best_move_by_ev(you, foe)
    outcome = resolve_hit(you, foe, first, terrain, rng)
    cites = []
    for q in ["Damage Base","STAB","Critical","Evasion","Type Effectiveness"]:
        cites += find_quote(q, max_hits=1)
    post = discord_turn_post(you, foe, first, outcome, extra_notes="EV perfect-play line: " + " → ".join(pv), citations=cites)
    return {"best_first_move": first.name, "principal_variation": pv, "discord_post": post}

def monte_carlo_first_move(you:Combatant, foe:Combatant, terrain:Terrain, sims:int=1000, seed:int=42)->Dict[str,float]:
    rng=random.Random(seed)
    table={}
    for m in you.mon.known_moves:
        wins=0
        for _ in range(max(1,sims//max(1,len(you.mon.known_moves)))):
            A=Combatant("A","Player",you.mon, you.x,you.y,you.mon.max_hp(),0,[])
            B=Combatant("B","AI",foe.mon, foe.x,foe.y,foe.mon.max_hp(),0,[])
            # A turn
            out=resolve_hit(A,B,m,terrain,rng)
            if B.hp<=0 and A.hp>0: wins+=1; continue
            # B greedy reply
            mvB = best_move_by_ev(B, A)
            out2=resolve_hit(B,A,mvB,terrain,rng)
            # Continue with greedy until one faints
            mvA = best_move_by_ev(A, B)
            while A.hp>0 and B.hp>0:
                out=resolve_hit(A,B,mvA,terrain,rng)
                if B.hp<=0: break
                out2=resolve_hit(B,A,mvB,terrain,rng)
            if B.hp<=0 and A.hp>0: wins+=1
        table[m.name]=wins/(sims//max(1,len(you.mon.known_moves)))
    return table

############################
# I/O helpers for sheets
############################

def _get_str(d, *keys, default=""):
    for k in keys:
        if k in d and d[k] is not None: return str(d[k])
    return default

def build_mon_from_dict(d:Dict[str,Any])->Pokemon:
    moves=[]
    for mv in d.get("moves",[]):
        moves.append(Move(
            name=mv["name"], type=mv["type"], category=mv["category"], db=int(mv["db"]),
            ac=mv.get("ac",2), range_kind=mv.get("range_kind","Melee"),
            range_value=mv.get("range_value"), keywords=mv.get("keywords",[]),
            priority=mv.get("priority",0), crit_range=mv.get("crit_range",20),
            freq=mv.get("freq", mv.get("frequency", "EOT")),
            effects_text=mv.get("effects_text", mv.get("effects", ""))
        ))
    return Pokemon(
        name=_get_str(d,"name","nickname","species"),
        species=_get_str(d,"species","name"),
        level=int(d["level"]), types=d["types"],
        hp_stat=int(d["hp_stat"]), atk=int(d["atk"]), def_=int(d["def"]), spatk=int(d["spatk"]), spdef=int(d["spdef"]), spd=int(d["spd"]),
        accuracy_cs=int(d.get("accuracy_cs",0)),
        evasion_bonus_phys=int(d.get("evasion_phys",0)), evasion_bonus_spec=int(d.get("evasion_spec",0)), evasion_bonus_spd=int(d.get("evasion_spd",0)),
        capabilities=[Capability(**c) for c in d.get("capabilities",[])],
        abilities=[Ability(name=a["name"], hooks=[AbilityHook(**h) for h in a.get("hooks",[])]) for a in d.get("abilities",[])],
        items=[Item(**it) for it in d.get("items",[])],
        statuses=[Status(**s) for s in d.get("statuses",[])],
        trainer_features=[TrainerFeature(**t) for t in d.get("trainer_features",[])],
        known_moves=moves
    )

def build_combatant(mon:Pokemon, id="you", controller="Player", pos=(5,5))->Combatant:
    c=Combatant(id, controller, mon, pos[0], pos[1], -1, 0, [])
    c.init_hp(); return c

def build_mons_from_dict(you_dict:Dict[str,Any], foe_dict:Dict[str,Any])->Dict[str,Combatant]:
    you = build_combatant(build_mon_from_dict(you_dict), id="you", controller="Player")
    foe = build_combatant(build_mon_from_dict(foe_dict), id="foe", controller="AI", pos=(12,5))
    return {"you":you,"foe":foe}

def load_party_from_excel(sheet_you:str, sheet_foe:str)->Dict[str,Combatant]:
    # Minimal parser that expects a "Stats" sheet with named columns
    import pandas as pd
    def read_one(xlsx):
        xl=pd.ExcelFile(xlsx)
        # Try Stats or Pokemon1 tab
        tab = "Stats" if "Stats" in xl.sheet_names else xl.sheet_names[0]
        df=pd.read_excel(xlsx, sheet_name=tab)
        d=df.set_index(df.columns[0]).to_dict().get(df.columns[1], {})
        # Expect keys like: species, level, types (comma), hp_stat, atk, def, spatk, spdef, spd
        types=[t.strip() for t in str(d.get("types","Electric")).split(",")]
        moves=[]
        mv_df_candidates=[n for n in xl.sheet_names if "Move" in n or "Attacks" in n or "Moves" in n]
        for tabn in mv_df_candidates:
            mdf=pd.read_excel(xlsx, sheet_name=tabn)
            for _,row in mdf.iterrows():
                if not str(row.get("Name","")).strip(): continue
                try:
                    moves.append({
                        "name":row.get("Name"),
                        "type":row.get("Type"),
                        "category":row.get("Category","Special"),
                        "db":int(row.get("DB",8)),
                        "ac":int(row.get("AC",2)),
                        "range_kind":"Ranged" if "Range" in row and str(row["Range"]).lower().startswith("ranged") else "Melee",
                        "range_value":int(re.findall(r"\d+", str(row.get("Range","6")))[0]) if "Range" in row else None,
                        "freq":row.get("Freq", row.get("Frequency", "EOT"))
                    })
                except Exception:
                    continue
        you_dict={
            "species":d.get("species", d.get("Species","Pokemon")),
            "level":int(d.get("level", d.get("Level",30))),
            "types":types,
            "hp_stat":int(d.get("hp_stat", d.get("HP",12))),
            "atk":int(d.get("atk", d.get("ATK",50))),
            "def":int(d.get("def", d.get("DEF",40))),
            "spatk":int(d.get("spatk", d.get("SpAtk",60))),
            "spdef":int(d.get("spdef", d.get("SpDef",50))),
            "spd":int(d.get("spd", d.get("SPD",80))),
            "moves":moves[:8] # cap
        }
        return you_dict
    return build_mons_from_dict(read_one(sheet_you), read_one(sheet_foe))

############################
# One-call helpers you’ll use
############################

def simulate_perfect_play(you:Dict[str,Any], foe:Dict[str,Any], weather:str="Clear", depth:int=6)->str:
    """High-level convenience: pass two dicts with stats/moves; get Discord-ready advice."""
    mons=build_mons_from_dict(you, foe)
    terr = Terrain() if weather=="Clear" else Terrain.rain()
    res = expectimax_battle(mons["you"], mons["foe"], terr, depth=depth)
    return res["discord_post"]
