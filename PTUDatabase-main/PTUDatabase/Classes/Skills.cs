using System.Collections;

namespace PTUDatabase;

public record Skills
{
    // Body Skills
    public (int Rank, int Bonus) Intimidate { get; init; }
    public (int Rank, int Bonus) Survival { get; init; }
    public (int Rank, int Bonus) Athletics { get; init; }
    public (int Rank, int Bonus) Acrobatics { get; init; }
    public (int Rank, int Bonus) Combat { get; init; }
    public (int Rank, int Bonus) Stealth { get; init; }
    // Mind Skills
    public (int Rank, int Bonus) GeneralEducation { get; init; }
    public (int Rank, int Bonus) MedicineEducation { get; init; }
    public (int Rank, int Bonus) OccultEducation { get; init; }
    public (int Rank, int Bonus) PokemonEducation { get; init; }
    public (int Rank, int Bonus) TechnologyEducation { get; init; }
    public (int Rank, int Bonus) Guile { get; init; }
    public (int Rank, int Bonus) Perception { get; init; }
    // Spirit Skills
    public (int Rank, int Bonus) Charm { get; init; }
    public (int Rank, int Bonus) Command { get; init; }
    public (int Rank, int Bonus) Intuition { get; init; }
    public (int Rank, int Bonus) Focus { get; init; }

    public static readonly Skills Zero = new();
    public static readonly Skills Minimum = new()
    {
        Athletics = (1, 0),
        Acrobatics = (1, 0),
        Combat = (1, 0),
        Stealth = (1, 0),
        Intimidate = (1, 0),
        Survival = (1, 0),
        Perception = (1, 0),
        GeneralEducation = (1, 0),
        MedicineEducation = (1, 0),
        OccultEducation = (1, 0),
        PokemonEducation = (1, 0),
        TechnologyEducation = (1, 0),
        Focus = (1, 0),
        Guile = (1, 0),
        Charm = (1, 0),
        Command = (1, 0),
        Intuition = (1, 0),
    };

    public IEnumerable<(string Name, int Rank, int Bonus)> AsEnumerable()
    {
        yield return ("Athletics", Athletics.Rank, Athletics.Bonus);
        yield return ("Acrobatics", Acrobatics.Rank, Acrobatics.Bonus);
        yield return ("Combat", Combat.Rank, Combat.Bonus);
        yield return ("Stealth", Stealth.Rank, Stealth.Bonus);
        yield return ("Intimidate", Intimidate.Rank, Intimidate.Bonus);
        yield return ("Survival", Survival.Rank, Survival.Bonus);
        yield return ("Perception", Perception.Rank, Perception.Bonus);
        yield return ("General Edu.", GeneralEducation.Rank, GeneralEducation.Bonus);
        yield return ("Medicine Edu.", MedicineEducation.Rank, MedicineEducation.Bonus);
        yield return ("Occult Edu.", OccultEducation.Rank, OccultEducation.Bonus);
        yield return ("Pokemon Edu.", PokemonEducation.Rank, PokemonEducation.Bonus);
        yield return ("Technology Edu.", TechnologyEducation.Rank, TechnologyEducation.Bonus);
        yield return ("Focus", Focus.Rank, Focus.Bonus);
        yield return ("Guile", Guile.Rank, Guile.Bonus);
        yield return ("Charm", Charm.Rank, Charm.Bonus);
        yield return ("Command", Command.Rank, Command.Bonus);
        yield return ("Intuition", Intuition.Rank, Intuition.Bonus);
    }
}

