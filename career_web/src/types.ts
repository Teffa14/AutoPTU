export type Locale = "es" | "en";
export type CareerMode = "simple" | "advanced";

export interface RegionCatalog {
  id: string;
  label: string;
  underdogs: string[];
  starters: string[];
  partner_choices: string[];
  clubs: string[];
  arena_theme: string;
}

export interface CareerCatalog {
  version: string;
  regions: RegionCatalog[];
  classes: {
    id: string;
    name: string;
    focus: string;
    battle: Record<string, number>;
    season: Record<string, number>;
    decision_affinity: string;
    description_es: string;
    description_en: string;
  }[];
  class_count: number;
  feature_count: number;
  decision_signature_count: number;
  items: Record<string, { description_es: string; description_en: string; target: string }>;
  shop: Record<string, { label_es: string; label_en: string; description_es: string; description_en: string; price: number; kind: string; item?: string }>;
  training_methods: Record<string, { label_es: string; label_en: string; description_es: string; description_en: string; stats: Record<string, number> }>;
}

export interface DecisionOption {
  id: string;
  label: string;
  description: string;
  risk: "safe" | "calculated" | "gamble";
  transparency: "full" | "estimated" | "hidden";
  guaranteed: Record<string, number>;
  rewards: DecisionReward[];
  gamble?: {
    chance?: number;
    success?: Record<string, number>;
    failure?: Record<string, number>;
    success_rewards?: DecisionReward[];
    failure_rewards?: DecisionReward[];
  };
}

export type DecisionReward =
  | { type: "pokemon"; species: string; rarity?: "common" | "rare" | "very_rare" | "epic" | "legendary" | "mythical" }
  | { type: "item"; item: string; quantity: number }
  | { type: "move"; move: string }
  | { type: "relationship"; name: string; amount: number }
  | { type: "level"; levels: number }
  | { type: "stat"; pokemon_id: string; species: string; stat: "hp" | "atk" | "def" | "spatk" | "spdef" | "spd"; amount: number };

export interface CareerDecision {
  id: string;
  family: string;
  title: string;
  body: string;
  npc_name: string;
  options: DecisionOption[];
  variant?: string;
}

export interface CareerPokemon {
  id: string;
  species: string;
  caught_species: string;
  level: number;
  acquired_season: number;
  acquired_age: number;
  capture_region: string;
  is_partner: boolean;
  status: "active" | "pc";
  matches: number;
  wins: number;
  taught_moves: string[];
  nature: string;
  abilities: string[];
  stat_training: Partial<Record<"hp" | "atk" | "def" | "spatk" | "spdef" | "spd", number>>;
  evolution_history: {
    from: string;
    to: string;
    level: number;
    season: number;
    age: number;
  }[];
  gimmicks: string[];
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
  career_earnings: number;
  money: number;
  pokedex_level: number;
  license_status: string;
  seasons_without_contract: number;
  relationships: Record<string, number>;
  relationship_effects: {
    best_contact?: string;
    best_value?: number;
    active_contacts?: number;
    home_level_bonus?: number;
    season_recovery?: number;
    contract_guard?: boolean;
    mentor_training_bonus?: number;
    rival_scouting_bonus?: number;
    owner_recovery_bonus?: number;
    contact_effects?: {
      name: string;
      role: string;
      bond: number;
      tier: string;
      benefit: string;
      amount: number;
      next_unlock?: number | null;
    }[];
  };
  inventory: Record<string, number>;
  status: "active" | "retired";
  revision: number;
  build: { name: string; region: string; starter: string; classes: string[]; pokeballs: number };
  contract?: { club_name: string; region: string; league: string; salary: number; loan_slots: number; seasons_remaining: number };
  roster: string[];
  pokemon: CareerPokemon[];
  active_roster: string[];
  totals: { wins: number; losses: number; draws: number; titles: number };
  achievements: string[];
  class_effects: {
    adapters: { class_name: string; focus: string; description_es: string; description_en: string; battle: Record<string, number>; season: Record<string, number> }[];
    battle: Record<string, number>;
    season: Record<string, number>;
  };
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
    training_completed: boolean;
    training_method: string;
    training_completed_ids: string[];
  };
  summary?: {
    seasons: number;
    final_age: number;
    highest_league: string;
    wins: number;
    losses: number;
    titles: number;
    score: number;
    retirement_reason: string;
    achievements: string[];
    pokemon_owned: number;
    evolutions: number;
    partner_species: string;
  };
}

export interface BattleTranscript {
  battle_id: string;
  winner_team?: string;
  winner_label?: string;
  rounds: number;
  sha256: string;
  spec: {
    seed?: number;
    home_club: string;
    away_club: string;
    home_species: string;
    home_pokemon_id?: string;
    away_species: string;
    region: string;
    league: string;
    season?: number;
    level?: number;
    home_level_bonus?: number;
    away_level_bonus?: number;
    home_team_species?: string[];
    home_pokemon_ids?: string[];
    home_team_levels?: number[];
    home_team_natures?: string[];
    home_team_abilities?: string[][];
    away_team_species?: string[];
    away_team_levels?: number[];
    away_team_rarities?: string[];
    away_team_gimmicks?: string[];
    difficulty_label?: "favored" | "even" | "dangerous";
    home_ai_level?: string;
    away_ai_level?: string;
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
    nature?: string;
    hp: number;
    max_hp: number;
    position?: [number, number];
    sprite_url?: string;
    statuses?: string[];
    stats?: Partial<Record<"hp" | "atk" | "def" | "spatk" | "spdef" | "spd", number>>;
    effective_stats?: Partial<Record<"hp" | "atk" | "def" | "spatk" | "spdef" | "spd", number>>;
    abilities?: string[];
    types?: string[];
    moves?: BattleMove[];
    active?: boolean;
    size?: string;
    footprint_side?: number;
    gimmick?: string;
}
