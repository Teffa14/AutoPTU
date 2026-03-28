using CommunityToolkit.Mvvm.ComponentModel;
using System.Collections.ObjectModel;
using PTUDatabase;
using System.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace PTUDataEditor.ViewModels;

public partial class FormViewModel : ObservableObject
{
    public Form BuildModel(IReadOnlyList<Move> allMoves, IReadOnlyList<Ability> allAbilities)
    {
        SortMovesAndAbilities();
        return new()
        {
            Name = Name,
            ImageUrl = ImageUrl == "" ? null : ImageUrl,
            BaseStats = BaseStats.BuildModel(),
            Types = Types,
            Abilities = Abilities.Select(avm => avm.BuildModel(allAbilities)).ToList(),
            Moves = Moves.Select(mvm => mvm.BuildModel(allMoves)).ToList(),
            BaseSkills = BaseSkills,
            Capabilities = Capabilities.BuildModel(),
            AverageSize = (AverageSizeMeters, AverageSizeInches, SizeClass),
            AverageWeight = (AverageWeightKilograms, 0f, 0),
            MaleFemaleRatio = HasGender ? MaleFemaleRatio : null,
            EggGroups = EggGroups,
            SelectionWeight = SelectionWeight,
        };
    }

    public FormViewModel(Form model, DatabaseViewModel db)
    {
        _Name = model.Name;
        _ImageUrl = model.ImageUrl ?? "";
        _BaseStats = new(model.BaseStats);
        _Types = new(model.Types);
        _Abilities = new(model.Abilities.Select(ability => new AbilityRequirementViewModel(ability, db.Abilities)));
        _Moves = new(model.Moves.Select(move => new MoveRequirementViewModel(move, db.Moves)));
        _BaseSkills = model.BaseSkills;
        _Capabilities = new(model.Capabilities);
        _AverageSizeMeters = model.AverageSize.Meters;
        _SizeClass = model.AverageSize.Class;
        _AverageWeightKilograms = model.AverageWeight.Kilograms;
        _MaleFemaleRatio = model.MaleFemaleRatio ?? 0.5f;
        _HasGender = model.MaleFemaleRatio.HasValue;
        _EggGroups = new(model.EggGroups);
        _SelectionWeight = model.SelectionWeight;
        rootDB = db;
    }

    private DatabaseViewModel rootDB;

    protected override void OnPropertyChanged(PropertyChangedEventArgs e)
    {
        base.OnPropertyChanged(e);

        if (e.PropertyName is not nameof(ValidationIssues) and not nameof(HasValidationIssues))
            ValidationIssues = Validate();
    }

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(HasValidationIssues))]
    private IReadOnlyList<string> _ValidationIssues = Array.Empty<string>();
    public bool HasValidationIssues => ValidationIssues.Count > 0;

    private List<string> Validate()
    {
        var issues = new List<string>();
        if (string.IsNullOrEmpty(Name)) issues.Add("Missing form name.");
        if (SelectionWeight < 0) issues.Add("Selection weight must be >= 0.");
        if (Types?.Count is null or 0) issues.Add("Missing types.");
        if (EggGroups?.Count is null or 0) issues.Add("Missing egg groups.");
        if (AverageWeightKilograms == 0) issues.Add("Missing weight.");
        if (AverageSizeMeters == 0) issues.Add("Missing size.");
        if (string.IsNullOrEmpty(ImageUrl)) issues.Add("Missing image.");
        if (BaseStats.Total == 0) issues.Add("Missing base stats.");
        if (BaseSkills == Skills.Zero) issues.Add("Missing base skills.");
        if (BaseSkills.AsEnumerable().Any(s => s.Rank < 1)) issues.Add("Some base skills are below the minimum of 1.");
        // TODO: Validate capabilities
        if (Moves?.Count is null or 0) issues.Add("Missing moves.");
        if (Abilities?.Count is null or 0) issues.Add("Missing abilities.");
        return issues;
    }

    [ObservableProperty]
    private string _Name;

    [ObservableProperty]
    private string _ImageUrl;

    [ObservableProperty]
    private StatsViewModel _BaseStats;

    [ObservableProperty]
    private ObservableCollection<PokemonType> _Types;

    [ObservableProperty]
    private ObservableCollection<AbilityRequirementViewModel> _Abilities;

    [ObservableProperty]
    private ObservableCollection<MoveRequirementViewModel> _Moves;

    [RelayCommand]
    private void AddMove()
    {
        if (rootDB.Moves.Count == 0) return;
        Moves.Add(new MoveRequirementViewModel(rootDB.Moves[0]));
    }

    [RelayCommand]
    private void RemoveMove(MoveRequirementViewModel move)
    {
        var force = (System.Windows.Input.Keyboard.Modifiers & System.Windows.Input.ModifierKeys.Shift) != 0;
        var result = force ? System.Windows.MessageBoxResult.Yes : System.Windows.MessageBox.Show(
            $"Are you sure you would like to remove {move.Move.Name}?", "Remove Form Move",
            System.Windows.MessageBoxButton.YesNo, System.Windows.MessageBoxImage.Warning, System.Windows.MessageBoxResult.No);
        if (result == System.Windows.MessageBoxResult.Yes)
            Moves.Remove(move);
    }

    [RelayCommand]
    private void AddAbility()
    {
        if (rootDB.Abilities.Count == 0) return;
        Abilities.Add(new AbilityRequirementViewModel(rootDB.Abilities[0]));
    }

    [RelayCommand]
    private void RemoveAbility(AbilityRequirementViewModel ability)
    {
        var force = (System.Windows.Input.Keyboard.Modifiers & System.Windows.Input.ModifierKeys.Shift) != 0;
        var result = force ? System.Windows.MessageBoxResult.Yes : System.Windows.MessageBox.Show(
            $"Are you sure you would like to remove {ability.Ability.Name}?", "Remove Form Ability",
            System.Windows.MessageBoxButton.YesNo, System.Windows.MessageBoxImage.Warning, System.Windows.MessageBoxResult.No);
        if (result == System.Windows.MessageBoxResult.Yes)
            Abilities.Remove(ability);
    }

    private void SortMovesAndAbilities()
    {
        var sortedMoves = Moves
            .OrderBy(m => m.RequirementType)
            .ThenBy(m => m.RequirementType switch
            {
                MoveRequirementType.Level => (IComparable)m.RequiredLevel,
                MoveRequirementType.Machine => m.MachineId,
                _ => 0,
            })
            .ThenBy(m => m.Move.Name);
        Moves = new(sortedMoves);

        var sortedAbilities = Abilities
            .OrderBy(a => a.RequirementType)
            .ThenBy(a => a.Ability.Name);
        Abilities = new(sortedAbilities);

    }


    [ObservableProperty]
    private Skills _BaseSkills = Skills.Minimum;

    [ObservableProperty]
    private CapabilitiesViewModel _Capabilities;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(AverageSizeInches))]
    [NotifyPropertyChangedFor(nameof(AverageSizeFeetInches))]
    private float _AverageSizeMeters;
    public float AverageSizeInches
    {
        get => AverageSizeMeters * 39.37f;
        set => AverageSizeMeters = value / 39.37f;
    }
    public string AverageSizeFeetInches => $"{(int)Math.Round(AverageSizeInches) / 12}' {(int)Math.Round(AverageSizeInches) % 12}\"";

    [ObservableProperty]
    private SizeClass _SizeClass = SizeClass.Small;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(AverageWeightPounds))]
    [NotifyPropertyChangedFor(nameof(WeightClass))]
    private float _AverageWeightKilograms;
    public float AverageWeightPounds
    {
        get => AverageWeightKilograms * 2.2f;
        set => AverageWeightKilograms = value / 2.2f;
    }
    public int WeightClass => AverageWeightKilograms switch
    {
        < 11.001f => 1,
        < 25.001f => 2,
        < 50.001f => 3,
        < 100.001f => 4,
        < 200.001f => 5,
        _ => 6,
    };

    [ObservableProperty]
    private float _MaleFemaleRatio;

    [ObservableProperty]
    private bool _HasGender;

    [ObservableProperty]
    private ObservableCollection<EggGroup> _EggGroups;

    [ObservableProperty]
    private float _SelectionWeight;
}
