import type { CareerCatalog, CareerRun } from "./types";

export interface TrainerSpriteOption {
  id: string;
  label: string;
  region: string;
}

export interface TrainerSpriteStorageEntry {
  key: string;
  sprite: string;
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
  const rawTimeline = (run as unknown as { timeline?: unknown }).timeline;
  if (!Array.isArray(rawTimeline)) return DEFAULT_TRAINER_SPRITE;
  for (let index = rawTimeline.length - 1; index >= 0; index -= 1) {
    const entry = rawTimeline[index];
    if (!entry || typeof entry !== "object") continue;
    const event = entry as { type?: unknown; trainer_sprite?: unknown };
    if (event.type !== "trainer.appearance_selected") continue;
    if (typeof event.trainer_sprite !== "string") continue;
    const sprite = event.trainer_sprite.trim();
    if (sprite) return sprite;
  }
  return DEFAULT_TRAINER_SPRITE;
}

export function trainerSpriteStorageEntry(run: CareerRun): TrainerSpriteStorageEntry | null {
  const rawBuild = (run as unknown as { build?: { name?: unknown } }).build;
  if (typeof rawBuild?.name !== "string") return null;
  const name = rawBuild.name.trim();
  if (!name) return null;
  return {
    key: `career-trainer-sprite:${name.toLocaleLowerCase()}`,
    sprite: trainerSpriteForRun(run),
  };
}
