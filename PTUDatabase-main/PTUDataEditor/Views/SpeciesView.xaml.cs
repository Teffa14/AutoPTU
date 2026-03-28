using System.Windows;
using System.Windows.Controls;
using PTUDataEditor.ViewModels;

namespace PTUDataEditor.Views;
/// <summary>
/// Interaction logic for SpeciesView.xaml
/// </summary>
public partial class SpeciesView : UserControl
{
    public SpeciesView()
    {
        InitializeComponent();
    }



    public bool EditingMoves
    {
        get { return (bool)GetValue(EditingMovesProperty); }
        set { SetValue(EditingMovesProperty, value); }
    }

    public static readonly DependencyProperty EditingMovesProperty =
        DependencyProperty.Register("EditingMoves", typeof(bool), typeof(SpeciesView), new PropertyMetadata(false));



    public bool EditingAbilities
    {
        get { return (bool)GetValue(EditingAbilitiesProperty); }
        set { SetValue(EditingAbilitiesProperty, value); }
    }

    public static readonly DependencyProperty EditingAbilitiesProperty =
        DependencyProperty.Register("EditingAbilities", typeof(bool), typeof(SpeciesView), new PropertyMetadata(false));




    private bool suppressChanged = false;

    private void TypesChanged(object sender, SelectionChangedEventArgs e)
    {
        var types = TypesList.SelectedItems.Cast<PTUDatabase.PokemonType>();
        //var content = string.Join(", ", types);
        //TypesBtn.Content = content == "" ? "None" : content;

        var form = FormsListBox.SelectedItem as FormViewModel;
        if (!suppressChanged && form is not null)
        {
            form.Types.Clear();
            foreach (var type in types)
                form.Types.Add(type);
        }
    }

    private void EggGroupsChanged(object sender, SelectionChangedEventArgs e)
    {
        var groups = EggGroupsList.SelectedItems.Cast<PTUDatabase.EggGroup>();
        var content = string.Join(", ", groups);
        EggGroupsBtn.Content = content == "" ? "None" : content;

        var form = FormsListBox.SelectedItem as FormViewModel;
        if (!suppressChanged && form is not null)
        {
            form.EggGroups.Clear();
            foreach (var group in groups)
                form.EggGroups.Add(group);
        }
    }

    private void FormsListBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        var form = FormsListBox.SelectedItem as FormViewModel;
        suppressChanged = true;
        try
        {
            TypesList.SelectedItems.Clear();
            EggGroupsList.SelectedItems.Clear();
            NaturewalkList.SelectedItems.Clear();
            OtherCapsList.SelectedItems.Clear();
            if (form is not null)
            {
                foreach (var type in form.Types)
                    TypesList.SelectedItems.Add(type);
                foreach (var group in form.EggGroups)
                    EggGroupsList.SelectedItems.Add(group);
                foreach (var terrain in form.Capabilities.NaturewalkTypes)
                    NaturewalkList.SelectedItems.Add(terrain);
                foreach (var cap in form.Capabilities.Others)
                    OtherCapsList.SelectedItems.Add(cap);
            }
        }
        finally
        {
            suppressChanged = false;
        }
    }

    private void EnableEditingMoves(object sender, RoutedEventArgs e)
    {
        EditingMoves = true;
    }

    private void EnableEditingAbilities(object sender, RoutedEventArgs e)
    {
        EditingAbilities = true;
    }

    private void NaturewalkChanged(object sender, SelectionChangedEventArgs e)
    {
        var terrains = NaturewalkList.SelectedItems.Cast<PTUDatabase.TerrainType>();
        var content = string.Join(", ", terrains);
        NaturewalkBtn.Content = content == "" ? "None" : content;

        var form = FormsListBox.SelectedItem as FormViewModel;
        if (!suppressChanged && form is not null)
        {
            form.Capabilities.NaturewalkTypes.Clear();
            foreach (var terrain in terrains)
                form.Capabilities.NaturewalkTypes.Add(terrain);
        }
    }

    private void OtherCapsChanged(object sender, SelectionChangedEventArgs e)
    {
        var caps = OtherCapsList.SelectedItems.Cast<PTUDatabase.OtherCapability>();
        var content = string.Join(", ", caps);
        OtherCapsBtn.Content = content == "" ? "None" : content;

        var form = FormsListBox.SelectedItem as FormViewModel;
        if (!suppressChanged && form is not null)
        {
            form.Capabilities.Others.Clear();
            foreach (var cap in caps)
                form.Capabilities.Others.Add(cap);
        }
    }
}
