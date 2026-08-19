import type { Locale } from "../types";
import { trainerSpriteUrl, type TrainerSpriteOption } from "../trainerSprites";
import "../trainerSprites.css";

interface Props {
  sprites: TrainerSpriteOption[];
  value: string;
  locale: Locale;
  compact?: boolean;
  onChange: (sprite: string) => void;
}

export function TrainerSpritePicker({ sprites, value, locale, compact = false, onChange }: Props) {
  if (!sprites.length) return null;
  return (
    <fieldset className={`trainer-sprite-field ${compact ? "compact" : ""}`.trim()}>
      <legend>{locale === "es" ? "Apariencia del entrenador" : "Trainer appearance"}</legend>
      <div className="trainer-sprite-grid">
        {sprites.map((sprite) => (
          <button
            type="button"
            key={sprite.id}
            className={value === sprite.id ? "trainer-sprite-option active" : "trainer-sprite-option"}
            aria-pressed={value === sprite.id}
            aria-label={`${locale === "es" ? "Elegir" : "Choose"} ${sprite.label}`}
            onClick={() => onChange(sprite.id)}
          >
            <img src={trainerSpriteUrl(sprite.id)} alt="" loading="lazy" />
            <span>{sprite.label}</span>
            <small>{sprite.region.toUpperCase()}</small>
          </button>
        ))}
      </div>
    </fieldset>
  );
}
