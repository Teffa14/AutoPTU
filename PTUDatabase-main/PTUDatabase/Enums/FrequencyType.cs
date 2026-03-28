using System.ComponentModel;

namespace PTUDatabase;

public enum FrequencyType
{
    [Description("At-Will")]
    AtWill,
    [Description("EOT")]
    EveryOtherTurn,
    Scene,
    Daily,
    Static,
    Varies,
}
