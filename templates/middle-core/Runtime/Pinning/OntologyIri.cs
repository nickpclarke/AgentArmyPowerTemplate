using System.Security.Cryptography;
using System.Text;

namespace MiddleCore.Runtime.Pinning;

/// <summary>
/// Builds stable ontology IRIs under the <c>urn:agentarmy:mc:</c> scheme.
///
/// Schemes:
///   Endurant  — <c>urn:agentarmy:mc:{concept}/{objectType}/{id}</c>
///   Perdurant — <c>urn:agentarmy:mc:event:{stateMachine}/{objectId}/{trigger}</c>
///   Relator   — <c>urn:agentarmy:mc:relator:{relatorType}/{sha256(sorted participant identity hashes)}</c>
/// </summary>
public static class OntologyIri
{
    private const string Scheme = "urn:agentarmy:mc";

    // -----------------------------------------------------------------------
    // Endurant (business object)
    // -----------------------------------------------------------------------

    /// <summary>
    /// Builds an endurant IRI: <c>urn:agentarmy:mc:{concept}/{objectType}/{id}</c>.
    /// </summary>
    /// <param name="ontologyConcept">UFO/gUFO concept name, e.g. "SemanticAsset".</param>
    /// <param name="objectType">Middle-core object type, e.g. "knowledge-source".</param>
    /// <param name="id">Domain identifier of the object.</param>
    public static string ForEndurant(string ontologyConcept, string objectType, string id)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(ontologyConcept);
        ArgumentException.ThrowIfNullOrWhiteSpace(objectType);
        ArgumentException.ThrowIfNullOrWhiteSpace(id);

        return $"{Scheme}:{ontologyConcept}/{objectType}/{id}";
    }

    // -----------------------------------------------------------------------
    // Perdurant (state-machine event)
    // -----------------------------------------------------------------------

    /// <summary>
    /// Builds a perdurant IRI: <c>urn:agentarmy:mc:event:{stateMachine}/{objectId}/{trigger}</c>.
    /// </summary>
    /// <param name="stateMachine">State machine name / object type.</param>
    /// <param name="objectId">Identity of the object undergoing the transition.</param>
    /// <param name="trigger">Transition trigger name.</param>
    public static string ForPerdurant(string stateMachine, string objectId, string trigger)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(stateMachine);
        ArgumentException.ThrowIfNullOrWhiteSpace(objectId);
        ArgumentException.ThrowIfNullOrWhiteSpace(trigger);

        return $"{Scheme}:event:{stateMachine}/{objectId}/{trigger}";
    }

    // -----------------------------------------------------------------------
    // Relator (n-ary reified relationship)
    // -----------------------------------------------------------------------

    /// <summary>
    /// Builds a relator IRI: <c>urn:agentarmy:mc:relator:{relatorType}/{participantHash}</c>.
    ///
    /// The participant hash is a SHA-256 over the sorted (role/ordinal, identityHash) pairs,
    /// making it order-independent with respect to participant list order.
    /// </summary>
    /// <param name="relatorType">Relator type name, e.g. "ingest-evidence".</param>
    /// <param name="participantIdentityHashes">
    /// Sequence of (roleName, ordinal, identityHash) tuples describing the bound participants.
    /// Ordering of this sequence does not affect the resulting IRI.
    /// </param>
    public static string ForRelator(
        string relatorType,
        IEnumerable<(string RoleName, int Ordinal, string IdentityHash)> participantIdentityHashes)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(relatorType);

        string participantHash = ComputeParticipantHash(participantIdentityHashes);
        return $"{Scheme}:relator:{relatorType}/{participantHash}";
    }

    // -----------------------------------------------------------------------
    // Internal helpers
    // -----------------------------------------------------------------------

    /// <summary>
    /// Computes a SHA-256 hex digest over the sorted participant (role, ordinal, hash) tuples.
    /// Sorting is by (roleName ordinal, ordinal integer, identityHash) so the output is
    /// invariant to the order in which participants are passed in.
    /// </summary>
    public static string ComputeParticipantHash(
        IEnumerable<(string RoleName, int Ordinal, string IdentityHash)> participants)
    {
        // Sort for determinism: primary key = role name, secondary = ordinal, tertiary = hash.
        List<(string RoleName, int Ordinal, string IdentityHash)> sorted =
            [.. participants.OrderBy(p => p.RoleName, StringComparer.Ordinal)
                            .ThenBy(p => p.Ordinal)
                            .ThenBy(p => p.IdentityHash, StringComparer.Ordinal)];

        // Build a canonical string and hash it.
        StringBuilder sb = new();
        foreach ((string roleName, int ordinal, string identityHash) in sorted)
        {
            sb.Append(roleName);
            sb.Append(':');
            sb.Append(ordinal);
            sb.Append(':');
            sb.Append(identityHash);
            sb.Append('|');
        }

        byte[] inputBytes = Encoding.UTF8.GetBytes(sb.ToString());
        byte[] hashBytes = SHA256.HashData(inputBytes);
        return Convert.ToHexStringLower(hashBytes);
    }
}
