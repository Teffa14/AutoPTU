using System.IO.Compression;
using YamlDotNet.Serialization;

namespace PTUDatabase;

public record Database
{
    public IList<ContestEffect> ContestEffects { get; init; } = Array.Empty<ContestEffect>();
    public IList<Move> Moves { get; init; } = Array.Empty<Move>();
    public IList<Ability> Abilities { get; init; } = Array.Empty<Ability>();
    public IList<Species> Species { get; init; } = Array.Empty<Species>();

    public static Database Load(string path)
    {
        using var file = File.OpenRead(path);
        return Load(file);
    }
    public static Database Load(Stream stream)
    {
        var (b1, b2) = (stream.ReadByte(), stream.ReadByte()); // Check for GZip magic number
        stream.Position = 0;
        using var stream2 = (b1 == 0x1f && b2 == 0x8b) ? new GZipStream(stream, CompressionMode.Decompress) : stream;
        using var sr = new StreamReader(stream2);
        var deserializer = new DeserializerBuilder().Build();
        return deserializer.Deserialize<Database>(sr);
    }

    public void Save(string path, bool gzip = true)
    {
        using var file = File.Create(path);
        Save(file, gzip);
    }
    public void Save(Stream stream, bool gzip = true)
    {
        using var stream2 = gzip ? new GZipStream(stream, CompressionLevel.Optimal) : stream;
        using var sw = new StreamWriter(stream2);
        var serializer = new SerializerBuilder().Build();
        serializer.Serialize(sw, this);
    }
}
