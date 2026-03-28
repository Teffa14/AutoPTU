using CommunityToolkit.Mvvm.ComponentModel;
using PTUDatabase;

namespace PTUDataEditor.ViewModels;
public partial class StatsViewModel : ObservableObject
{
    public Stats BuildModel() => new()
    {
        HP = _HP,
        PhysicalAttack = _PhysicalAttack,
        SpecialAttack = _SpecialAttack,
        PhysicalDefense = _PhysicalDefense,
        SpecialDefense = _SpecialDefense,
        Speed = _Speed,
    };

    public StatsViewModel(Stats model)
    {
        _HP = model.HP;
        _PhysicalAttack = model.PhysicalAttack;
        _SpecialAttack = model.SpecialAttack;
        _PhysicalDefense = model.PhysicalDefense;
        _SpecialDefense = model.SpecialDefense;
        _Speed = model.Speed;
    }

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(Total))]
    private int _HP;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(Total))]
    private int _PhysicalAttack;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(Total))]
    private int _SpecialAttack;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(Total))]
    private int _PhysicalDefense;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(Total))]
    private int _SpecialDefense;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(Total))]
    private int _Speed;

    public int Total => HP + PhysicalAttack + SpecialAttack + PhysicalDefense + SpecialDefense + Speed;
}
