namespace PTUDatabase;

public record Form
{
    public string Name { get; init; } = "";
    public string? ImageUrl { get; init; }
    public Stats BaseStats { get; init; } = Stats.Zero;
    public IList<PokemonType> Types { get; init; } = Array.Empty<PokemonType>();
    public IList<AbilityRequirement> Abilities { get; init; } = Array.Empty<AbilityRequirement>();
    public IList<MoveRequirement> Moves { get; init; } = Array.Empty<MoveRequirement>();
    public Skills BaseSkills { get; init; } = Skills.Zero;
    public Capabilities Capabilities { get; init; } = Capabilities.None;
    public (float Meters, float Inches, SizeClass Class) AverageSize { get; init; }
    public (float Kilograms, float Pounds, int Class) AverageWeight { get; init; }
    public float? MaleFemaleRatio { get; init; } = 0.5f; // Genderless = null
    public IList<EggGroup> EggGroups { get; init; } = Array.Empty<EggGroup>();
    public float SelectionWeight { get; init; } = 1f;
    // Evolution info?
}
