export function spriteUrl(species: string): string {
  return `https://play.pokemonshowdown.com/sprites/ani/${spriteSlug(species)}.gif`;
}

export function fallbackSpriteUrl(): string {
  return "https://play.pokemonshowdown.com/sprites/ani/substitute.gif";
}

export function spriteSlug(species: string): string {
  const normalized = species
    .trim()
    .toLowerCase()
    .replaceAll("♀", "f")
    .replaceAll("♂", "m")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "");
  const regional = normalized
    .replace(/\s+(alolan|alola)$/i, "-alola")
    .replace(/\s+(galarian|galar)$/i, "-galar")
    .replace(/\s+(hisuian|hisui)$/i, "-hisui")
    .replace(/\s+(paldean|paldea)$/i, "-paldea");
  return regional.replace(/[^a-z0-9-]+/g, "").replace(/^-+|-+$/g, "");
}
