namespace MiddleCore.Runtime.GraphQL;

// Builds the knowledge-drop object graph once at startup and exposes it as an
// immutable snapshot. GraphQL queries read this snapshot rather than the live,
// mutable ModelObjectGraph, so reads need no locking and never observe a
// half-built graph (the concurrency hazard of a shared mutable singleton).
public sealed class ModelGraphSnapshotProvider
{
    private readonly IReadOnlyDictionary<string, ModelObject> byId;

    public ModelGraphSnapshotProvider(KnowledgeDropScenarioRunner runner)
    {
        ScenarioRunResult result = runner
            .RunAsync(disableLastHandler: false, CancellationToken.None)
            .GetAwaiter()
            .GetResult();
        Snapshot = result.Graph;
        byId = Snapshot.Objects.ToDictionary(item => item.Id, StringComparer.Ordinal);
    }

    public ModelObjectGraphSnapshot Snapshot { get; }

    public ModelObject? GetObject(string id) =>
        byId.TryGetValue(id, out ModelObject? value) ? value : null;
}
