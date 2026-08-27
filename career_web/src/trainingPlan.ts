import type { CareerPokemon, CareerRun } from "./types";

export type TrainingPlan = "manual" | "conditioning" | "power" | "guard" | "agility";
export type AutomaticTrainingPlan = Exclude<TrainingPlan, "manual">;

const TRAINING_STATS: Record<AutomaticTrainingPlan, (keyof CareerPokemon["stat_training"])[]> = {
  conditioning: ["hp"],
  power: ["atk", "spatk"],
  guard: ["def", "spdef"],
  agility: ["spd"],
};

export function canUseTrainingPlan(pokemon: CareerPokemon, plan: AutomaticTrainingPlan): boolean {
  if (pokemon.status === "retired" || pokemon.career_health <= 0) return false;
  const stats = TRAINING_STATS[plan];
  if (!stats) return false;
  return stats.some((stat) => authoritativeTrainingProgress(pokemon.stat_training?.[stat]) < 12);
}

export function automaticTrainingCandidates(run: CareerRun, plan: AutomaticTrainingPlan): string[] {
  const activeRoster = Array.isArray(run.active_roster) ? run.active_roster : [];
  const pokemonList = Array.isArray(run.pokemon) ? run.pokemon : [];
  const active = Array.from(new Set(activeRoster))
    .map((id) => pokemonList.find((pokemon) => pokemon && typeof pokemon === "object" && pokemon.id === id))
    .filter((pokemon): pokemon is CareerPokemon => Boolean(pokemon && pokemon.status !== "retired" && pokemon.career_health > 0));
  const completedIds = Array.isArray(run.season?.training_completed_ids) ? run.season.training_completed_ids : [];
  const completed = new Set(completedIds);

  return active
    .filter((pokemon) => !completed.has(pokemon.id) && canUseTrainingPlan(pokemon, plan))
    .map((pokemon) => pokemon.id);
}

export function automaticTrainingHasRoom(run: CareerRun, plan: AutomaticTrainingPlan): boolean {
  return automaticTrainingCandidates(run, plan).length > 0;
}

function authoritativeTrainingProgress(value: unknown): number {
  if (typeof value === "number") return Number.isFinite(value) && value >= 0 ? value : 0;
  if (typeof value !== "string") return 0;
  const text = value.trim();
  if (!text) return 0;
  const parsed = Number(text);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
}
