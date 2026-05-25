using Xunit;
using MiddleCore.Runtime;
using MiddleCore.Generated;

namespace MiddleCore.Tests;

// ---------------------------------------------------------------------------
// Tests for the GeneratedModel static enforcement API and the StateNames
// ToModelString() extension methods.
//
// All anchors (state names, transitions) are taken directly from the
// generated StateMachineContracts.g.cs — no strings are invented.
// ---------------------------------------------------------------------------
public sealed class EnforcementApiTests
{
    // =======================================================================
    // IsValidState
    // =======================================================================

    [Theory]
    [InlineData("landed")]
    [InlineData("ingesting")]
    [InlineData("indexed")]
    [InlineData("searchable")]
    [InlineData("archived")]
    [InlineData("failed")]
    public void IsValidState_KnowledgeSource_RecognisesAllStates(string state)
    {
        Assert.True(GeneratedModel.IsValidState(BusinessObjectTypes.KnowledgeSource, state));
    }

    [Fact]
    public void IsValidState_KnowledgeSource_RejectsUnknownState()
    {
        Assert.False(GeneratedModel.IsValidState(BusinessObjectTypes.KnowledgeSource, "not-a-state"));
    }

    [Fact]
    public void IsValidState_UnknownObjectType_ReturnsFalse()
    {
        Assert.False(GeneratedModel.IsValidState("not-an-object-type", "landed"));
    }

    // -----------------------------------------------------------------------
    // Spot-checks for other object types using their real model strings
    // -----------------------------------------------------------------------
    [Theory]
    [InlineData(BusinessObjectTypes.WorkPacket, "todo")]
    [InlineData(BusinessObjectTypes.WorkPacket, "in-progress")]
    [InlineData(BusinessObjectTypes.WorkPacket, "awaiting-decision")]
    [InlineData(BusinessObjectTypes.ToolOffering, "schema-ready")]
    [InlineData(BusinessObjectTypes.ToolOffering, "candidate")]
    [InlineData(BusinessObjectTypes.DecisionRecord, "proposed")]
    [InlineData(BusinessObjectTypes.DecisionRecord, "superseded")]
    public void IsValidState_VariousObjectTypes_RecognisesRealStates(string objectType, string state)
    {
        Assert.True(GeneratedModel.IsValidState(objectType, state));
    }

    // =======================================================================
    // CanTransition
    // =======================================================================

    [Fact]
    public void CanTransition_KnowledgeSource_LandedToIngesting_IsTrue()
    {
        // Confirmed in StateMachineContracts.g.cs:
        //   new StateTransitionContract("landed", "ingesting", "ingest-started")
        Assert.True(GeneratedModel.CanTransition(BusinessObjectTypes.KnowledgeSource, "landed", "ingesting"));
    }

    [Fact]
    public void CanTransition_KnowledgeSource_LandedToSearchable_IsFalse()
    {
        // "landed" → "searchable" is NOT a defined transition (must go via ingesting → indexed → searchable).
        Assert.False(GeneratedModel.CanTransition(BusinessObjectTypes.KnowledgeSource, "landed", "searchable"));
    }

    [Theory]
    [InlineData("ingesting", "indexed")]     // chunks-indexed trigger
    [InlineData("indexed", "searchable")]    // evidence-complete trigger
    [InlineData("searchable", "archived")]   // source-retired trigger
    public void CanTransition_KnowledgeSource_ValidTransitions_AreTrue(string from, string to)
    {
        Assert.True(GeneratedModel.CanTransition(BusinessObjectTypes.KnowledgeSource, from, to));
    }

    [Fact]
    public void CanTransition_WorkPacket_BlockedToAwaitingDecision_IsTrue()
    {
        // new StateTransitionContract("blocked", "awaiting-decision", "decision-required")
        Assert.True(GeneratedModel.CanTransition(BusinessObjectTypes.WorkPacket, "blocked", "awaiting-decision"));
    }

    [Fact]
    public void CanTransition_WorkPacket_DoneToAny_IsFalse()
    {
        // "done" is a terminal state — no outgoing transitions.
        Assert.False(GeneratedModel.CanTransition(BusinessObjectTypes.WorkPacket, "done", "todo"));
        Assert.False(GeneratedModel.CanTransition(BusinessObjectTypes.WorkPacket, "done", "in-progress"));
    }

    [Fact]
    public void CanTransition_ToolOffering_CandidateToSchemaReady_IsTrue()
    {
        // new StateTransitionContract("candidate", "schema-ready", "schemas-generated")
        Assert.True(GeneratedModel.CanTransition(BusinessObjectTypes.ToolOffering, "candidate", "schema-ready"));
    }

    [Fact]
    public void CanTransition_UnknownObjectType_ReturnsFalse()
    {
        Assert.False(GeneratedModel.CanTransition("not-an-object-type", "a", "b"));
    }

    // =======================================================================
    // InitialState
    // =======================================================================

    [Theory]
    [InlineData(BusinessObjectTypes.KnowledgeSource, "landed")]
    [InlineData(BusinessObjectTypes.KnowledgeChunk, "created")]
    [InlineData(BusinessObjectTypes.WorkPacket, "todo")]
    [InlineData(BusinessObjectTypes.ToolOffering, "candidate")]
    [InlineData(BusinessObjectTypes.DecisionRecord, "proposed")]
    [InlineData(BusinessObjectTypes.CapabilityExercise, "draft")]
    [InlineData(BusinessObjectTypes.EvidencePack, "collecting")]
    [InlineData(BusinessObjectTypes.ScenarioTemplate, "draft")]
    [InlineData(BusinessObjectTypes.KnowledgeGraphSnapshot, "requested")]
    public void InitialState_KnownObjectType_ReturnsExpectedState(string objectType, string expectedInitial)
    {
        Assert.Equal(expectedInitial, GeneratedModel.InitialState(objectType));
    }

    [Fact]
    public void InitialState_UnknownObjectType_ReturnsNull()
    {
        Assert.Null(GeneratedModel.InitialState("not-an-object-type"));
    }

    // =======================================================================
    // IsTerminalState
    // =======================================================================

    [Theory]
    [InlineData("searchable")]
    [InlineData("archived")]
    [InlineData("failed")]
    public void IsTerminalState_KnowledgeSource_TerminalStatesAreRecognised(string terminal)
    {
        Assert.True(GeneratedModel.IsTerminalState(BusinessObjectTypes.KnowledgeSource, terminal));
    }

    [Theory]
    [InlineData("landed")]
    [InlineData("ingesting")]
    [InlineData("indexed")]
    public void IsTerminalState_KnowledgeSource_NonTerminalStatesReturnFalse(string nonTerminal)
    {
        Assert.False(GeneratedModel.IsTerminalState(BusinessObjectTypes.KnowledgeSource, nonTerminal));
    }

    [Fact]
    public void IsTerminalState_WorkPacket_DoneIsTerminal()
    {
        Assert.True(GeneratedModel.IsTerminalState(BusinessObjectTypes.WorkPacket, "done"));
    }

    [Fact]
    public void IsTerminalState_WorkPacket_InProgressIsNotTerminal()
    {
        Assert.False(GeneratedModel.IsTerminalState(BusinessObjectTypes.WorkPacket, "in-progress"));
    }

    [Fact]
    public void IsTerminalState_UnknownObjectType_ReturnsFalse()
    {
        Assert.False(GeneratedModel.IsTerminalState("not-an-object-type", "landed"));
    }

    // =======================================================================
    // ToModelString() extension — StateNames round-trips
    // =======================================================================

    // KnowledgeSourceState
    [Theory]
    [InlineData(KnowledgeSourceState.Landed, "landed")]
    [InlineData(KnowledgeSourceState.Ingesting, "ingesting")]
    [InlineData(KnowledgeSourceState.Indexed, "indexed")]
    [InlineData(KnowledgeSourceState.Searchable, "searchable")]
    [InlineData(KnowledgeSourceState.Archived, "archived")]
    [InlineData(KnowledgeSourceState.Failed, "failed")]
    public void ToModelString_KnowledgeSourceState_RoundTrips(KnowledgeSourceState value, string expected)
    {
        Assert.Equal(expected, value.ToModelString());
    }

    // WorkPacketState — includes multi-word kebab-case entries
    [Theory]
    [InlineData(WorkPacketState.Todo, "todo")]
    [InlineData(WorkPacketState.Ready, "ready")]
    [InlineData(WorkPacketState.InProgress, "in-progress")]
    [InlineData(WorkPacketState.InReview, "in-review")]
    [InlineData(WorkPacketState.Done, "done")]
    [InlineData(WorkPacketState.Blocked, "blocked")]
    [InlineData(WorkPacketState.AwaitingDecision, "awaiting-decision")]
    public void ToModelString_WorkPacketState_RoundTrips(WorkPacketState value, string expected)
    {
        Assert.Equal(expected, value.ToModelString());
    }

    // ToolOfferingState — contains the hyphenated "schema-ready"
    [Theory]
    [InlineData(ToolOfferingState.Candidate, "candidate")]
    [InlineData(ToolOfferingState.SchemaReady, "schema-ready")]
    [InlineData(ToolOfferingState.Enabled, "enabled")]
    [InlineData(ToolOfferingState.Disabled, "disabled")]
    [InlineData(ToolOfferingState.Deprecated, "deprecated")]
    public void ToModelString_ToolOfferingState_RoundTrips(ToolOfferingState value, string expected)
    {
        Assert.Equal(expected, value.ToModelString());
    }

    // Verify that ToModelString() values ARE valid states according to the
    // enforcement API — i.e. the two systems agree.
    [Fact]
    public void ToModelString_KnowledgeSource_ValuesAreValidStatesInEnforcementApi()
    {
        foreach (KnowledgeSourceState state in Enum.GetValues<KnowledgeSourceState>())
        {
            string modelString = state.ToModelString();
            Assert.True(
                GeneratedModel.IsValidState(BusinessObjectTypes.KnowledgeSource, modelString),
                $"KnowledgeSourceState.{state} → \"{modelString}\" is not recognised by GeneratedModel.IsValidState");
        }
    }

    [Fact]
    public void ToModelString_WorkPacket_ValuesAreValidStatesInEnforcementApi()
    {
        foreach (WorkPacketState state in Enum.GetValues<WorkPacketState>())
        {
            string modelString = state.ToModelString();
            Assert.True(
                GeneratedModel.IsValidState(BusinessObjectTypes.WorkPacket, modelString),
                $"WorkPacketState.{state} → \"{modelString}\" is not recognised by GeneratedModel.IsValidState");
        }
    }

    // =======================================================================
    // Structural sanity — StateMachines collection
    // =======================================================================

    [Fact]
    public void StateMachines_ContainsExpectedCount()
    {
        // Nine state machines are defined in StateMachineContracts.g.cs.
        Assert.Equal(9, GeneratedModel.StateMachines.Count);
    }

    [Fact]
    public void StateMachines_EachMachineHasDistinctObjectType()
    {
        var objectTypes = GeneratedModel.StateMachines.Select(m => m.ObjectType).ToList();
        Assert.Equal(objectTypes.Count, objectTypes.Distinct(StringComparer.Ordinal).Count());
    }
}
