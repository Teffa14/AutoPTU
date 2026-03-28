namespace PTUDatabase;

public record Move
{
    public string Name { get; init; } = "";
    public PokemonType Type { get; init; }
    public MoveClass Class { get; init; }
    public int? DamageBase { get; init; }
    [YamlDotNet.Serialization.YamlIgnore]
    public (string Dice, int Minimum, int Average, int Maximum)? Damage => DamageBase is int ? DamageBaseData[System.Math.Clamp(DamageBase ?? 1, 1, 28)] : DamageBaseData[0];
    public Frequency Frequency { get; init; } = Frequency.AtWill();
    public int? AccuracyCheck { get; init; }
    public string Range { get; init; } = "";
    //public IList<MoveRange> Ranges { get; init; } = Array.Empty<MoveRange>(); // Disabled this because we really don't need it for our purposes, and would add more cleanup work.
    public ContestType ContestType { get; init; }
    public ContestEffect ContestEffect { get; init; } = ContestEffect.None;
    public string Effects { get; init; } = "";
    public bool UnofficialAlternative { get; init; } = false;

    public override string ToString() => Name;

    public static readonly Move None = new() { Name = "None" };

    public static readonly (string Dice, int Minimum, int Average, int Maximum)[] DamageBaseData = new[]
    {
            (    "--"  ,   0,   0,   0), // Invalid
            ( "1d6 + 1",   2,   5,   7), // 1
            ( "1d6 + 3",   4,   7,   9),
            ( "1d6 + 5",   6,   9,  11),
            ( "1d8 + 6",   7,  11,  14),
            ( "1d8 + 8",   9,  13,  16), // 5
            ( "2d6 + 8",  10,  15,  20),
            ( "2d6 + 10", 12,  17,  22),
            ( "2d8 + 10", 12,  19,  26),
            ("2d10 + 10", 12,  21,  30),
            ( "3d8 + 10", 13,  24,  34), // 10
            ("3d10 + 10", 13,  27,  40),
            ("3d12 + 10", 13,  30,  46),
            ("4d10 + 10", 14,  35,  50),
            ("4d10 + 15", 19,  40,  55),
            ("4d10 + 20", 24,  45,  60), // 15
            ("5d10 + 20", 25,  50,  70),
            ("5d12 + 25", 30,  60,  85),
            ("6d12 + 25", 31,  65,  97),
            ("6d12 + 30", 36,  70, 102),
            ("6d12 + 35", 41,  75, 107), // 20
            ("6d12 + 40", 46,  80, 112),
            ("6d12 + 45", 51,  85, 117),
            ("6d12 + 50", 56,  90, 122),
            ("6d12 + 55", 61,  95, 127),
            ("6d12 + 60", 66, 100, 132), // 25
            ("7d12 + 65", 72, 110, 149),
            ("8d12 + 70", 78, 120, 166),
            ("8d12 + 80", 88, 130, 176), // 28
        };
}

