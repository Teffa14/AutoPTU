namespace PTUDatabase;

public record Ability
{
    public string Name { get; init; } = "";
    public string Trigger { get; init; } = "";
    public string Target { get; init; } = "";
    public string Effect { get; init; } = "";
    public Frequency Frequency { get; init; } = Frequency.Static();
    public MoveRangeKeywords Keywords { get; init; } = MoveRangeKeywords.None;
    public bool UnofficialAlternative { get; init; } = false;

    public static readonly Ability None = new() { Name = "None" };
}
