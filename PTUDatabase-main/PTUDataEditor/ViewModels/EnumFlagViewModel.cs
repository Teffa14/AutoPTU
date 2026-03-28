using CommunityToolkit.Mvvm.ComponentModel;

namespace PTUDataEditor.ViewModels;

public partial class EnumFlagViewModel : ObservableObject
{
    [ObservableProperty]
    private object _EnumFlag = 0;

    [ObservableProperty]
    private bool _Selected = false;

    [ObservableProperty]
    private string _Name = "";
}
