using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using PTUDatabase;

namespace PTUDataEditor.TypeConverters;

public class TypeToImageSourceConverter : IValueConverter
{
    private static ImageSource[] typeImages;

    static TypeToImageSourceConverter()
    {
        var allTypes = Enum.GetValues<PokemonType>();
        typeImages = new ImageSource[allTypes.Length];
        foreach (var type in allTypes)
            typeImages[(int)type] = new BitmapImage(new Uri($"pack://application:,,,/PTUDataEditor;component/Resources/Types/{type}.png"));
    }

    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        return typeImages[value is PokemonType type && Enum.IsDefined(type) ? (int)type : 0];
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        return (PokemonType)Math.Max(0, Array.IndexOf(typeImages, value));
    }
}
