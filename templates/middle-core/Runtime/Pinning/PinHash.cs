using System.Security.Cryptography;
using System.Text;

namespace MiddleCore.Runtime.Pinning;

/// <summary>
/// A pair of SHA-256 hex hashes that characterise a pinned object.
/// </summary>
/// <param name="Identity">
/// Hash of the object's stable identity key — derived only from fields that
/// uniquely identify the object (type + id) and never change across mutations.
/// Stable across payload changes.
/// </param>
/// <param name="Content">
/// Hash of the object's full canonical payload including valid-time window.
/// Changes whenever the payload or valid-time changes.
/// </param>
public sealed record PinHash(string Identity, string Content)
{
    // -----------------------------------------------------------------------
    // Factory helpers
    // -----------------------------------------------------------------------

    /// <summary>
    /// Computes a SHA-256 identity hash from an object's stable identity fields.
    /// The <paramref name="identityJson"/> must already be a canonical (key-sorted)
    /// JSON string produced by <see cref="CanonicalJson"/>.
    /// </summary>
    public static string ComputeIdentityHash(string identityJson)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(identityJson);
        return HashString(identityJson);
    }

    /// <summary>
    /// Computes a SHA-256 content hash from an object's full canonical payload
    /// (including valid-time fields).
    /// </summary>
    public static string ComputeContentHash(string contentJson)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(contentJson);
        return HashString(contentJson);
    }

    /// <summary>
    /// Builds a <see cref="PinHash"/> from pre-computed canonical JSON strings.
    /// </summary>
    /// <param name="identityJson">Canonical JSON covering only stable identity fields.</param>
    /// <param name="contentJson">Canonical JSON covering the full payload + valid-time.</param>
    public static PinHash From(string identityJson, string contentJson) =>
        new(ComputeIdentityHash(identityJson), ComputeContentHash(contentJson));

    // -----------------------------------------------------------------------
    // Internal helpers
    // -----------------------------------------------------------------------

    private static string HashString(string input)
    {
        byte[] bytes = Encoding.UTF8.GetBytes(input);
        byte[] hash = SHA256.HashData(bytes);
        return Convert.ToHexStringLower(hash);
    }
}
