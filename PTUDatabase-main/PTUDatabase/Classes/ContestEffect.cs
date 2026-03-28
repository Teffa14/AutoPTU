namespace PTUDatabase;

public record ContestEffect
{
    public string Name { get; init; } = "";
    public int? Dice { get; init; }
    [YamlDotNet.Serialization.YamlIgnore]
    public string DiceString => $"{Dice?.ToString() ?? "X"}d6";
    public string Effect { get; init; } = "";

    public override string ToString() => $"{Name} - {DiceString} - {Effect}";

    public static readonly ContestEffect None = new() { Name = "None", Dice = 0, Effect = "No effect." };
}
