using Xunit;
using MiddleCore.Runtime;
using MiddleCore.Generated;

namespace MiddleCore.Tests;

// ---------------------------------------------------------------------------
// Minimal fake handler — all test setup is done inline so the test class
// stays easy to read.  TInput == TOutput == ScenarioExecutionContext matches
// the concrete constraint used by ScenarioRuntime.
// ---------------------------------------------------------------------------
file sealed class FakeStepHandler : IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>
{
    private readonly Func<ScenarioExecutionContext, CancellationToken, Task<ScenarioExecutionContext>>? _action;

    public FakeStepHandler(string stepId, bool enabled = true,
        Func<ScenarioExecutionContext, CancellationToken, Task<ScenarioExecutionContext>>? action = null)
    {
        StepId = stepId;
        Enabled = enabled;
        _action = action;
    }

    public string StepId { get; }
    public bool Enabled { get; }

    public Task<ScenarioExecutionContext> HandleAsync(ScenarioExecutionContext input, CancellationToken cancellationToken)
    {
        if (_action is not null)
            return _action(input, cancellationToken);

        return Task.FromResult(input);
    }
}

// ---------------------------------------------------------------------------
// Helper that builds a ScenarioRuntime from a handler list and an explicit
// ordered step-id sequence, using a fresh InMemoryEvidenceSink.
// ---------------------------------------------------------------------------
file static class RuntimeFactory
{
    public static (ScenarioRuntime Runtime, InMemoryEvidenceSink Sink) Build(
        IEnumerable<IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>> handlers,
        IReadOnlyList<string> orderedStepIds)
    {
        var sink = new InMemoryEvidenceSink();
        var runtime = new ScenarioRuntime(handlers, sink, orderedStepIds);
        return (runtime, sink);
    }
}

public sealed class ScenarioRuntimeTests
{
    // -----------------------------------------------------------------------
    // Happy path — every step has an enabled handler → Status == "passed"
    // -----------------------------------------------------------------------
    [Fact]
    public async Task RunAsync_AllStepsEnabled_ReturnsPassedStatus()
    {
        var steps = new[] { "step-a", "step-b", "step-c" };
        var handlers = steps.Select(id => new FakeStepHandler(id));
        var (runtime, _) = RuntimeFactory.Build(handlers, steps);

        var result = await runtime.RunAsync(new ScenarioRunRequest("scenario-x"), CancellationToken.None);

        Assert.Equal("passed", result.Status);
        Assert.Equal(steps.Length, result.Steps.Count);
        Assert.All(result.Steps, s => Assert.Equal("passed", s.Status));
    }

    // -----------------------------------------------------------------------
    // Disabled handler at each position (parametrised via [Theory]).
    // The first disabled step must short-circuit and return "failed".
    // -----------------------------------------------------------------------
    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(2)]
    public async Task RunAsync_DisabledHandlerAtPosition_ReturnsFailed(int disabledIndex)
    {
        var stepIds = new[] { "step-0", "step-1", "step-2" };
        var handlers = stepIds.Select((id, i) => new FakeStepHandler(id, enabled: i != disabledIndex));
        var (runtime, sink) = RuntimeFactory.Build(handlers, stepIds);

        var result = await runtime.RunAsync(new ScenarioRunRequest("scenario-x"), CancellationToken.None);

        Assert.Equal("failed", result.Status);

        // The failing step is the disabled one.
        var failedStep = result.Steps.Last();
        Assert.Equal("failed", failedStep.Status);
        Assert.Equal(stepIds[disabledIndex], failedStep.StepId);

        // Evidence sink must have recorded exactly the steps that were attempted
        // (all steps before the disabled one, plus the failure itself).
        var evidence = sink.Snapshot();
        Assert.Equal(disabledIndex + 1, evidence.Count);
        Assert.Equal("failed", evidence.Last().Status);
    }

    // -----------------------------------------------------------------------
    // Unknown step — orderedStepIds references a step id that has no handler
    // registered at all → should return "failed" (not throw).
    // -----------------------------------------------------------------------
    [Fact]
    public async Task RunAsync_UnknownStep_ReturnsFailed()
    {
        var knownHandler = new FakeStepHandler("known-step");
        var orderedSteps = new[] { "known-step", "ghost-step" };
        var (runtime, _) = RuntimeFactory.Build([knownHandler], orderedSteps);

        var result = await runtime.RunAsync(new ScenarioRunRequest("scenario-x"), CancellationToken.None);

        Assert.Equal("failed", result.Status);
        var failedStep = result.Steps.Last();
        Assert.Equal("ghost-step", failedStep.StepId);
        Assert.Equal("failed", failedStep.Status);
    }

    // -----------------------------------------------------------------------
    // DisableLastHandler=true → runtime appends ":disabled" suffix to the last
    // step id in orderedStepIds which causes that step to fail even when a
    // handler with that id exists and is Enabled.
    // -----------------------------------------------------------------------
    [Fact]
    public async Task RunAsync_DisableLastHandlerTrue_LastStepFails()
    {
        var steps = new[] { "step-a", "step-b", "step-last" };
        var handlers = steps.Select(id => new FakeStepHandler(id));
        var (runtime, _) = RuntimeFactory.Build(handlers, steps);

        var result = await runtime.RunAsync(
            new ScenarioRunRequest("scenario-x", DisableLastHandler: true),
            CancellationToken.None);

        Assert.Equal("failed", result.Status);

        var failedStep = result.Steps.Last();
        // The runtime strips ":disabled" from the step id before recording it.
        Assert.Equal("step-last", failedStep.StepId);
        Assert.Equal("failed", failedStep.Status);
    }

    // -----------------------------------------------------------------------
    // Handler throws a non-cancellation exception → must surface as a clean
    // failed step (Status=="failed", descriptive Message), NOT an unhandled
    // exception bubbling to the caller.
    // -----------------------------------------------------------------------
    [Fact]
    public async Task RunAsync_HandlerThrows_ReturnsFaultedStepNotException()
    {
        const string faultingStepId = "faulting-step";
        const string exceptionMessage = "simulated projection drift";

        var handlers = new IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>[]
        {
            new FakeStepHandler("step-before"),
            new FakeStepHandler(faultingStepId, enabled: true, action: (_, _) =>
                Task.FromException<ScenarioExecutionContext>(new InvalidOperationException(exceptionMessage))),
        };

        var (runtime, sink) = RuntimeFactory.Build(handlers, ["step-before", faultingStepId]);

        // Must NOT throw.
        var result = await runtime.RunAsync(new ScenarioRunRequest("scenario-x"), CancellationToken.None);

        Assert.Equal("failed", result.Status);

        var faultedStep = result.Steps.Last();
        Assert.Equal(faultingStepId, faultedStep.StepId);
        Assert.Equal("failed", faultedStep.Status);
        Assert.Contains(exceptionMessage, faultedStep.Message, StringComparison.Ordinal);

        // Evidence sink should have the faulted step recorded.
        var evidence = sink.Snapshot();
        Assert.Equal("failed", evidence.Last().Status);
    }

    // -----------------------------------------------------------------------
    // CancellationToken is honoured — OperationCanceledException re-throws
    // (is NOT swallowed like other exceptions).
    // -----------------------------------------------------------------------
    [Fact]
    public async Task RunAsync_HandlerObservesCancellation_ThrowsOperationCanceledException()
    {
        using var cts = new CancellationTokenSource();

        var handlers = new IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>[]
        {
            new FakeStepHandler("cancelling-step", enabled: true, action: (_, ct) =>
            {
                ct.ThrowIfCancellationRequested();
                return Task.FromResult<ScenarioExecutionContext>(null!);
            }),
        };

        var (runtime, _) = RuntimeFactory.Build(handlers, ["cancelling-step"]);
        cts.Cancel();

        await Assert.ThrowsAsync<OperationCanceledException>(
            () => runtime.RunAsync(new ScenarioRunRequest("scenario-x"), cts.Token));
    }

    // -----------------------------------------------------------------------
    // ScenarioRunResult carries the ScenarioId from the request.
    // -----------------------------------------------------------------------
    [Fact]
    public async Task RunAsync_ReturnsResultWithCorrectScenarioId()
    {
        var (runtime, _) = RuntimeFactory.Build(
            [new FakeStepHandler("only-step")],
            ["only-step"]);

        var result = await runtime.RunAsync(
            new ScenarioRunRequest("my-unique-scenario-id"),
            CancellationToken.None);

        Assert.Equal("my-unique-scenario-id", result.ScenarioId);
    }
}
