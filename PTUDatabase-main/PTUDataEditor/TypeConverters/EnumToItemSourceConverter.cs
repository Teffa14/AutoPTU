using System.Globalization;
using System.Windows.Data;

namespace PTUDataEditor.TypeConverters;

internal class EnumToItemSourceConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        return Enum.GetValues((value as Type)!);
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        return Binding.DoNothing;
    }
}
