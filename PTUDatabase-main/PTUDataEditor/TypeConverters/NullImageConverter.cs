using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace PTUDataEditor.TypeConverters;
public class NullImageConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (string.IsNullOrEmpty(value as string))
            return DependencyProperty.UnsetValue;
        return value;
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        return Binding.DoNothing;
    }
}
