using YamlDotNet.Serialization;

namespace PTUDatabase;

public record MoveRange
{
    public MoveRangeType Type { get; init; }
    public MoveRangeKeywords Keywords { get; init; }
    [YamlMember(DefaultValuesHandling = DefaultValuesHandling.OmitNull)]
    public int? Targets { get; init; }
    [YamlMember(DefaultValuesHandling = DefaultValuesHandling.OmitNull)]
    public int? Range { get; init; }
    [YamlMember(DefaultValuesHandling = DefaultValuesHandling.OmitNull)]
    public int? Size { get; init; }

    public override string ToString()
    {
        var sb = new System.Text.StringBuilder();
        sb.Append(Type switch
        {
            MoveRangeType.Self => "Self",
            MoveRangeType.Melee => "Melee",
            MoveRangeType.CardinallyAdjacentTargets => "Cardinally Adjacent Targets",
            MoveRangeType.Any => $"Any",
            MoveRangeType.WeaponRange => $"WR",
            MoveRangeType.Burst => $"Burst {Size}",
            MoveRangeType.Ranged => $"{Range}",
            MoveRangeType.Line => $"Line {Range}",
            MoveRangeType.Cone => $"Cone {Range}",
            MoveRangeType.Blast when Range == 1 => $"Close Blast {Size}",
            MoveRangeType.Blast => $"{Range}, Ranged Blast {Size}",
            MoveRangeType.Field => $"Field",
            MoveRangeType.Blessing => $"Blessing",
            _ => $"Unknown Range {Range},{Size}",
        });

        if (Targets is int)
            sb.Append($", {Targets} Target{(Targets != 1 ? "s" : "")}");

        return sb.ToString();
    }

    public static MoveRange Self(MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Self, Keywords = keywords };

    public static MoveRange Melee(int maxTargets = 1, MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Melee, Targets = maxTargets, Keywords = keywords };

    public static MoveRange Any(int maxTargets = 1, MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Any, Targets = maxTargets, Keywords = keywords };

    public static MoveRange WeaponRange(int maxTargets = 1, MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.WeaponRange, Targets = maxTargets, Keywords = keywords };

    public static MoveRange Ranged(int range, int maxTargets = 1, MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Ranged, Targets = maxTargets, Range = range, Keywords = keywords };

    public static MoveRange CardinallyAdjacentTargets(int? maxTargets = null, MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.CardinallyAdjacentTargets, Targets = maxTargets, Keywords = keywords };

    public static MoveRange Burst(int radius, int? maxTargets = null, MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Burst, Targets = maxTargets, Size = radius, Keywords = keywords };

    public static MoveRange Line(int range, int? maxTargets = null, MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Line, Targets = maxTargets, Range = range, Keywords = keywords };

    public static MoveRange Cone(int range, int? maxTargets = null, MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Cone, Targets = maxTargets, Range = range, Keywords = keywords };

    public static MoveRange CloseBlast(int size, int? maxTargets = null, MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Blast, Targets = maxTargets, Range = 1, Size = size, Keywords = keywords };

    public static MoveRange RangedBlast(int range, int size, int? maxTargets = null, MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Blast, Targets = maxTargets, Range = range, Size = size, Keywords = keywords };

    public static MoveRange Field(MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Field, Keywords = keywords };

    public static MoveRange Blessing(MoveRangeKeywords keywords = MoveRangeKeywords.None)
        => new() { Type = MoveRangeType.Blessing, Keywords = keywords };
}
