export type Locale = "es" | "en";
export type CareerMode = "simple" | "advanced";

export interface RegionCatalog {
  id: string;
  label: string;
  underdogs: string[];
  clubs: string[];
  arena_theme: string;
}

export interface CareerCatalog {
  version: string;
  regions: RegionCatalog[];
  classes: { id: string; name: string }[];
  class_count: number;
  feature_count: number;
  decision_signature_count: number;
}

export interface DecisionOption {
  id: string;
  label: string;
  description: string;
  risk: "safe" | "calculated" | "gamble";
  transparency: "full" | "estimated" | "hidden";
  guaranteed: Record<string, number>;
  gamble?: {
    chance?: number;
    success?: Record<string, number>;
    failure?: Record<string, number>;
  };
}

export interface CareerDecision {
  id: string;
  family: string;
  title: string;
  body: string;
  npc_name: string;
  options: DecisionOption[];
}

export interface CareerRun {
  id: string;
  mode: CareerMode;
  locale: Locale;
  age: number;
  league: string;
  season_number: number;
  health: number;
  score: number;
  reputation: number;
  development: number;
  scouting: number;
  finances: number;
  status: "active" | "retired";
  revision: number;
  build: { name: string; region: string; starter: string; classes: string[]; pokeballs: number };
  contract?: { club_name: string; region: string; league: string; salary: number; loan_slots: number };
  roster: string[];
  totals: { wins: number; losses: number; draws: number; titles: number };
  achievements: string[];
  timeline: Record<string, unknown>[];
  season?: {
    number: number;
    age: number;
    league: string;
    club_name: string;
    status: string;
    decision?: CareerDecision;
    battle_ids: string[];
    decisions_required: number;
    decisions_completed: number;
    decision_history: Record<string, unknown>[];
  };
  summary?: Record<string, unknown>;
}

export interface BattleTranscript {
  battle_id: string;
  winner_team?: string;
  winner_label?: string;
  rounds: number;
  sha256: string;
  spec: {
    home_club: string;
    away_club: string;
    home_species: string;
    away_species: string;
    region: string;
    league: string;
    season?: number;
    level?: number;
    home_level_bonus?: number;
    away_level_bonus?: number;
  };
  events: Record<string, unknown>[];
  initial_state: BattleFrame;
  final_state: BattleFrame;
}

export interface BattleFrame {
  round: number;
  battle_over: boolean;
  winner_team?: string;
  grid?: { width: number; height: number };
  combatants: BattleCombatant[];
}

export interface BattleMove {
  name: string;
  type: string;
  category: string;
  db?: number;
  ac?: number;
  range?: string;
}

export interface BattleCombatant {
    id: string;
    name: string;
    species: string;
    team: string;
    level?: number;
    hp: number;
    max_hp: number;
    position?: [number, number];
    sprite_url?: string;
    statuses?: string[];
    stats?: Partial<Record<"hp" | "atk" | "def" | "spatk" | "spdef" | "spd", number>>;
    effective_stats?: Partial<Record<"hp" | "atk" | "def" | "spatk" | "spdef" | "spd", number>>;
    abilities?: string[];
    moves?: BattleMove[];
}
