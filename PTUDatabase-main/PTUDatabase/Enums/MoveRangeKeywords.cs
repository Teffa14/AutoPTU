using System.ComponentModel;

namespace PTUDatabase;

[System.Flags]
public enum MoveRangeKeywords : ulong
{
    None = 0,
    AllAdjacentFoes = 1UL << 0,
    AllCardinallyAdjacentTargets = 1UL << 1,
    Aura = 1UL << 2,
    Berry = 1UL << 3,
    Blessing = 1UL << 4,
    Coat = 1UL << 5,
    Dash = 1UL << 6,
    DoubleStrike = 1UL << 7,
    Environ = 1UL << 8,
    Execute = 1UL << 9,
    Exhaust = 1UL << 10,
    ExtendedAction = 1UL << 11,
    Fling = 1UL << 12,
    FreeAction = 1UL << 13,
    Friendly = 1UL << 14,
    FiveStrike = 1UL << 15,
    FullAction = 1UL << 16,
    Groundsource = 1UL << 17,
    Hazard = 1UL << 18,
    Healing = 1UL << 19,
    [Description("HP Loss")]
    HPLoss = 1UL << 20,
    Illusion = 1UL << 21,
    Interrupt = 1UL << 22,
    Pass = 1UL << 23,
    Pledge = 1UL << 24,
    Powder = 1UL << 25,
    Priority = 1UL << 26,
    [Description("Priority (Limited)")]
    PriorityLimited = 1UL << 27,
    Push = 1UL << 28,
    Reaction = 1UL << 29,
    [Description("Recoil 1/4")]
    RecoilFourth = 1UL << 30,
    [Description("Recoil 1/3")]
    RecoilThird = 1UL << 31,
    [Description("Recoil 1/2")]
    RecoilHalf = 1UL << 32,
    [Description("Set-Up")]
    SetUp = 1UL << 33,
    Shield = 1UL << 34,
    ShiftAction = 1UL << 35,
    Smite = 1UL << 36,
    Social = 1UL << 37,
    Sonic = 1UL << 38,
    SpiritSurge = 1UL << 39,
    StandardAction = 1UL << 40,
    SwiftAction = 1UL << 41,
    Trigger = 1UL << 42,
    Vortex = 1UL << 43,
    Weather = 1UL << 44,
    Hail = 1UL << 45,
    Rainy = 1UL << 46,
    Sandstorm = 1UL << 47,
    Sunny = 1UL << 48,
    WeightClass = 1UL << 49,

    SeeEffect = 1UL << 50,
}
