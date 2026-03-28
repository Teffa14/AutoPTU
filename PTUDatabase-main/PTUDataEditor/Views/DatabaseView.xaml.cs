using System.Windows.Controls;
using PTUDataEditor.ViewModels;

namespace PTUDataEditor.Views;

/// <summary>
/// Interaction logic for DatabaseView.xaml
/// </summary>
public partial class DatabaseView : UserControl
{
    public DatabaseView()
    {
        InitializeComponent();

#if DEBUG
        // Quickly load ptu.1.05.yaml to speed up debugging.
        DataContext = DatabaseViewModel.DesignData;
        // TODO: Ensure things work correctly when nothing is loaded here. As of writing this, things don't.
#endif
    }
}
