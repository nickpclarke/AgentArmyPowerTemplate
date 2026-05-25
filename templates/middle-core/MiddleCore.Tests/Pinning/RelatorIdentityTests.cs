using Xunit;
using MiddleCore.Runtime.Pinning;

namespace MiddleCore.Tests.Pinning;

/// <summary>
/// PIN-F1 acceptance: relator identity = deterministic hash of bound participant
/// identities, order-independent after role/ordinal sort.
///
/// These tests verify the full chain:
///   participant identity hashes → OntologyIri.ForRelator → stable IRI
///   regardless of the order participants are enumerated.
/// </summary>
public sealed class RelatorIdentityTests
{
    // The four roles that the `ingest-evidence` relator binds
    // (see Reification-and-Hyperedges.md / PIN-F1 spec).
    private const string SourceHash = "hash-source-platform-vision";
    private const string Chunk1Hash = "hash-chunk-001";
    private const string Chunk2Hash = "hash-chunk-002";
    private const string ExerciseHash = "hash-exercise-001";
    private const string EvidenceHash = "hash-evidence-001";

    private static IEnumerable<(string RoleName, int Ordinal, string IdentityHash)> IngestEvidenceParticipants() =>
    [
        ("source",   0, SourceHash),
        ("chunks",   1, Chunk1Hash),
        ("chunks",   2, Chunk2Hash),
        ("exercise", 3, ExerciseHash),
        ("evidence", 4, EvidenceHash),
    ];

    // -----------------------------------------------------------------------
    // Order-independence — same participants, 3 different orderings
    // -----------------------------------------------------------------------

    [Fact]
    public void RelatorIri_OrderIndependent_OrderA_Equals_OrderB()
    {
        var orderA = IngestEvidenceParticipants().ToArray();

        var orderB = new (string RoleName, int Ordinal, string IdentityHash)[]
        {
            ("evidence", 4, EvidenceHash),
            ("chunks",   1, Chunk1Hash),
            ("source",   0, SourceHash),
            ("exercise", 3, ExerciseHash),
            ("chunks",   2, Chunk2Hash),
        };

        string iriA = OntologyIri.ForRelator("ingest-evidence", orderA);
        string iriB = OntologyIri.ForRelator("ingest-evidence", orderB);

        Assert.Equal(iriA, iriB);
    }

    [Fact]
    public void RelatorIri_OrderIndependent_OrderC_Equals_OrderA()
    {
        var orderA = IngestEvidenceParticipants().ToArray();

        // Randomize more thoroughly.
        var orderC = new (string RoleName, int Ordinal, string IdentityHash)[]
        {
            ("chunks",   2, Chunk2Hash),
            ("exercise", 3, ExerciseHash),
            ("chunks",   1, Chunk1Hash),
            ("evidence", 4, EvidenceHash),
            ("source",   0, SourceHash),
        };

        string iriA = OntologyIri.ForRelator("ingest-evidence", orderA);
        string iriC = OntologyIri.ForRelator("ingest-evidence", orderC);

        Assert.Equal(iriA, iriC);
    }

    // -----------------------------------------------------------------------
    // Stability — same call, same result
    // -----------------------------------------------------------------------

    [Fact]
    public void RelatorIri_CalledTwice_SameResult()
    {
        var participants = IngestEvidenceParticipants().ToArray();

        string iri1 = OntologyIri.ForRelator("ingest-evidence", participants);
        string iri2 = OntologyIri.ForRelator("ingest-evidence", participants);

        Assert.Equal(iri1, iri2);
    }

    // -----------------------------------------------------------------------
    // Different relator types produce different IRIs
    // -----------------------------------------------------------------------

    [Fact]
    public void RelatorIri_DifferentRelatorType_ProducesDifferentIri()
    {
        var participants = IngestEvidenceParticipants().ToArray();

        string iriA = OntologyIri.ForRelator("ingest-evidence", participants);
        string iriB = OntologyIri.ForRelator("other-relator", participants);

        Assert.NotEqual(iriA, iriB);
    }

    // -----------------------------------------------------------------------
    // One participant changed → different IRI
    // -----------------------------------------------------------------------

    [Fact]
    public void RelatorIri_OneParticipantChanged_ProducesDifferentIri()
    {
        var original = IngestEvidenceParticipants().ToArray();

        // Swap in a different identity hash for the source participant.
        var mutated = new (string RoleName, int Ordinal, string IdentityHash)[]
        {
            ("source",   0, "hash-DIFFERENT-source"),
            ("chunks",   1, Chunk1Hash),
            ("chunks",   2, Chunk2Hash),
            ("exercise", 3, ExerciseHash),
            ("evidence", 4, EvidenceHash),
        };

        string iriOriginal = OntologyIri.ForRelator("ingest-evidence", original);
        string iriMutated = OntologyIri.ForRelator("ingest-evidence", mutated);

        Assert.NotEqual(iriOriginal, iriMutated);
    }

    // -----------------------------------------------------------------------
    // IRI format
    // -----------------------------------------------------------------------

    [Fact]
    public void RelatorIri_HasCorrectSegmentCount()
    {
        // urn:agentarmy:mc:relator:ingest-evidence/<64-char-hash>
        var participants = IngestEvidenceParticipants().ToArray();
        string iri = OntologyIri.ForRelator("ingest-evidence", participants);

        // Split on the last '/' to get the relator segment and hash.
        int lastSlash = iri.LastIndexOf('/');
        string hashPart = iri[(lastSlash + 1)..];

        Assert.Equal(64, hashPart.Length);
        Assert.Matches("^[0-9a-f]+$", hashPart);
        Assert.StartsWith("urn:agentarmy:mc:relator:", iri, StringComparison.Ordinal);
    }

    // -----------------------------------------------------------------------
    // PinHash.Identity from relator IRI is stable across participant reordering
    // -----------------------------------------------------------------------

    [Fact]
    public void RelatorIdentityHash_StableAcrossParticipantReordering()
    {
        var orderA = IngestEvidenceParticipants().ToArray();
        var orderB = new (string RoleName, int Ordinal, string IdentityHash)[]
        {
            ("evidence", 4, EvidenceHash),
            ("source",   0, SourceHash),
            ("chunks",   2, Chunk2Hash),
            ("chunks",   1, Chunk1Hash),
            ("exercise", 3, ExerciseHash),
        };

        // Use the IRI as the identity JSON input (the IRI is the stable key for relators).
        string iriA = OntologyIri.ForRelator("ingest-evidence", orderA);
        string iriB = OntologyIri.ForRelator("ingest-evidence", orderB);

        // The IRIs are equal (proven above), therefore the identity hashes must be equal.
        string identityHashA = PinHash.ComputeIdentityHash(iriA);
        string identityHashB = PinHash.ComputeIdentityHash(iriB);

        Assert.Equal(identityHashA, identityHashB);
    }
}
