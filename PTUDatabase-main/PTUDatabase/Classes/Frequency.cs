using YamlDotNet.Serialization;

namespace PTUDatabase;

public record Frequency
{
    public FrequencyType Type { get; init; }
    [YamlMember(DefaultValuesHandling = DefaultValuesHandling.OmitNull)]
    public int? Count { get; init; }

    public static Frequency AtWill() => new() { Type = FrequencyType.AtWill };
    public static Frequency EveryOtherTurn() => new() { Type = FrequencyType.EveryOtherTurn };
    public static Frequency Static() => new() { Type = FrequencyType.Static };
    public static Frequency Varies() => new() { Type = FrequencyType.Varies };
    public static Frequency Scene(int count) => new() { Type = FrequencyType.Scene, Count = count };
    public static Frequency Daily(int count) => new() { Type = FrequencyType.Daily, Count = count };

    public override string ToString() => this switch
    {
        Frequency { Type: FrequencyType.AtWill } => "At-Will",
        Frequency { Type: FrequencyType.EveryOtherTurn } => "EOT",
        Frequency { Type: FrequencyType.Varies } => "Varies",
        Frequency { Type: FrequencyType.Scene, Count: 1 } => "Scene",
        Frequency { Type: FrequencyType.Scene } => $"Scene x{Count}",
        Frequency { Type: FrequencyType.Daily, Count: 1 } => "Daily",
        Frequency { Type: FrequencyType.Daily } => $"Daily x{Count}",
        _ => $"Unknown Freq x{Count}",
    };
}
