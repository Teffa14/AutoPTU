using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace PTUDataEditor.Controls;

/// <summary>
/// Interaction logic for EditableListBox.xaml
/// </summary>
public partial class EditableListBox : ListBox
{
    public EditableListBox()
    {
        InitializeComponent();
    }




    public ICommand Add
    {
        get { return (ICommand)GetValue(AddProperty); }
        set { SetValue(AddProperty, value); }
    }

    public static readonly DependencyProperty AddProperty = DependencyProperty.Register("Add", typeof(ICommand), typeof(EditableListBox));


    public ICommand Remove
    {
        get { return (ICommand)GetValue(RemoveProperty); }
        set { SetValue(RemoveProperty, value); }
    }

    public static readonly DependencyProperty RemoveProperty = DependencyProperty.Register("Remove", typeof(ICommand), typeof(EditableListBox));




    private void RemoveBtn_Click(object sender, RoutedEventArgs e)
    {
        var collection = ItemsSource as dynamic;
        if (collection is not null)
            collection.RemoveAt(SelectedIndex);
    }

    private void AddBtn_Click(object sender, RoutedEventArgs e)
    {
        var collection = ItemsSource as dynamic;
        if (collection is null)
            collection = ItemsSource = new ObservableCollection<object>();
        var newItem = (dynamic)NewItem!.Invoke();
        collection.Add(newItem);
        SelectedItem = newItem;
    }

    public event Func<object>? NewItem;
}
