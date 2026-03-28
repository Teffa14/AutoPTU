namespace PTUDatabase;

public sealed record AbilityRequirement
{
    public AbilityRequirementType RequirementType { get; init; }
    public Ability Ability { get; init; } = Ability.None;

    public override string ToString() => RequirementType switch
    {
        AbilityRequirementType.Basic => $"{Ability.Name} (Basic Ability)",
        AbilityRequirementType.Advanced => $"{Ability.Name} (Adv Ability)",
        AbilityRequirementType.High => $"{Ability.Name} (High Ability)",
        _ => throw new System.NotImplementedException(),
    };
}
