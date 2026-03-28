using System.Windows;
using Microsoft.Win32;
using PTUDataEditor.ViewModels;

namespace PTUDataEditor;

/// <summary>
/// Interaction logic for MainWindow.xaml
/// </summary>
public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
    }

    public string? OpenPath { get; private set; }

    private void MenuOpen_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog()
        {
            Filter = "YAML File (*.yaml;*.yaml.gz)|*.yaml;*.yaml.gz|All Files (*.*)|*.*",
            InitialDirectory = System.IO.Path.GetFullPath("../../../../Data"),
        };
        if (dialog.ShowDialog(this) == true)
        {
            using var file = dialog.OpenFile();
            DatabaseView.DataContext = new DatabaseViewModel(PTUDatabase.Database.Load(file));
            OpenPath = dialog.FileName;
        }
    }

    private void MenuSave_Click(object sender, RoutedEventArgs e)
    {
        if (OpenPath is null)
        {
            MenuSaveAs_Click(sender, e);
            return;
        }

        var dbvm = DatabaseView.DataContext as DatabaseViewModel;
        if (dbvm is not null)
            dbvm.BuildModel().Save(OpenPath, gzip: OpenPath.EndsWith(".gz"));
    }

    private void MenuSaveAs_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new SaveFileDialog()
        {
            Filter = "YAML File (*.yaml;*.yaml.gz)|*.yaml;*.yaml.gz|Plain Text YAML File (*.yaml)|*.yaml|Compressed YAML File (*.yaml.gz)|*.yaml.gz|All Files (*.*)|*.*",
            FileName = OpenPath,
            InitialDirectory = System.IO.Path.GetFullPath("../../../../Data"),
            OverwritePrompt = true,
        };
        if (dialog.ShowDialog(this) == true)
        {
            using var file = dialog.OpenFile();
            var dbvm = DatabaseView.DataContext as DatabaseViewModel;
            if (dbvm is not null)
            {
                dbvm.BuildModel().Save(file, gzip: dialog.FileName!.EndsWith(".gz"));
                OpenPath = dialog.FileName;
            }
        }
    }
}
