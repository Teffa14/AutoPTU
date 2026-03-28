using CommunityToolkit.Mvvm.ComponentModel;
using PTUDatabase;

namespace PTUDataEditor.ViewModels;

public partial class MoveRequirementViewModel : ObservableObject
{
    public MoveRequirement BuildModel(IReadOnlyList<Move> allMoves) => new()
    {
        RequirementType = RequirementType,
        RequiredLevel = RequirementType == MoveRequirementType.Level ? RequiredLevel : null,
        MachineId = RequirementType == MoveRequirementType.Machine ? MachineId : null,
        Move = allMoves.First(m => m.Name == Move.Name),
    };

    public MoveRequirementViewModel(MoveRequirement model, IReadOnlyList<MoveViewModel> allMoves)
    {
        _RequirementType = model.RequirementType;
        _RequiredLevel = model.RequiredLevel ?? 1;
        _MachineId = model.MachineId ?? "TM00";
        _Move = allMoves.First(mvm => mvm.Name == model.Move.Name);
    }

    public MoveRequirementViewModel(MoveViewModel move, MoveRequirementType requirementType = MoveRequirementType.Level, int requiredLevel = 1, string machineId = "TM00")
    {
        _RequirementType = requirementType;
        _RequiredLevel = requiredLevel;
        _MachineId = machineId;
        _Move = move;
    }

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(ShowLevelBox))]
    [NotifyPropertyChangedFor(nameof(ShowMachineBox))]
    [NotifyPropertyChangedFor(nameof(ShowEitherBox))]
    private MoveRequirementType _RequirementType;

    public bool ShowLevelBox => RequirementType == MoveRequirementType.Level;
    public bool ShowMachineBox => RequirementType == MoveRequirementType.Machine;
    public bool ShowEitherBox => ShowLevelBox || ShowMachineBox;

    [ObservableProperty]
    private int _RequiredLevel;

    [ObservableProperty]
    private string _MachineId;

    [ObservableProperty]
    private MoveViewModel _Move;
}
