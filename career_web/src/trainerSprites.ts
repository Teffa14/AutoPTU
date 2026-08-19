import type { CareerCatalog, CareerRun } from "./types";

export interface TrainerSpriteOption {
  id: string;
  label: string;
  region: string;
}

const TRAINER_SPRITE_BASE = "https://play.pokemonshowdown.com/sprites/trainers";
export const DEFAULT_TRAINER_SPRITE = "red";

export function trainerSpriteOptions(catalog: CareerCatalog | null): TrainerSpriteOption[] {
  const enriched = catalog as (CareerCatalog & { trainer_sprites?: TrainerSpriteOption[] }) | null;
  return enriched?.trainer_sprites ?? [];
}

export function trainerSpriteUrl(sprite: string): string {
  const id = sprite.trim().toLowerCase() || DEFAULT_TRAINER_SPRITE;
  return `${TRAINER_SPRITE_BASE}/${encodeURIComponent(id)}.png`;
}

export function trainerSpriteForRun(run: CareerRun): string {
  const event = [...run.timeline].reverse().find((entry) => entry.type === "trainer.appearance_selected");
  return typeof event?.trainer_sprite === "string" && event.trainer_sprite ? event.trainer_sprite : DEFAULT_TRAINER_SPRITE;
}
