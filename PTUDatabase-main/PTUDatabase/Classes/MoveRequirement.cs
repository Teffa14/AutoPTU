using YamlDotNet.Serialization;

namespace PTUDatabase;

public sealed record MoveRequirement
{
    public MoveRequirementType RequirementType { get; init; }
    public Move Move { get; init; } = Move.None;
    [YamlMember(DefaultValuesHandling = DefaultValuesHandling.OmitNull)]
    public int? RequiredLevel { get; init; }
    [YamlMember(DefaultValuesHandling = DefaultValuesHandling.OmitNull)]
    public string? MachineId { get; init; }

    public override string ToString() => RequirementType switch
    {
        MoveRequirementType.Egg => $"{Move.Name} (Egg)",
        MoveRequirementType.Level => $"{Move.Name} (Level {RequiredLevel})",
        MoveRequirementType.Tutor => $"{Move.Name} (Tutor)",
        MoveRequirementType.Machine => $"{Move.Name} ({MachineId})",
        _ => throw new System.NotImplementedException(),
    };
}
