namespace MiddleCore.Runtime.Pinning;

/// <summary>
/// PROV-O-aligned provenance metadata attached to a pinning operation.
/// Immutable by design — a stamp is never mutated after it is created.
/// </summary>
/// <param name="RecordedAt">
/// ISO-8601 UTC timestamp at which the pinning operation was executed
/// (transaction time / "recorded_at").  Supplied by <see cref="ISerializationClock"/>.
/// </param>
/// <param name="AgentId">
/// Identifier of the agent or process that triggered the pin
/// (maps to PROV-O <c>prov:wasAttributedTo</c>).
/// </param>
/// <param name="ActivityId">
/// Identifier of the activity that generated this pinned element
/// (maps to PROV-O <c>prov:wasGeneratedBy</c>).
/// </param>
/// <param name="SchemaVersion">
/// The model schema version at the time of pinning
/// (e.g. <c>middle-core-model.v1</c>).
/// </param>
public sealed record ProvenanceStamp(
    string RecordedAt,
    string AgentId,
    string ActivityId,
    string SchemaVersion)
{
    /// <summary>
    /// Creates a <see cref="ProvenanceStamp"/> using the supplied
    /// <see cref="ISerializationClock"/> for the <see cref="RecordedAt"/> timestamp.
    /// </summary>
    /// <param name="clock">Clock used to produce <see cref="RecordedAt"/>.</param>
    /// <param name="agentId">Agent/process identifier.</param>
    /// <param name="activityId">Activity identifier.</param>
    /// <param name="schemaVersion">Model schema version.</param>
    public static ProvenanceStamp Create(
        ISerializationClock clock,
        string agentId,
        string activityId,
        string schemaVersion)
    {
        ArgumentNullException.ThrowIfNull(clock);
        ArgumentException.ThrowIfNullOrWhiteSpace(agentId);
        ArgumentException.ThrowIfNullOrWhiteSpace(activityId);
        ArgumentException.ThrowIfNullOrWhiteSpace(schemaVersion);

        return new ProvenanceStamp(
            RecordedAt: clock.UtcNow(),
            AgentId: agentId,
            ActivityId: activityId,
            SchemaVersion: schemaVersion);
    }
}
