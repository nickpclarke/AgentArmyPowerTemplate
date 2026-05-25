using Xunit;
using MiddleCore.Runtime.Pinning;

namespace MiddleCore.Tests.Pinning;

public sealed class ProvenanceStampTests
{
    // -----------------------------------------------------------------------
    // Create — uses injected clock
    // -----------------------------------------------------------------------

    [Fact]
    public void Create_UsesClockForRecordedAt()
    {
        const string fixedTime = "2026-05-24T12:00:00.0000000Z";
        var clock = new FakeSerializationClock(fixedTime);

        ProvenanceStamp stamp = ProvenanceStamp.Create(
            clock,
            agentId: "middle-core-runtime",
            activityId: "pin-op-001",
            schemaVersion: "middle-core-model.v1");

        Assert.Equal(fixedTime, stamp.RecordedAt);
    }

    [Fact]
    public void Create_StoresAllFields()
    {
        var clock = new FakeSerializationClock("2026-05-24T12:00:00.0000000Z");

        ProvenanceStamp stamp = ProvenanceStamp.Create(
            clock,
            agentId: "test-agent",
            activityId: "test-activity",
            schemaVersion: "schema-v2");

        Assert.Equal("test-agent", stamp.AgentId);
        Assert.Equal("test-activity", stamp.ActivityId);
        Assert.Equal("schema-v2", stamp.SchemaVersion);
    }

    // -----------------------------------------------------------------------
    // Create — guard clauses
    // -----------------------------------------------------------------------

    [Fact]
    public void Create_NullClock_ThrowsArgumentNullException()
    {
        Assert.Throws<ArgumentNullException>(() =>
            ProvenanceStamp.Create(null!, "agent", "activity", "schema"));
    }

    [Fact]
    public void Create_EmptyAgentId_ThrowsArgumentException()
    {
        var clock = new FakeSerializationClock("2026-01-01T00:00:00.0000000Z");
        Assert.Throws<ArgumentException>(() =>
            ProvenanceStamp.Create(clock, "", "activity", "schema"));
    }

    [Fact]
    public void Create_WhitespaceActivityId_ThrowsArgumentException()
    {
        var clock = new FakeSerializationClock("2026-01-01T00:00:00.0000000Z");
        Assert.Throws<ArgumentException>(() =>
            ProvenanceStamp.Create(clock, "agent", "   ", "schema"));
    }

    [Fact]
    public void Create_EmptySchemaVersion_ThrowsArgumentException()
    {
        var clock = new FakeSerializationClock("2026-01-01T00:00:00.0000000Z");
        Assert.Throws<ArgumentException>(() =>
            ProvenanceStamp.Create(clock, "agent", "activity", ""));
    }

    // -----------------------------------------------------------------------
    // Immutability — record value equality
    // -----------------------------------------------------------------------

    [Fact]
    public void ProvenanceStamp_SameValues_AreEqual()
    {
        var clock = new FakeSerializationClock("2026-05-24T00:00:00.0000000Z");

        ProvenanceStamp a = ProvenanceStamp.Create(clock, "agent-a", "act-1", "v1");
        ProvenanceStamp b = ProvenanceStamp.Create(clock, "agent-a", "act-1", "v1");

        Assert.Equal(a, b);
    }

    [Fact]
    public void ProvenanceStamp_DifferentAgentId_AreNotEqual()
    {
        var clock = new FakeSerializationClock("2026-05-24T00:00:00.0000000Z");

        ProvenanceStamp a = ProvenanceStamp.Create(clock, "agent-a", "act-1", "v1");
        ProvenanceStamp b = ProvenanceStamp.Create(clock, "agent-b", "act-1", "v1");

        Assert.NotEqual(a, b);
    }
}
