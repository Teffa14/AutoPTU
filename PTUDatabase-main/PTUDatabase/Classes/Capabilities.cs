using System.Text;

namespace PTUDatabase;

public record Capabilities
{
    public int Overland { get; init; }
    public int Swim { get; init; }
    public int Sky { get; init; }
    public int Levitate { get; init; }
    public int Burrow { get; init; }
    public int Teleporter { get; init; }
    public int HighJump { get; init; }
    public int LongJump { get; init; }
    public int Power { get; init; }
    public int Mountable { get; init; }
    public IList<TerrainType> NaturewalkTypes { get; init; } = Array.Empty<TerrainType>();
    public IList<OtherCapability> Others { get; init; } = Array.Empty<OtherCapability>();

    public static readonly Capabilities None = new();

    public override string ToString()
    {
        var sb = new StringBuilder();

        if (Overland > 0)
            sb.Append(", Overland ").Append(Overland);
        if (Swim > 0)
            sb.Append(", Swim ").Append(Swim);
        if (Sky > 0)
            sb.Append(", Sky ").Append(Sky);
        if (Levitate > 0)
            sb.Append(", Levitate ").Append(Levitate);
        if (Burrow > 0)
            sb.Append(", Burrow ").Append(Burrow);
        if (Teleporter > 0)
            sb.Append(", Teleporter ").Append(Teleporter);
        if (HighJump > 0 || LongJump > 0)
            sb.Append(", Jump ").Append(HighJump).Append('/').Append(LongJump);
        if (Power > 0)
            sb.Append(", Power ").Append(Power);
        if (Mountable > 0)
            sb.Append(", Mountable ").Append(Mountable);
        if (NaturewalkTypes.Count > 0)
            sb.Append(", Naturewalk (").Append(string.Join(", ", NaturewalkTypes.Select(t => Utilities.GetActualName(t)))).Append(')');
        foreach (var other in Others)
            sb.Append(", ").Append(Utilities.GetActualName(other));

        if (sb.Length >= 2)
            return sb.ToString(2, sb.Length - 2);
        else
            return "None";
    }
}

