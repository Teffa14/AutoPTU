using System.ComponentModel;
using System.Windows.Markup;

namespace PTUDataEditor.TypeConverters;

// Source: https://stackoverflow.com/a/4398752/87834
public class EnumExtension : MarkupExtension
{
    public EnumExtension(Type enumType)
    {
        if (enumType == null)
            throw new ArgumentNullException("enumType");

        enumType = Nullable.GetUnderlyingType(enumType) ?? enumType;

        if (enumType.IsEnum == false)
            throw new ArgumentException("Type must be an Enum.");

        EnumType = enumType;
    }

    public Type EnumType { get; }

    public override object ProvideValue(IServiceProvider serviceProvider) // or IXamlServiceProvider for UWP and WinUI
    {
        return Enum.GetValues(EnumType)
            .Cast<object>()
            .Select(enumValue => new EnumerationMember(GetDescription(enumValue), enumValue))
            .ToArray();
    }

    private string? GetDescription(object enumValue)
    {
        var descriptionAttribute = EnumType.GetField(enumValue.ToString()!)
          ?.GetCustomAttributes(typeof(DescriptionAttribute), false)
          .FirstOrDefault() as DescriptionAttribute;

        return descriptionAttribute != null
          ? descriptionAttribute.Description
          : enumValue.ToString();
    }

    public record struct EnumerationMember(string? Description, object? Value);
}
