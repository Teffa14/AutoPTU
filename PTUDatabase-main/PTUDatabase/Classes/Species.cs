namespace PTUDatabase;

public record Species
{
    public string Name { get; init; } = "";
    public int? NationalDexNumber { get; init; }
    public IList<Form> Forms { get; init; } = Array.Empty<Form>();
    public Rarity Rarity { get; init; } = Rarity.Common;
    public int MinimumLevel { get; init; }

    public override string ToString() => Name;
}
