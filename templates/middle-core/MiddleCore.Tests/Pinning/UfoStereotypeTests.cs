using Xunit;
using MiddleCore.Generated;
using MiddleCore.Runtime.Pinning;

namespace MiddleCore.Tests.Pinning;

public sealed class UfoStereotypeTests
{
    // -----------------------------------------------------------------------
    // ConceptToUfo.Resolve — gUFO Kinds from top-level-ufo-lite.ttl
    // -----------------------------------------------------------------------

    [Theory]
    [InlineData("SemanticAsset", UfoStereotype.Kind)]
    [InlineData("EvidenceBundle", UfoStereotype.Kind)]
    [InlineData("CapabilityObservation", UfoStereotype.Kind)]
    [InlineData("GovernedDecision", UfoStereotype.Kind)]
    [InlineData("BusinessObjectKind", UfoStereotype.Kind)]
    public void Resolve_GufoKinds_ReturnKind(string concept, UfoStereotype expected)
    {
        Assert.Equal(expected, ConceptToUfo.Resolve(concept));
    }

    // -----------------------------------------------------------------------
    // SubKind
    // -----------------------------------------------------------------------

    [Fact]
    public void Resolve_LifecycleState_ReturnSubKind()
    {
        Assert.Equal(UfoStereotype.SubKind, ConceptToUfo.Resolve("LifecycleState"));
    }

    // -----------------------------------------------------------------------
    // EventType (perdurant)
    // -----------------------------------------------------------------------

    [Theory]
    [InlineData("StateTransition")]
    [InlineData("ScenarioExecution")]
    public void Resolve_EventTypes_ReturnEventType(string concept)
    {
        Assert.Equal(UfoStereotype.EventType, ConceptToUfo.Resolve(concept));
    }

    // -----------------------------------------------------------------------
    // Relator
    // -----------------------------------------------------------------------

    [Fact]
    public void Resolve_IngestEvidence_ReturnRelator()
    {
        Assert.Equal(UfoStereotype.Relator, ConceptToUfo.Resolve("ingest-evidence"));
    }

    // -----------------------------------------------------------------------
    // middle-core.ttl concepts (rdfs:Class treated as Kind)
    // -----------------------------------------------------------------------

    [Theory]
    [InlineData("ActorIntent")]
    [InlineData("ScenarioContract")]
    [InlineData("ToolCandidate")]
    public void Resolve_MiddleCoreTtlConcepts_ReturnKind(string concept)
    {
        Assert.Equal(UfoStereotype.Kind, ConceptToUfo.Resolve(concept));
    }

    // -----------------------------------------------------------------------
    // Unknown concept → Unknown
    // -----------------------------------------------------------------------

    [Fact]
    public void Resolve_UnknownConcept_ReturnUnknown()
    {
        Assert.Equal(UfoStereotype.Unknown, ConceptToUfo.Resolve("DoesNotExist"));
    }

    [Fact]
    public void Resolve_EmptyString_ReturnUnknown()
    {
        Assert.Equal(UfoStereotype.Unknown, ConceptToUfo.Resolve(""));
    }

    [Fact]
    public void Resolve_NullString_ReturnUnknown()
    {
        Assert.Equal(UfoStereotype.Unknown, ConceptToUfo.Resolve(null!));
    }

    // -----------------------------------------------------------------------
    // IsPerdurant helper
    // -----------------------------------------------------------------------

    [Theory]
    [InlineData("StateTransition", true)]
    [InlineData("ScenarioExecution", true)]
    [InlineData("SemanticAsset", false)]
    [InlineData("ingest-evidence", false)]
    public void IsPerdurant_MatchesEventType(string concept, bool expected)
    {
        Assert.Equal(expected, ConceptToUfo.IsPerdurant(concept));
    }

    // -----------------------------------------------------------------------
    // IsRelator helper
    // -----------------------------------------------------------------------

    [Theory]
    [InlineData("ingest-evidence", true)]
    [InlineData("SemanticAsset", false)]
    [InlineData("StateTransition", false)]
    public void IsRelator_MatchesRelatorStereotype(string concept, bool expected)
    {
        Assert.Equal(expected, ConceptToUfo.IsRelator(concept));
    }

    // -----------------------------------------------------------------------
    // Alignment check: every generated BusinessObject's OntologyConcept is mapped
    // -----------------------------------------------------------------------

    [Fact]
    public void AllGeneratedBusinessObjectConcepts_AreMapped()
    {
        foreach (BusinessObjectContract bo in GeneratedModel.BusinessObjects)
        {
            UfoStereotype stereotype = ConceptToUfo.Resolve(bo.OntologyConcept);
            Assert.True(
                stereotype != UfoStereotype.Unknown,
                $"BusinessObject '{bo.Id}' has unmapped concept '{bo.OntologyConcept}'");
        }
    }
}
