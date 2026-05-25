using System.Text.Json;
using Xunit;
using MiddleCore.Runtime.Pinning;

namespace MiddleCore.Tests.Pinning;

public sealed class CanonicalJsonTests
{
    // -----------------------------------------------------------------------
    // Key-order independence — same data, different property order in source
    // -----------------------------------------------------------------------

    [Fact]
    public void Serialize_DictionaryWithDifferentInsertionOrder_ProducesSameJson()
    {
        // Alpha-first insertion order.
        var alpha = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["alpha"] = "a",
            ["beta"] = "b",
            ["gamma"] = "c",
        };

        // Reverse insertion order.
        var reversed = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["gamma"] = "c",
            ["beta"] = "b",
            ["alpha"] = "a",
        };

        string alphaJson = CanonicalJson.Serialize(alpha);
        string reversedJson = CanonicalJson.Serialize(reversed);

        Assert.Equal(alphaJson, reversedJson);
    }

    [Fact]
    public void Serialize_DictionaryWithDifferentInsertionOrder_SortedKeyFirst()
    {
        var payload = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["z_last"] = 1,
            ["a_first"] = 2,
            ["m_mid"] = 3,
        };

        string json = CanonicalJson.Serialize(payload);

        // Keys must appear in lexicographic order.
        int aPos = json.IndexOf("a_first", StringComparison.Ordinal);
        int mPos = json.IndexOf("m_mid", StringComparison.Ordinal);
        int zPos = json.IndexOf("z_last", StringComparison.Ordinal);

        Assert.True(aPos < mPos, "a_first must appear before m_mid");
        Assert.True(mPos < zPos, "m_mid must appear before z_last");
    }

    // -----------------------------------------------------------------------
    // Nested object — keys sorted at every level
    // -----------------------------------------------------------------------

    [Fact]
    public void Serialize_NestedObject_AllLevelsSorted()
    {
        var payload = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["z_outer"] = "z",
            ["a_outer"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["z_inner"] = 9,
                ["a_inner"] = 1,
            },
        };

        string json = CanonicalJson.Serialize(payload);

        // Outer level: a_outer before z_outer.
        int aOuter = json.IndexOf("a_outer", StringComparison.Ordinal);
        int zOuter = json.IndexOf("z_outer", StringComparison.Ordinal);
        Assert.True(aOuter < zOuter, "a_outer must appear before z_outer");

        // Inner level: a_inner before z_inner.
        int aInner = json.IndexOf("a_inner", StringComparison.Ordinal);
        int zInner = json.IndexOf("z_inner", StringComparison.Ordinal);
        Assert.True(aInner < zInner, "a_inner must appear before z_inner");
    }

    // -----------------------------------------------------------------------
    // Idempotency — serializing the same input twice yields identical output
    // -----------------------------------------------------------------------

    [Fact]
    public void Serialize_SameInputTwice_ProducesIdenticalOutput()
    {
        var payload = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["object_type"] = "knowledge-source",
            ["id"] = "ks-001",
            ["state"] = "landed",
        };

        string first = CanonicalJson.Serialize(payload);
        string second = CanonicalJson.Serialize(payload);

        Assert.Equal(first, second);
    }

    // -----------------------------------------------------------------------
    // No whitespace — output is compact
    // -----------------------------------------------------------------------

    [Fact]
    public void Serialize_Output_ContainsNoWhitespace()
    {
        var payload = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["key"] = "value",
            ["num"] = 42,
        };

        string json = CanonicalJson.Serialize(payload);

        Assert.DoesNotContain(" ", json, StringComparison.Ordinal);
        Assert.DoesNotContain("\n", json, StringComparison.Ordinal);
        Assert.DoesNotContain("\r", json, StringComparison.Ordinal);
        Assert.DoesNotContain("\t", json, StringComparison.Ordinal);
    }

    // -----------------------------------------------------------------------
    // Typed record serialization uses snake_case property naming
    // -----------------------------------------------------------------------

    private sealed record SampleRecord(string ObjectType, int ClaimCount, bool IsActive);

    [Fact]
    public void Serialize_TypedRecord_UsesSnakeCaseKeys()
    {
        var record = new SampleRecord("evidence-pack", 3, true);
        string json = CanonicalJson.Serialize(record);

        Assert.Contains("object_type", json, StringComparison.Ordinal);
        Assert.Contains("claim_count", json, StringComparison.Ordinal);
        Assert.Contains("is_active", json, StringComparison.Ordinal);
    }

    [Fact]
    public void Serialize_TypedRecord_KeysAreSorted()
    {
        // Record properties: ObjectType (→ object_type), ClaimCount (→ claim_count), IsActive (→ is_active)
        // Sorted order: claim_count < is_active < object_type
        var record = new SampleRecord("evidence-pack", 3, true);
        string json = CanonicalJson.Serialize(record);

        int claimPos = json.IndexOf("claim_count", StringComparison.Ordinal);
        int activePos = json.IndexOf("is_active", StringComparison.Ordinal);
        int typePos = json.IndexOf("object_type", StringComparison.Ordinal);

        Assert.True(claimPos < activePos, "claim_count must precede is_active");
        Assert.True(activePos < typePos, "is_active must precede object_type");
    }

    // -----------------------------------------------------------------------
    // Array values are preserved in original order (arrays are not sorted)
    // -----------------------------------------------------------------------

    [Fact]
    public void Serialize_ArrayValues_PreservesArrayOrder()
    {
        var payload = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["items"] = new[] { "c", "a", "b" },
        };

        string json = CanonicalJson.Serialize(payload);

        // Verify the exact array order is preserved.
        using JsonDocument doc = JsonDocument.Parse(json);
        JsonElement items = doc.RootElement.GetProperty("items");
        JsonElement[] arr = [.. items.EnumerateArray()];

        Assert.Equal(3, arr.Length);
        Assert.Equal("c", arr[0].GetString());
        Assert.Equal("a", arr[1].GetString());
        Assert.Equal("b", arr[2].GetString());
    }

    // -----------------------------------------------------------------------
    // Null values are serialized as JSON null
    // -----------------------------------------------------------------------

    [Fact]
    public void Serialize_NullValue_EmitsJsonNull()
    {
        var payload = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["key"] = null,
        };

        string json = CanonicalJson.Serialize(payload);

        Assert.Contains("\"key\":null", json, StringComparison.Ordinal);
    }
}
