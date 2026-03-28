using System.Globalization;
using System.Windows.Data;

namespace PTUDataEditor.TypeConverters;

public sealed class BoolConverter : IValueConverter
{
    public object? True { get; set; }
    public object? False { get; set; }

    public object? Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is not bool) return null;
        return (bool)value ? True : False;
    }

    public object? ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (Equals(value, True))
            return true;
        if (Equals(value, False))
            return false;
        return null;
    }
}
