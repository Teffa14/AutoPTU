using System.Globalization;
using System.Windows.Data;

namespace PTUDataEditor.TypeConverters;

public class EnumActualNameTypeConverter : IValueConverter
{
    public object? Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is null || targetType != typeof(string))
            return null;

        var getActualName = typeof(PTUDatabase.Utilities).GetMethod("GetActualName")!.MakeGenericMethod(value.GetType());
        return getActualName?.Invoke(null, new[] { value });
    }

    public object? ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is null || !targetType.IsEnum)
            return null;

        try
        {
            var parseActualName = typeof(PTUDatabase.Utilities).GetMethod("ParseActualName")!.MakeGenericMethod(targetType);
            return parseActualName?.Invoke(null, new[] { value });
        }
        catch (ArgumentException)
        {
            return null;
        }
    }
}
