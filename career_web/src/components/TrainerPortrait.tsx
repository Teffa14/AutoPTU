import type { CSSProperties } from "react";

import { readLocalStorage } from "../browserStorage";
import { trainerSpriteUrl } from "../trainerSprites";

interface Props {
  name: string;
  role?: "owner" | "mentor" | "rival" | "scout" | string;
  className?: string;
}

const ROLE_SPRITES: Record<string, readonly string[]> = {
  owner: ["clerk-boss", "gentleman", "madame", "richboy"],
  mentor: ["veteran", "riley", "cynthia", "alder"],
  rival: ["acetrainer", "acetrainerf", "benga", "hugh"],
  scout: ["pokemonranger", "pokemonrangerf", "backpacker", "backpackerf"],
  contact: ["reporter", "interviewer-gen3", "scientist", "doctor"],
};
const FALLBACK_SPRITES = ROLE_SPRITES.scout;

export function TrainerPortrait({ name, role = "scout", className = "" }: Props) {
  const playerSprite = className.includes("profile-trainer-portrait")
    ? readLocalStorage(`career-trainer-sprite:${name.trim().toLocaleLowerCase()}`) ?? ""
    : "";
  const sprite = playerSprite || roleSprite(name, role);
  return <span
    className={`trainer-portrait ${className}`.trim()}
    role="img"
    aria-label={name}
    title={name}
    style={{ background: "none", display: "grid", placeItems: "center", overflow: "visible" } as CSSProperties}
  ><img
      src={trainerSpriteUrl(sprite)}
      alt=""
      loading="lazy"
      decoding="async"
      style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "center bottom", imageRendering: "pixelated" }}
    /></span>;
}

function roleSprite(name: string, role: string): string {
  const options = ROLE_SPRITES[role] ?? FALLBACK_SPRITES;
  return options[stableIndex(name, options.length)] ?? FALLBACK_SPRITES[0];
}

function stableIndex(value: string, size: number): number {
  let hash = 0;
  for (const character of value) hash = ((hash * 31) + character.charCodeAt(0)) >>> 0;
  return hash % Math.max(1, size);
}
