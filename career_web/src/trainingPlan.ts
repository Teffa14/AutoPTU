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
  return TRAINING_STATS[plan].some((stat) => Number(pokemon.stat_training?.[stat] ?? 0) < 12);
}

export function automaticTrainingCandidates(run: CareerRun, plan: AutomaticTrainingPlan): string[] {
  const active = run.active_roster
    .map((id) => run.pokemon.find((pokemon) => pokemon.id === id))
    .filter((pokemon): pokemon is CareerPokemon => Boolean(pokemon && pokemon.status !== "retired" && pokemon.career_health > 0));
  const completed = new Set(run.season?.training_completed_ids ?? []);

  const selected = run.mode === "advanced"
    ? active
    : [active.find((pokemon) => pokemon.is_partner) ?? active[0]].filter((pokemon): pokemon is CareerPokemon => Boolean(pokemon));

  return selected
    .filter((pokemon) => !completed.has(pokemon.id) && canUseTrainingPlan(pokemon, plan))
    .map((pokemon) => pokemon.id);
}

export function automaticTrainingHasRoom(run: CareerRun, plan: AutomaticTrainingPlan): boolean {
  return automaticTrainingCandidates(run, plan).length > 0;
}
