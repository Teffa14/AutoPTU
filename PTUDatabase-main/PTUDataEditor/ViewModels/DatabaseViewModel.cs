using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PTUDatabase;

namespace PTUDataEditor.ViewModels;

public partial class DatabaseViewModel : ObservableObject
{
    public Database BuildModel()
    {
        var contestEffects = ContestEffects.Select(vm => vm.BuildModel()).ToList();
        var moves = Moves.Select(vm => vm.BuildModel(contestEffects)).ToList();
        var abilities = Abilities.Select(vm => vm.BuildModel()).ToList();
        var species = Species.Select(vm => vm.BuildModel(moves, abilities)).ToList();
        return new()
        {
            ContestEffects = contestEffects,
            Abilities = abilities,
            Moves = moves,
            Species = species,
        };
    }

    public DatabaseViewModel(Database model)
    {
        _ContestEffects = new(model.ContestEffects.Select(ce => new ContestEffectViewModel(ce)).OrderBy(m => m.Name));
        _Abilities = new(model.Abilities.Select(a => new AbilityViewModel(a)).OrderBy(m => m.Name));
        _Moves = new(model.Moves.Select(m => new MoveViewModel(m, this)).OrderBy(m => m.Name));
        _Species = new(model.Species.Select(s => new SpeciesViewModel(s, this)).OrderBy(m => m.Name));
    }

    [RelayCommand]
    private void AddSpecies() => Species.Add(new SpeciesViewModel(new Species() { Name = "*New Species", Forms = new Form[] { new() { Name = "Normal" } } }, this));
    
    [RelayCommand]
    private void AddMove() => Moves.Add(new MoveViewModel(new Move() { Name = "*New Move" }, this));

    [RelayCommand]
    private void AddAbility() => Abilities.Add(new AbilityViewModel(new Ability() { Name = "*New Ability" }));

    [RelayCommand]
    private void AddContestEffect() => ContestEffects.Add(new ContestEffectViewModel(new ContestEffect() { Name = "*New Contest Effect" }));

    [RelayCommand]
    private void RemoveSpecies(SpeciesViewModel species)
    {
        var force = (System.Windows.Input.Keyboard.Modifiers & System.Windows.Input.ModifierKeys.Shift) != 0;
        var result = force ? System.Windows.MessageBoxResult.Yes : System.Windows.MessageBox.Show(
            $"Are you sure you would like to remove {species.Name}?", "Remove Species",
            System.Windows.MessageBoxButton.YesNo, System.Windows.MessageBoxImage.Warning, System.Windows.MessageBoxResult.No);
        if (result == System.Windows.MessageBoxResult.Yes)
            Species.Remove(species);
    }

    [RelayCommand]
    private void RemoveMove(MoveViewModel move)
    {
        var usages = (
            from species in Species
            from form in species.Forms
            from moveReq in form.Moves
            where moveReq.Move == move
            select (form, moveReq)
            ).ToList();

        var force = (System.Windows.Input.Keyboard.Modifiers & System.Windows.Input.ModifierKeys.Shift) != 0;
        var result = force ? System.Windows.MessageBoxResult.Yes : System.Windows.MessageBox.Show(
            $"Are you sure you would like to remove {move.Name}?\nThis move is used by various species {usages.Count} time(s), and will be removed from them as well.", "Remove Move",
            System.Windows.MessageBoxButton.YesNo, System.Windows.MessageBoxImage.Warning, System.Windows.MessageBoxResult.No);
        if (result == System.Windows.MessageBoxResult.Yes)
        {
            foreach (var usage in usages)
                usage.form.Moves.Remove(usage.moveReq);
            Moves.Remove(move);
        }
    }

    [RelayCommand]
    private void RemoveAbility(AbilityViewModel ability)
    {
        var usages = (
            from species in Species
            from form in species.Forms
            from abilityReq in form.Abilities
            where abilityReq.Ability == ability
            select (form, abilityReq)
            ).ToList();

        var force = (System.Windows.Input.Keyboard.Modifiers & System.Windows.Input.ModifierKeys.Shift) != 0;
        var result = force ? System.Windows.MessageBoxResult.Yes : System.Windows.MessageBox.Show(
            $"Are you sure you would like to remove {ability.Name}?\nThis ability is used by various species {usages.Count} time(s), and will be removed from them as well.", "Remove Ability",
            System.Windows.MessageBoxButton.YesNo, System.Windows.MessageBoxImage.Warning, System.Windows.MessageBoxResult.No);
        if (result == System.Windows.MessageBoxResult.Yes)
        {
            foreach (var usage in usages)
                usage.form.Abilities.Remove(usage.abilityReq);
            Abilities.Remove(ability);
        }
    }

    [RelayCommand]
    private void RemoveContestEffect(ContestEffectViewModel contestEffect)
    {
        var usages = (
            from move in Moves
            where move.HasContestEffect && move.MoveContestEffect == contestEffect
            select move
            ).ToList();

        var force = (System.Windows.Input.Keyboard.Modifiers & System.Windows.Input.ModifierKeys.Shift) != 0;
        var result = force ? System.Windows.MessageBoxResult.Yes : System.Windows.MessageBox.Show(
            $"Are you sure you would like to remove {contestEffect.Name}?\nThis contest effect is used by various moves {usages.Count} time(s), and will be removed from them as well.", "Remove Contest Effect",
            System.Windows.MessageBoxButton.YesNo, System.Windows.MessageBoxImage.Warning, System.Windows.MessageBoxResult.No);
        if (result == System.Windows.MessageBoxResult.Yes)
        {
            foreach (var move in usages)
                move.HasContestEffect = false;
            ContestEffects.Remove(contestEffect);
        }
    }

    [ObservableProperty]
    private ObservableCollection<SpeciesViewModel> _Species;

    [ObservableProperty]
    private SpeciesViewModel? _SelectedSpecies = null;


    [ObservableProperty]
    private ObservableCollection<MoveViewModel> _Moves;

    [ObservableProperty]
    private MoveViewModel? _SelectedMove = null;


    [ObservableProperty]
    private ObservableCollection<AbilityViewModel> _Abilities;

    [ObservableProperty]
    private AbilityViewModel? _SelectedAbility = null;


    [ObservableProperty]
    private ObservableCollection<ContestEffectViewModel> _ContestEffects;

    [ObservableProperty]
    private ContestEffectViewModel? _SelectedContestEffect = null;

#if DEBUG
    public static DatabaseViewModel DesignData { get; } = new DatabaseViewModel(Database.Load(GetDesignDataPath()));
    private static string GetDesignDataPath([System.Runtime.CompilerServices.CallerFilePath] string path = "")
        => System.IO.Path.GetFullPath(System.IO.Path.Combine(path, @"../../../Data/ptu.1.05.yaml"));
#endif
}
