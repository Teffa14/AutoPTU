using System.ComponentModel;
using System.Diagnostics;
using System.Text.RegularExpressions;

namespace PTUDatabase;

public static class Utilities
{
    [DebuggerHidden]
    public static string GetActualName<T>(T enumValue) where T : Enum
    {
        if (typeof(T).GetCustomAttributes(typeof(FlagsAttribute), false).Length == 0)
            return GetActualNameNoFlags<T>(enumValue);

        ulong result = Convert.ToUInt64(enumValue);
        var values = (T[])Enum.GetValues(typeof(T));
        var foundNames = new List<string>();
        for (int i = values.Length - 1; i >= 0; --i)
        {
            var asInt = Convert.ToUInt64(values[i]);
            if ((result & asInt) != 0)
            {
                result -= asInt;
                foundNames.Add(GetActualNameNoFlags((T)Enum.ToObject(typeof(T), values[i])));
            }
        }

        if (result > 0)
            throw new ArgumentException($"Invalid enum value: \"{enumValue}\"", nameof(enumValue));

        return string.Join(", ", foundNames);
    }

    private static string GetActualNameNoFlags<T>(T enumValue) where T : Enum
    {
        var valueName = Enum.GetName(typeof(T), enumValue) ?? throw new IndexOutOfRangeException("Invalid value.");
        var member = typeof(T).GetMember(valueName).Single();
        var attr = member.GetCustomAttributes(typeof(DescriptionAttribute), false).Cast<DescriptionAttribute>().SingleOrDefault();

        if (attr is DescriptionAttribute { Description: var name }) return name;

        return Regex.Replace(valueName, @"(?!^)(?=[0-9A-Z])", " "); // Add a space before every capital letter.
    }

    [DebuggerHidden]
    public static T ParseActualName<T>(string name) where T : Enum
    {
        if (TryParseActualName<T>(name, out T value))
            return value;
        else
            throw new ArgumentException($"Invalid enum name: \"{name}\"", nameof(name));
    }

    [DebuggerHidden]
    public static bool TryParseActualName<T>(string name, out T result) where T : Enum
    {
        ulong resultValue = 0;
        bool found = false;

        var names = name.Split(',').Select(s => s.Trim()).ToList();
        foreach (var value in Enum.GetValues(typeof(T)).Cast<T>())
        {
            var properName = GetActualName((T)Enum.ToObject(typeof(T), value));
            foreach (var splitName in names)
            {
                if (string.Compare(properName, splitName, ignoreCase: true) == 0)
                {
                    resultValue |= Convert.ToUInt64(value);
                    found = true;
                }
            }
        }

        result = (T)Enum.ToObject(typeof(T), resultValue);
        return found;
    }
}

