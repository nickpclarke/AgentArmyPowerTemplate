using Xunit;
using MiddleCore.Runtime.Pinning;

namespace MiddleCore.Tests.Pinning;

public sealed class PinHashTests
{
    // -----------------------------------------------------------------------
    // Identity hash — stable across payload change
    // -----------------------------------------------------------------------

    [Fact]
    public void IdentityHash_StableAcrossPayloadChange()
    {
        // Identity JSON covers only stable identity fields.
        string identityJson = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["object_type"] = "knowledge-source",
            ["id"] = "ks-001",
        });

        // Two different payloads with the same identity.
        string content1Json = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["object_type"] = "knowledge-source",
            ["id"] = "ks-001",
            ["state"] = "landed",
            ["valid_from"] = "2026-01-01T00:00:00Z",
        });

        string content2Json = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["object_type"] = "knowledge-source",
            ["id"] = "ks-001",
            ["state"] = "ingesting",           // state changed
            ["valid_from"] = "2026-01-01T00:00:00Z",
        });

        PinHash hash1 = PinHash.From(identityJson, content1Json);
        PinHash hash2 = PinHash.From(identityJson, content2Json);

        // Identity hash must not change when payload changes.
        Assert.Equal(hash1.Identity, hash2.Identity);
    }

    // -----------------------------------------------------------------------
    // Content hash — changes with payload
    // -----------------------------------------------------------------------

    [Fact]
    public void ContentHash_ChangesWhenPayloadChanges()
    {
        string identityJson = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
        });

        string content1Json = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
            ["state"] = "landed",
        });

        string content2Json = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
            ["state"] = "ingesting",
        });

        PinHash hash1 = PinHash.From(identityJson, content1Json);
        PinHash hash2 = PinHash.From(identityJson, content2Json);

        Assert.NotEqual(hash1.Content, hash2.Content);
    }

    // -----------------------------------------------------------------------
    // Content hash — changes with valid-time
    // -----------------------------------------------------------------------

    [Fact]
    public void ContentHash_ChangesWhenValidTimeChanges()
    {
        string identityJson = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
        });

        string content1Json = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
            ["state"] = "landed",
            ["valid_from"] = "2026-01-01T00:00:00Z",
            ["valid_to"] = null,
        });

        string content2Json = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
            ["state"] = "landed",
            ["valid_from"] = "2026-06-01T00:00:00Z",  // valid_from changed
            ["valid_to"] = null,
        });

        PinHash hash1 = PinHash.From(identityJson, content1Json);
        PinHash hash2 = PinHash.From(identityJson, content2Json);

        Assert.NotEqual(hash1.Content, hash2.Content);
    }

    // -----------------------------------------------------------------------
    // Identity hash — key-order independent (canonical JSON guarantees this)
    // -----------------------------------------------------------------------

    [Fact]
    public void IdentityHash_KeyOrderIndependent()
    {
        // Alpha order.
        string jsonA = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
            ["object_type"] = "knowledge-source",
        });

        // Reverse order.
        string jsonB = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["object_type"] = "knowledge-source",
            ["id"] = "ks-001",
        });

        string hashA = PinHash.ComputeIdentityHash(jsonA);
        string hashB = PinHash.ComputeIdentityHash(jsonB);

        Assert.Equal(hashA, hashB);
    }

    // -----------------------------------------------------------------------
    // Hash format — 64-char lowercase hex
    // -----------------------------------------------------------------------

    [Fact]
    public void ComputeIdentityHash_OutputIsLowercaseHex64Chars()
    {
        string json = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
        });

        string hash = PinHash.ComputeIdentityHash(json);

        Assert.Equal(64, hash.Length);
        Assert.Matches("^[0-9a-f]+$", hash);
    }

    [Fact]
    public void ComputeContentHash_OutputIsLowercaseHex64Chars()
    {
        string json = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
            ["state"] = "landed",
        });

        string hash = PinHash.ComputeContentHash(json);

        Assert.Equal(64, hash.Length);
        Assert.Matches("^[0-9a-f]+$", hash);
    }

    // -----------------------------------------------------------------------
    // PinHash.From — record equality / value semantics
    // -----------------------------------------------------------------------

    [Fact]
    public void PinHash_SameInputs_EqualRecords()
    {
        string idJson = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
        });
        string contentJson = CanonicalJson.Serialize(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = "ks-001",
            ["state"] = "landed",
        });

        PinHash a = PinHash.From(idJson, contentJson);
        PinHash b = PinHash.From(idJson, contentJson);

        Assert.Equal(a, b);
    }

    // -----------------------------------------------------------------------
    // Error cases
    // -----------------------------------------------------------------------

    [Fact]
    public void ComputeIdentityHash_EmptyString_ThrowsArgumentException()
    {
        Assert.Throws<ArgumentException>(() => PinHash.ComputeIdentityHash(""));
    }

    [Fact]
    public void ComputeContentHash_WhitespaceOnly_ThrowsArgumentException()
    {
        Assert.Throws<ArgumentException>(() => PinHash.ComputeContentHash("   "));
    }
}
