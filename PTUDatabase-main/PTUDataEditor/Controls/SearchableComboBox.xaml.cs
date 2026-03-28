using System.ComponentModel;
using System.Windows.Controls;
using System.Windows.Data;

namespace PTUDataEditor.Controls;
/// <summary>
/// Interaction logic for SearchableComboBox.xaml
/// </summary>
public partial class SearchableComboBox : ComboBox
{
    public SearchableComboBox()
    {
        InitializeComponent();
    }

    public override void OnApplyTemplate()
    {
        base.OnApplyTemplate();
        searchBox = (TextBox)GetTemplateChild("PART_FilterTextBox");
        itemsPresenter = (ItemsPresenter)GetTemplateChild("ItemsPresenter");
        filteredSource = (CollectionViewSource)GetTemplateChild("PART_FilteredSource");
        itemsPresenter.DataContext = filteredSource;
    }

    TextBox searchBox;
    ItemsPresenter itemsPresenter;
    CollectionViewSource filteredSource;

    private void ComboBox_DropDownOpened(object sender, EventArgs e)
    {
        searchBox.Text = "";
        Dispatcher.BeginInvoke((SearchableComboBox self) =>
        {
            self.searchBox.Focus();
        }, this);
        if (filteredSource.View is { } view)
        {
            view.Filter = null;
            view.Refresh();
        }
        //filteredSource.View.Filter = null;
        //filteredSource.View.Refresh();
    }

    private void PART_SearchBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        if (filteredSource.View is { } view)
        {
            view.Filter =
                searchBox.Text is null or "" or "Search..."
                ? new Predicate<object>(e => ((dynamic)e).Name.Contains(searchBox.Text))
                : null;
            view.Refresh();
        }
    }

    private void PART_FilterTextBox_GotFocus(object sender, System.Windows.RoutedEventArgs e)
    {
        if (searchBox.Text is null or "Search...")
            searchBox.Text = "";
    }

    private void PART_FilterTextBox_LostFocus(object sender, System.Windows.RoutedEventArgs e)
    {
        if (searchBox.Text is null or "")
            searchBox.Text = "Search...";
    }

    private void PART_FilteredSource_Filter(object sender, FilterEventArgs e)
    {
        e.Accepted = searchBox.Text is null or "" or "Search..." || ((dynamic)e.Item).Name.Contains(searchBox.Text);
    }
}
