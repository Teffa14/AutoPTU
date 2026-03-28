using CommunityToolkit.Mvvm.ComponentModel;
using PTUDatabase;

namespace PTUDataEditor.ViewModels;

public partial class AbilityRequirementViewModel : ObservableObject
{
    public AbilityRequirement BuildModel(IReadOnlyList<Ability> allAbilities) => new()
    {
        RequirementType = RequirementType,
        Ability = allAbilities.First(a => a.Name == Ability.Name),
    };

    public AbilityRequirementViewModel(AbilityRequirement model, IReadOnlyList<AbilityViewModel> allAbilities)
    {
        _RequirementType = model.RequirementType;
        _Ability = allAbilities.First(avm => avm.Name == model.Ability.Name);
    }

    public AbilityRequirementViewModel(AbilityViewModel ability, AbilityRequirementType requirementType = AbilityRequirementType.Basic)
    {
        _RequirementType = requirementType;
        _Ability = ability;
    }

    [ObservableProperty]
    private AbilityRequirementType _RequirementType;

    [ObservableProperty]
    private AbilityViewModel _Ability;

}
