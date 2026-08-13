import { fallbackSpriteUrl, spriteUrl } from "../spriteUrl";

interface Props {
  name: string;
  className?: string;
  decorative?: boolean;
}

export function PokemonSprite({ name, className = "", decorative = false }: Props) {
  return (
    <span className={`pokemon-sprite ${className}`.trim()}>
      <img
        src={spriteUrl(name)}
        alt={decorative ? "" : name}
        loading="lazy"
        onError={(event) => {
          const image = event.currentTarget;
          const fallback = fallbackSpriteUrl();
          if (!image.src.endsWith(fallback)) image.src = fallback;
        }}
      />
    </span>
  );
}
