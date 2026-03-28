using System.ComponentModel;
using System.Windows.Controls;

namespace PTUDataEditor.Controls;

public partial class EnumListView : ListBox, INotifyPropertyChanged
{
    public EnumListView()
    {
        InitializeComponent();
    }

    private Type _enumType = typeof(Type);
    public Type EnumType
    {
        get => _enumType;
        set
        {
            if (value != _enumType)
            {
                _enumType = value;
                ItemsSource = Enum.GetValues(EnumType);
                PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(EnumType)));
            }
        }
    }



    public event PropertyChangedEventHandler? PropertyChanged;
}
