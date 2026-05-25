using Xunit;
using MiddleCore.Runtime.Pinning;

namespace MiddleCore.Tests.Pinning;

public sealed class OntologyIriTests
{
    // -----------------------------------------------------------------------
    // ForEndurant
    // -----------------------------------------------------------------------

    [Fact]
    public void ForEndurant_ProducesCorrectScheme()
    {
        string iri = OntologyIri.ForEndurant("SemanticAsset", "knowledge-source", "ks-001");

        Assert.Equal("urn:agentarmy:mc:SemanticAsset/knowledge-source/ks-001", iri);
    }

    [Fact]
    public void ForEndurant_NullConcept_ThrowsArgumentException()
    {
        Assert.ThrowsAny<ArgumentException>(() =>
            OntologyIri.ForEndurant(null!, "knowledge-source", "ks-001"));
    }

    [Fact]
    public void ForEndurant_WhitespaceConcept_ThrowsArgumentException()
    {
        Assert.Throws<ArgumentException>(() =>
            OntologyIri.ForEndurant("   ", "knowledge-source", "ks-001"));
    }

    [Fact]
    public void ForEndurant_EmptyObjectType_ThrowsArgumentException()
    {
        Assert.Throws<ArgumentException>(() =>
            OntologyIri.ForEndurant("SemanticAsset", "", "ks-001"));
    }

    [Fact]
    public void ForEndurant_EmptyId_ThrowsArgumentException()
    {
        Assert.Throws<ArgumentException>(() =>
            OntologyIri.ForEndurant("SemanticAsset", "knowledge-source", ""));
    }

    // -----------------------------------------------------------------------
    // ForPerdurant
    // -----------------------------------------------------------------------

    [Fact]
    public void ForPerdurant_ProducesCorrectScheme()
    {
        string iri = OntologyIri.ForPerdurant("knowledge-source", "ks-001", "ingest-started");

        Assert.Equal("urn:agentarmy:mc:event:knowledge-source/ks-001/ingest-started", iri);
    }

    [Fact]
    public void ForPerdurant_ContainsEventSegment()
    {
        string iri = OntologyIri.ForPerdurant("sm-x", "obj-1", "trigger-a");

        Assert.StartsWith("urn:agentarmy:mc:event:", iri, StringComparison.Ordinal);
    }

    [Fact]
    public void ForPerdurant_NullStateMachine_ThrowsArgumentException()
    {
        Assert.ThrowsAny<ArgumentException>(() =>
            OntologyIri.ForPerdurant(null!, "obj-1", "trigger-a"));
    }

    // -----------------------------------------------------------------------
    // ForRelator — determinism and order-independence
    // -----------------------------------------------------------------------

    [Fact]
    public void ForRelator_ProducesCorrectSchemePrefix()
    {
        var participants = new (string, int, string)[]
        {
            ("source", 0, "aabbcc"),
            ("evidence", 1, "ddeeff"),
        };

        string iri = OntologyIri.ForRelator("ingest-evidence", participants);

        Assert.StartsWith("urn:agentarmy:mc:relator:ingest-evidence/", iri, StringComparison.Ordinal);
    }

    [Fact]
    public void ForRelator_OrderIndependent_SameParticipants_DifferentOrder_ProducesSameIri()
    {
        // Same participants, two different orderings.
        var orderA = new (string, int, string)[]
        {
            ("source", 0, "hash-source"),
            ("chunks", 1, "hash-chunks"),
            ("exercise", 2, "hash-exercise"),
            ("evidence", 3, "hash-evidence"),
        };

        var orderB = new (string, int, string)[]
        {
            ("evidence", 3, "hash-evidence"),
            ("source", 0, "hash-source"),
            ("exercise", 2, "hash-exercise"),
            ("chunks", 1, "hash-chunks"),
        };

        string iriA = OntologyIri.ForRelator("ingest-evidence", orderA);
        string iriB = OntologyIri.ForRelator("ingest-evidence", orderB);

        Assert.Equal(iriA, iriB);
    }

    [Fact]
    public void ForRelator_DifferentParticipants_ProduceDifferentIris()
    {
        var participantsA = new (string, int, string)[]
        {
            ("source", 0, "hash-alpha"),
        };
        var participantsB = new (string, int, string)[]
        {
            ("source", 0, "hash-beta"),
        };

        string iriA = OntologyIri.ForRelator("ingest-evidence", participantsA);
        string iriB = OntologyIri.ForRelator("ingest-evidence", participantsB);

        Assert.NotEqual(iriA, iriB);
    }

    [Fact]
    public void ForRelator_NullRelatorType_ThrowsArgumentException()
    {
        Assert.ThrowsAny<ArgumentException>(() =>
            OntologyIri.ForRelator(null!, []));
    }

    // -----------------------------------------------------------------------
    // ComputeParticipantHash — internal helper tested directly
    // -----------------------------------------------------------------------

    [Fact]
    public void ComputeParticipantHash_EmptyInput_ReturnsConsistentHash()
    {
        string hash1 = OntologyIri.ComputeParticipantHash([]);
        string hash2 = OntologyIri.ComputeParticipantHash([]);

        Assert.Equal(hash1, hash2);
    }

    [Fact]
    public void ComputeParticipantHash_OutputIsLowercaseHex64Chars()
    {
        var participants = new (string, int, string)[]
        {
            ("role", 0, "abc123"),
        };

        string hash = OntologyIri.ComputeParticipantHash(participants);

        Assert.Equal(64, hash.Length);
        Assert.Matches("^[0-9a-f]+$", hash);
    }
}
