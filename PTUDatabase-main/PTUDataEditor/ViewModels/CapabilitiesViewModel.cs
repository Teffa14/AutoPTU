using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using PTUDatabase;

namespace PTUDataEditor.ViewModels;
public partial class CapabilitiesViewModel : ObservableObject
{
    public Capabilities BuildModel() => new()
    {
        Overland = _Overland,
        Swim = _Swim,
        Sky = _Sky,
        Levitate = _Levitate,
        Burrow = _Burrow,
        Teleporter = _Teleporter,
        HighJump = _HighJump,
        LongJump = _LongJump,
        Power = _Power,
        Mountable = _Mountable,
        NaturewalkTypes = _NaturewalkTypes,
        Others = _Others,
    };

    public CapabilitiesViewModel(Capabilities model)
    {
        _Overland = model.Overland;
        _Swim = model.Swim;
        _Sky = model.Sky;
        _Levitate = model.Levitate;
        _Burrow = model.Burrow;
        _Teleporter = model.Teleporter;
        _HighJump = model.HighJump;
        _LongJump = model.LongJump;
        _Power = model.Power;
        _Mountable = model.Mountable;
        _NaturewalkTypes = new(model.NaturewalkTypes);
        _Others = new(model.Others);
    }

    [ObservableProperty]
    private int _Overland;

    [ObservableProperty]
    private int _Swim;

    [ObservableProperty]
    private int _Sky;

    [ObservableProperty]
    private int _Levitate;

    [ObservableProperty]
    private int _Burrow;

    [ObservableProperty]
    private int _Teleporter;

    [ObservableProperty]
    private int _HighJump;

    [ObservableProperty]
    private int _LongJump;

    [ObservableProperty]
    private int _Power;

    [ObservableProperty]
    private int _Mountable;

    [ObservableProperty]
    private ObservableCollection<TerrainType> _NaturewalkTypes;

    [ObservableProperty]
    private ObservableCollection<OtherCapability> _Others;
}
