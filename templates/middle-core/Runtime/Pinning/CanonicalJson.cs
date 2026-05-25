using System.Text;
using System.Text.Json;

namespace MiddleCore.Runtime.Pinning;

/// <summary>
/// Produces deterministic, key-sorted, snake_case JSON for content-addressing.
/// Key ordering is lexicographic (ordinal). Values are emitted with no trailing
/// whitespace so the result is byte-stable across runs and platforms.
/// </summary>
public static class CanonicalJson
{
    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        WriteIndented = false,
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
    };

    /// <summary>
    /// Serializes <paramref name="value"/> to deterministic, key-sorted snake_case JSON.
    /// </summary>
    public static string Serialize<T>(T value)
    {
        // First pass: serialize via System.Text.Json to a JsonDocument so we can
        // walk and re-sort all object keys recursively.
        string raw = JsonSerializer.Serialize(value, SerializerOptions);
        using JsonDocument document = JsonDocument.Parse(raw);
        return SerializeElement(document.RootElement);
    }

    /// <summary>
    /// Serializes a pre-built <see cref="IReadOnlyDictionary{TKey,TValue}"/> of
    /// string→object? pairs to deterministic, key-sorted snake_case JSON.
    /// </summary>
    public static string Serialize(IReadOnlyDictionary<string, object?> payload)
    {
        string raw = JsonSerializer.Serialize(payload, SerializerOptions);
        using JsonDocument document = JsonDocument.Parse(raw);
        return SerializeElement(document.RootElement);
    }

    // -----------------------------------------------------------------------
    // Internal helpers
    // -----------------------------------------------------------------------

    internal static string SerializeElement(JsonElement element)
    {
        StringBuilder sb = new();
        WriteElement(element, sb);
        return sb.ToString();
    }

    private static void WriteElement(JsonElement element, StringBuilder sb)
    {
        switch (element.ValueKind)
        {
            case JsonValueKind.Object:
                WriteObject(element, sb);
                break;

            case JsonValueKind.Array:
                WriteArray(element, sb);
                break;

            case JsonValueKind.String:
                // Re-serialize string so special chars and unicode are escaped consistently.
                sb.Append(JsonSerializer.Serialize(element.GetString()));
                break;

            case JsonValueKind.Number:
                sb.Append(element.GetRawText());
                break;

            case JsonValueKind.True:
                sb.Append("true");
                break;

            case JsonValueKind.False:
                sb.Append("false");
                break;

            case JsonValueKind.Null:
            case JsonValueKind.Undefined:
            default:
                sb.Append("null");
                break;
        }
    }

    private static void WriteObject(JsonElement element, StringBuilder sb)
    {
        // Sort all keys lexicographically (ordinal) for determinism.
        List<(string Key, JsonElement Value)> properties = [];
        foreach (JsonProperty prop in element.EnumerateObject())
        {
            properties.Add((prop.Name, prop.Value));
        }

        properties.Sort((a, b) => string.Compare(a.Key, b.Key, StringComparison.Ordinal));

        sb.Append('{');
        for (int i = 0; i < properties.Count; i++)
        {
            if (i > 0)
            {
                sb.Append(',');
            }

            sb.Append(JsonSerializer.Serialize(properties[i].Key));
            sb.Append(':');
            WriteElement(properties[i].Value, sb);
        }

        sb.Append('}');
    }

    private static void WriteArray(JsonElement element, StringBuilder sb)
    {
        sb.Append('[');
        bool first = true;
        foreach (JsonElement item in element.EnumerateArray())
        {
            if (!first)
            {
                sb.Append(',');
            }

            WriteElement(item, sb);
            first = false;
        }

        sb.Append(']');
    }
}
