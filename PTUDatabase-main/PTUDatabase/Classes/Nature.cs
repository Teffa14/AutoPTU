namespace PTUDatabase;

public record Nature
{
    public string Name { get; init; } = "";
    public Stats StatChange { get; init; } = Stats.Zero;

    public static readonly Nature Cuddly = new() { Name = nameof(Cuddly), StatChange = new() { HP = 1, PhysicalAttack = -2 } };
    public static readonly Nature Distracted = new() { Name = nameof(Distracted), StatChange = new() { HP = 1, PhysicalDefense = -2 } };
    public static readonly Nature Proud = new() { Name = nameof(Proud), StatChange = new() { HP = 1, SpecialAttack = -2 } };
    public static readonly Nature Decisive = new() { Name = nameof(Decisive), StatChange = new() { HP = 1, SpecialDefense = -2 } };
    public static readonly Nature Patient = new() { Name = nameof(Patient), StatChange = new() { HP = 1, Speed = -2 } };

    public static readonly Nature Desperate = new() { Name = nameof(Desperate), StatChange = new() { PhysicalAttack = 2, HP = -1 } };
    public static readonly Nature Lonely = new() { Name = nameof(Lonely), StatChange = new() { PhysicalAttack = 2, PhysicalDefense = -2 } };
    public static readonly Nature Adamant = new() { Name = nameof(Adamant), StatChange = new() { PhysicalAttack = 2, SpecialAttack = -2 } };
    public static readonly Nature Naughty = new() { Name = nameof(Naughty), StatChange = new() { PhysicalAttack = 2, SpecialDefense = -2 } };
    public static readonly Nature Brave = new() { Name = nameof(Brave), StatChange = new() { PhysicalAttack = 2, Speed = -2 } };

    public static readonly Nature Stark = new() { Name = nameof(Desperate), StatChange = new() { PhysicalDefense = 2, HP = -1 } };
    public static readonly Nature Bold = new() { Name = nameof(Lonely), StatChange = new() { PhysicalDefense = 2, PhysicalAttack = -2 } };
    public static readonly Nature Impish = new() { Name = nameof(Adamant), StatChange = new() { PhysicalDefense = 2, SpecialAttack = -2 } };
    public static readonly Nature Lax = new() { Name = nameof(Naughty), StatChange = new() { PhysicalDefense = 2, SpecialDefense = -2 } };
    public static readonly Nature Relaxed = new() { Name = nameof(Brave), StatChange = new() { PhysicalDefense = 2, Speed = -2 } };

    public static readonly Nature Curious = new() { Name = nameof(Curious), StatChange = new() { SpecialAttack = 2, HP = -1 } };
    public static readonly Nature Modest = new() { Name = nameof(Modest), StatChange = new() { SpecialAttack = 2, PhysicalAttack = -2 } };
    public static readonly Nature Mild = new() { Name = nameof(Mild), StatChange = new() { SpecialAttack = 2, PhysicalDefense = -2 } };
    public static readonly Nature Rash = new() { Name = nameof(Rash), StatChange = new() { SpecialAttack = 2, SpecialDefense = -2 } };
    public static readonly Nature Quiet = new() { Name = nameof(Quiet), StatChange = new() { SpecialAttack = 2, Speed = -2 } };

    public static readonly Nature Dreamy = new() { Name = nameof(Dreamy), StatChange = new() { SpecialDefense = 2, HP = -1 } };
    public static readonly Nature Calm = new() { Name = nameof(Calm), StatChange = new() { SpecialDefense = 2, PhysicalAttack = -2 } };
    public static readonly Nature Gentle = new() { Name = nameof(Gentle), StatChange = new() { SpecialDefense = 2, PhysicalDefense = -2 } };
    public static readonly Nature Careful = new() { Name = nameof(Careful), StatChange = new() { SpecialDefense = 2, SpecialAttack = -2 } };
    public static readonly Nature Sassy = new() { Name = nameof(Sassy), StatChange = new() { SpecialDefense = 2, Speed = -2 } };

    public static readonly Nature Skittish = new() { Name = nameof(Skittish), StatChange = new() { Speed = 2, HP = -1 } };
    public static readonly Nature Timid = new() { Name = nameof(Timid), StatChange = new() { Speed = 2, PhysicalAttack = -2 } };
    public static readonly Nature Hasty = new() { Name = nameof(Hasty), StatChange = new() { Speed = 2, PhysicalDefense = -2 } };
    public static readonly Nature Jolly = new() { Name = nameof(Jolly), StatChange = new() { Speed = 2, SpecialAttack = -2 } };
    public static readonly Nature Naive = new() { Name = nameof(Naive), StatChange = new() { Speed = 2, SpecialDefense = -2 } };

    public static readonly Nature Composed = new() { Name = nameof(Composed), StatChange = Stats.Zero };
    public static readonly Nature Hardy = new() { Name = nameof(Hardy), StatChange = Stats.Zero };
    public static readonly Nature Docile = new() { Name = nameof(Docile), StatChange = Stats.Zero };
    public static readonly Nature Bashful = new() { Name = nameof(Bashful), StatChange = Stats.Zero };
    public static readonly Nature Quirky = new() { Name = nameof(Quirky), StatChange = Stats.Zero };
    public static readonly Nature Serious = new() { Name = nameof(Serious), StatChange = Stats.Zero };

    public static readonly IReadOnlyList<Nature> All = new[] {
            Cuddly, Distracted, Proud, Decisive, Patient, // +HP
            Desperate, Lonely, Adamant, Naughty, Brave,   // +P.Atk
            Stark, Bold, Impish, Lax, Relaxed,            // +P.Def
            Curious, Modest, Mild, Rash, Quiet,           // +S.Atk
            Dreamy, Calm, Gentle, Careful, Sassy,         // +S.Def
            Skittish, Timid, Hasty, Jolly, Naive,         // +Spd
            Composed, Hardy, Docile, Bashful, Quirky, Serious, // Neutral
        };
}

