interface Props {
  name: string;
  className?: string;
  decorative?: boolean;
}

export function PokemonSprite({ name, className = "", decorative = false }: Props) {
  return (
    <span className={`pokemon-sprite ${className}`.trim()}>
      <img
        src={`/api/sprites/pokemon?name=${encodeURIComponent(name)}`}
        alt={decorative ? "" : name}
        loading="lazy"
      />
    </span>
  );
}
