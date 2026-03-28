using CommunityToolkit.Mvvm.ComponentModel;
using PTUDatabase;

namespace PTUDataEditor.ViewModels;

public partial class ContestEffectViewModel : ObservableObject
{
    public ContestEffect BuildModel() => new()
    {
        Name = Name,
        Dice = Dice == 0 ? null : Dice,
        Effect = Effect,
    };

    public ContestEffectViewModel(ContestEffect model)
    {
        _Name = model.Name;
        _Dice = model.Dice ?? 0;
        _Effect = model.Effect;
    }

    [ObservableProperty]
    private string _Name;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(DiceString))]
    [NotifyPropertyChangedFor(nameof(UsesVariableDice))]
    private int _Dice;

    public string DiceString => _Dice == 0 ? "Xd6" : $"{_Dice}d6";

    public bool UsesVariableDice
    {
        get => _Dice == 0;
        set
        {
            if (value && _Dice != 0)
                Dice = 0;
            else if (!value && _Dice == 0)
                Dice = 1;
        }
    }

    [ObservableProperty]
    private string _Effect;
}
