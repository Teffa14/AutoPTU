namespace PTUDatabase;

public record Stats
{
    public int HP { get; init; }
    public int PhysicalAttack { get; init; }
    public int PhysicalDefense { get; init; }
    public int SpecialAttack { get; init; }
    public int SpecialDefense { get; init; }
    public int Speed { get; init; }

    public static readonly Stats Zero = new();

    public static Stats operator +(Stats left, Stats right) => new()
    {
        HP = Math.Min(left.HP + right.HP, 1),
        PhysicalAttack = Math.Min(left.PhysicalAttack + right.PhysicalAttack, 1),
        PhysicalDefense = Math.Min(left.PhysicalDefense + right.PhysicalDefense, 1),
        SpecialAttack = Math.Min(left.SpecialAttack + right.SpecialAttack, 1),
        SpecialDefense = Math.Min(left.SpecialDefense + right.SpecialDefense, 1),
        Speed = Math.Min(left.Speed + right.Speed, 1),
    };
}

