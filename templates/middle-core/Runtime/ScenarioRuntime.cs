namespace MiddleCore.Runtime;

public interface IScenarioRuntime
{
    Task<ScenarioRunResult> RunAsync(ScenarioRunRequest request, CancellationToken cancellationToken);
}

public interface IWorkflowStepHandler<TInput, TOutput>
{
    string StepId { get; }
    bool Enabled { get; }
    Task<TOutput> HandleAsync(TInput input, CancellationToken cancellationToken);
}

public interface IProjectionPort
{
    string Provider { get; }
    Task<IReadOnlyList<ProjectionRecord>> ReadAsync(string projectionId, CancellationToken cancellationToken);
}

public interface IEvidenceSink
{
    void Record(ScenarioStepResult result);
    IReadOnlyList<ScenarioStepResult> Snapshot();
}

public sealed record ProjectionRecord(string Id, string RecordType, IReadOnlyDictionary<string, string> Values);

public sealed record ScenarioRunRequest(string ScenarioId, bool DisableLastHandler = false);

public sealed record ScenarioStepResult(
    string StepId,
    string Status,
    string Message,
    IReadOnlyDictionary<string, int> ObjectCounts);

public sealed record ScenarioRunResult(
    string ScenarioId,
    string Status,
    IReadOnlyList<ScenarioStepResult> Steps,
    ModelObjectGraphSnapshot Graph,
    object? Evidence);

public sealed class ScenarioExecutionContext
{
    public ScenarioExecutionContext(string scenarioId, IModelObjectGraph graph)
    {
        ScenarioId = scenarioId;
        Graph = graph;
    }

    public string ScenarioId { get; }
    public IModelObjectGraph Graph { get; }
    public object? Evidence { get; set; }
    public Dictionary<string, string> Bag { get; } = new(StringComparer.Ordinal);

    public ScenarioStepResult StepSucceeded(string stepId, string message) =>
        new(stepId, "passed", message, Graph.Snapshot().CountsByType);

    public ScenarioStepResult StepFailed(string stepId, string message) =>
        new(stepId, "failed", message, Graph.Snapshot().CountsByType);
}

public sealed class ScenarioRuntime : IScenarioRuntime
{
    private readonly IReadOnlyDictionary<string, IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>> handlers;
    private readonly IEvidenceSink evidenceSink;
    private readonly IReadOnlyList<string> orderedStepIds;

    public ScenarioRuntime(
        IEnumerable<IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>> handlers,
        IEvidenceSink evidenceSink,
        IReadOnlyList<string> orderedStepIds)
    {
        this.handlers = handlers.ToDictionary(handler => handler.StepId, StringComparer.Ordinal);
        this.evidenceSink = evidenceSink;
        this.orderedStepIds = orderedStepIds;
    }

    public async Task<ScenarioRunResult> RunAsync(ScenarioRunRequest request, CancellationToken cancellationToken)
    {
        ModelObjectGraph graph = new();
        ScenarioExecutionContext context = new(request.ScenarioId, graph);
        List<ScenarioStepResult> stepResults = [];

        IReadOnlyList<string> steps = request.DisableLastHandler && orderedStepIds.Count > 0
            ? orderedStepIds.Take(orderedStepIds.Count - 1).Append(orderedStepIds[^1] + ":disabled").ToArray()
            : orderedStepIds;

        foreach (string stepId in steps)
        {
            string normalizedStepId = stepId.Replace(":disabled", "", StringComparison.Ordinal);
            if (!handlers.TryGetValue(normalizedStepId, out IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>? handler) || !handler.Enabled || stepId.EndsWith(":disabled", StringComparison.Ordinal))
            {
                ScenarioStepResult failure = context.StepFailed(normalizedStepId, $"Workflow step '{normalizedStepId}' has no enabled handler.");
                evidenceSink.Record(failure);
                stepResults.Add(failure);
                return new ScenarioRunResult(request.ScenarioId, "failed", stepResults, graph.Snapshot(), context.Evidence);
            }

            try
            {
                context = await handler.HandleAsync(context, cancellationToken);
            }
            catch (OperationCanceledException)
            {
                throw;
            }
            catch (Exception ex)
            {
                // A handler data-fault (e.g. projection drift) surfaces as a clean failed
                // step the caller can read, not an unhandled 500 from inside the scenario.
                ScenarioStepResult faulted = context.StepFailed(normalizedStepId, $"Workflow step '{normalizedStepId}' faulted: {ex.Message}");
                evidenceSink.Record(faulted);
                stepResults.Add(faulted);
                return new ScenarioRunResult(request.ScenarioId, "failed", stepResults, graph.Snapshot(), context.Evidence);
            }

            ScenarioStepResult result = context.StepSucceeded(normalizedStepId, $"Workflow step '{normalizedStepId}' completed.");
            evidenceSink.Record(result);
            stepResults.Add(result);
        }

        return new ScenarioRunResult(request.ScenarioId, "passed", stepResults, graph.Snapshot(), context.Evidence);
    }
}

public sealed class InMemoryEvidenceSink : IEvidenceSink
{
    private readonly List<ScenarioStepResult> results = [];

    public void Record(ScenarioStepResult result) => results.Add(result);

    public IReadOnlyList<ScenarioStepResult> Snapshot() => results.ToArray();
}
