using CommunityToolkit.Mvvm.ComponentModel;
using PTUDatabase;

namespace PTUDataEditor.ViewModels;

public partial class AbilityViewModel : ObservableObject
{
    public Ability BuildModel() => new()
    {
        Name = Name,
        Trigger = Trigger,
        Target = Target,
        Effect = Effect,
        Frequency = new Frequency
        {
            Type = FrequencyType,
            Count = FrequencyType switch
            {
                FrequencyType.Scene or FrequencyType.Daily => FrequencyCount,
                _ => null,
            },
        },
        Keywords = Keywords,
        UnofficialAlternative = UnofficialAlternative,
    };

    public AbilityViewModel(Ability model)
    {
        _Name = model.Name;
        _Trigger = model.Trigger;
        _Target = model.Target;
        _Effect = model.Effect;
        _FrequencyType = model.Frequency.Type;
        _FrequencyCount = model.Frequency.Count ?? 1;
        _Keywords = model.Keywords;
        _UnofficialAlternative = model.UnofficialAlternative;
    }

    [ObservableProperty]
    private string _Name;

    [ObservableProperty]
    private string _Trigger;

    [ObservableProperty]
    private string _Target;

    [ObservableProperty]
    private string _Effect;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FrequencyCountVisible))]
    private FrequencyType _FrequencyType;

    [ObservableProperty]
    private int _FrequencyCount;

    public bool FrequencyCountVisible => FrequencyType switch
    {
        FrequencyType.Scene or FrequencyType.Daily => true,
        _ => false,
    };

    [ObservableProperty]
    private MoveRangeKeywords _Keywords;

    [ObservableProperty]
    private bool _UnofficialAlternative;
}
