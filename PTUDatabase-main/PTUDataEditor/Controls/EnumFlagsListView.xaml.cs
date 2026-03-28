using System.ComponentModel;
using System.Diagnostics;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using PTUDataEditor.ViewModels;

namespace PTUDataEditor.Controls;

// This control is held together only by hopes and dreams, and should be rewritten properly at some point.
public partial class EnumFlagsListView : ListView, INotifyPropertyChanged
{
    public EnumFlagsListView()
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
                UpdateListItems(value);
                PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(EnumType)));
            }
        }
    }

    private void UpdateListItems(Type enumType)
    {
        var getActualName = typeof(PTUDatabase.Utilities).GetMethod("GetActualName")!.MakeGenericMethod(enumType);

        if (listItems is not null)
            foreach (var item in listItems)
                item.PropertyChanged -= Item_SelectedChanged;

        var values = Enum.GetValues(EnumType);
        var valueInt = Convert.ToUInt64(Value);
        listItems = values.Cast<object>()
            .Where(v => Convert.ToUInt64(v) != 0)
            .Select(v => new EnumFlagViewModel()
            {
                EnumFlag = v,
                Selected = (valueInt & Convert.ToUInt64(v)) != 0,
                Name = (string)getActualName?.Invoke(null, new[] { v })!
            })
            .ToList();

        var cv = new ListCollectionView(listItems);
        cv.SortDescriptions.Add(new SortDescription(nameof(EnumFlagViewModel.Selected), ListSortDirection.Descending));
        cv.SortDescriptions.Add(new SortDescription(nameof(EnumFlagViewModel.Name), ListSortDirection.Ascending));
        cv.IsLiveSorting = true;
        cv.LiveSortingProperties.Add(nameof(EnumFlagViewModel.Selected));
        BindingOperations.SetBinding(this, ItemsSourceProperty, new Binding() { Source = cv });

        foreach (var item in listItems)
            item.PropertyChanged += Item_SelectedChanged;
    }

    private void Item_SelectedChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (suppressUpdate || e.PropertyName != nameof(EnumFlagViewModel.Selected)) return;

        ulong value = 0UL;
        foreach (var item in listItems)
        {
            if (item.Selected)
                value |= Convert.ToUInt64(item.EnumFlag);
        }
        Value = Enum.ToObject(_enumType, value);
    }

    private List<EnumFlagViewModel> listItems = new();
    private bool suppressUpdate = false;


    public event PropertyChangedEventHandler? PropertyChanged;

    public object Value
    {
        get => GetValue(ValueProperty);
        set => SetValue(ValueProperty, value);
    }
    public static readonly DependencyProperty ValueProperty
        = DependencyProperty.Register(nameof(Value), typeof(object), typeof(EnumFlagsListView), new PropertyMetadata(0, ValueChanged));

    private static void ValueChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        var listView = d as EnumFlagsListView;
        Debug.Assert(listView is not null);
        listView.suppressUpdate = true;
        try
        {
            var newValue = Convert.ToUInt64(e.NewValue);
            foreach (var item in listView.listItems)
            {
                var flag = Convert.ToUInt64(item.EnumFlag);
                item.Selected = (newValue & flag) == flag;
            }
        }
        finally
        {
            listView.suppressUpdate = false;
        }
    }
}
