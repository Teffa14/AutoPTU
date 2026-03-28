using CommunityToolkit.Mvvm.ComponentModel;
using PTUDatabase;

namespace PTUDataEditor.ViewModels;

public partial class MoveViewModel : ObservableObject
{
    public Move BuildModel(IReadOnlyList<ContestEffect> allContestEffects) => new()
    {
        Name = Name,
        Type = Type,
        Class = Class,
        DamageBase = HasDamageBase ? DamageBase : null,
        Frequency = FrequencyType switch
        {
            FrequencyType.Daily or FrequencyType.Scene => new() { Type = FrequencyType, Count = FrequencyCount },
            _ => new() { Type = FrequencyType, Count = null },
        },
        AccuracyCheck = HasAccuracyCheck ? AccuracyCheck : null,
        Range = Range,
        ContestType = ContestType,
        ContestEffect = (HasContestEffect ? allContestEffects.FirstOrDefault(ce => ce.Name == MoveContestEffect?.Name) : null) ?? ContestEffect.None,
        Effects = Effects,
        UnofficialAlternative = UnofficialAlternative,
    };


    public MoveViewModel(Move model, DatabaseViewModel db)
    {
        _Name = model.Name;
        _Type = model.Type;
        _Class = model.Class;
        _DamageBase = model.DamageBase ?? 1;
        _HasDamageBase = model.DamageBase is not null;
        _FrequencyType = model.Frequency.Type;
        _FrequencyCount = model.Frequency.Count ?? 1;
        _AccuracyCheck = model.AccuracyCheck ?? 0;
        _HasAccuracyCheck = model.AccuracyCheck is not null;
        _Range = model.Range;
        _ContestType = model.ContestType;
        _HasContestEffect = model.ContestEffect != ContestEffect.None;
        _MoveContestEffect = _HasContestEffect ? db.ContestEffects.FirstOrDefault(cevm => cevm.Name == model.Name) : null;
        _Effects = model.Effects;
        _UnofficialAlternative = model.UnofficialAlternative;
        RootDB = db;
    }

    public DatabaseViewModel RootDB { get; }

    [ObservableProperty]
    private string _Name;

    [ObservableProperty]
    private PokemonType _Type;

    [ObservableProperty]
    private MoveClass _Class;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(DamageRoll))]
    private int _DamageBase;

    public string DamageRoll => Move.DamageBaseData[DamageBase].Dice;

    [ObservableProperty]
    private bool _HasDamageBase;

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
    private int _AccuracyCheck;

    [ObservableProperty]
    private bool _HasAccuracyCheck;

    [ObservableProperty]
    private string _Range;

    [ObservableProperty]
    private ContestType _ContestType;

    [ObservableProperty]
    private bool _HasContestEffect;

    [ObservableProperty]
    private ContestEffectViewModel? _MoveContestEffect;

    [ObservableProperty]
    private string _Effects;

    [ObservableProperty]
    private bool _UnofficialAlternative;
}
