import { useMemo, useState } from "react";

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
  const [query, setQuery] = useState("");
  const selected = sprites.find((sprite) => sprite.id === value) ?? sprites[0];
  const filtered = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase();
    if (!needle) return sprites;
    return sprites.filter((sprite) => `${sprite.label} ${sprite.id} ${sprite.region}`.toLocaleLowerCase().includes(needle));
  }, [query, sprites]);
  const choices = selected && !filtered.some((sprite) => sprite.id === selected.id)
    ? [selected, ...filtered]
    : filtered;

  if (!selected) return null;
  return (
    <fieldset className={`trainer-sprite-field ${compact ? "compact" : ""}`.trim()}>
      <legend>{locale === "es" ? "Apariencia del entrenador" : "Trainer appearance"}</legend>
      <div className="trainer-picker-shell">
        <figure className="trainer-sprite-preview" aria-live="polite">
          <img src={trainerSpriteUrl(selected.id)} alt="" decoding="async" />
          <figcaption>
            <strong>{selected.label}</strong>
            <small>{selected.region === "showdown" ? "SHOWDOWN ARCHIVE" : selected.region.toUpperCase()}</small>
          </figcaption>
        </figure>
        <div className="trainer-picker-controls">
          <label>
            <span>{locale === "es" ? "Buscar personaje" : "Search character"}</span>
            <input
              type="search"
              value={query}
              placeholder={locale === "es" ? "Nombre, generación o ID…" : "Name, generation or ID…"}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <label>
            <span>{locale === "es" ? "Sprite" : "Sprite"}</span>
            <select value={selected.id} onChange={(event) => onChange(event.target.value)}>
              {choices.map((sprite) => (
                <option key={sprite.id} value={sprite.id}>{sprite.label} · {sprite.id}</option>
              ))}
            </select>
          </label>
          <small className="trainer-picker-count">
            {locale === "es"
              ? `${filtered.length} de ${sprites.length} disponibles · sólo se carga la preview seleccionada`
              : `${filtered.length} of ${sprites.length} available · only the selected preview is loaded`}
          </small>
        </div>
      </div>
    </fieldset>
  );
}
