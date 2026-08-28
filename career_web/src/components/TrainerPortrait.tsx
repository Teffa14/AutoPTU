import type { CSSProperties } from "react";

import trainerPortraits from "../assets/generated/trainer-portraits-v1.png";
import { readLocalStorage } from "../browserStorage";
import { trainerSpriteUrl } from "../trainerSprites";

interface Props {
  name: string;
  role?: "owner" | "mentor" | "rival" | "scout" | string;
  className?: string;
}

const POSITIONS = [["0%", "0%"], ["100%", "0%"], ["0%", "100%"], ["100%", "100%"]] as const;
const ROLE_INDEX: Record<string, number> = { owner: 0, mentor: 1, rival: 2, scout: 3, contact: 3 };

export function TrainerPortrait({ name, role = "scout", className = "" }: Props) {
  const playerSprite = className.includes("profile-trainer-portrait")
    ? readLocalStorage(`career-trainer-sprite:${name.trim().toLocaleLowerCase()}`) ?? ""
    : "";
  if (playerSprite) {
    return <span
      className={`trainer-portrait ${className}`.trim()}
      role="img"
      aria-label={name}
      title={name}
      style={{ background: "none", display: "grid", placeItems: "center", overflow: "visible" } as CSSProperties}
    ><img src={trainerSpriteUrl(playerSprite)} alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "center bottom", imageRendering: "pixelated" }} /></span>;
  }
  const index = ROLE_INDEX[role] ?? stableIndex(name);
  const [x, y] = POSITIONS[index];
  return <span
    className={`trainer-portrait ${className}`.trim()}
    role="img"
    aria-label={name}
    title={name}
    style={{ "--portrait-sheet": `url(${trainerPortraits})`, "--portrait-x": x, "--portrait-y": y } as CSSProperties}
  />;
}

function stableIndex(value: string): number {
  let hash = 0;
  for (const character of value) hash = ((hash * 31) + character.charCodeAt(0)) >>> 0;
  return hash % POSITIONS.length;
}
