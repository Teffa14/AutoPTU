export function spriteUrl(species: string): string {
  if (import.meta.env.DEV) return `/api/sprites/pokemon?name=${encodeURIComponent(species)}`;
  return `/career-game/sprites/${spriteSlug(species)}.png`;
}

export function fallbackSpriteUrl(): string {
  return import.meta.env.DEV ? "/sprites/000.png" : "/career-game/sprites/000.png";
}

export function spriteSlug(species: string): string {
  return species
    .trim()
    .toLowerCase()
    .replaceAll("♀", " female")
    .replaceAll("♂", " male")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
