using System.ComponentModel;

namespace PTUDatabase;

public enum MoveRangeType
{
    Unknown,
    Self,
    Melee,
    CardinallyAdjacentTargets,
    Any,
    [Description("WR")]
    WeaponRange,
    Burst,
    Ranged,
    Line,
    Cone,
    Blast, // Close and Ranged
    Field,
    Blessing,
}
