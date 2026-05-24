using MiddleCore.Generated;

namespace MiddleCore.Runtime;

internal static class ScenarioGuards
{
    public static T RequireSingle<T>(IReadOnlyList<T> items, string description)
    {
        if (items.Count != 1)
        {
            throw new InvalidOperationException($"Expected exactly one {description} but found {items.Count}.");
        }

        return items[0];
    }
}

public sealed class KnowledgeDropScenarioRunner
{
    private static readonly string[] StepIds =
    [
        WorkflowStepIds.ValidateSourcePolicy,
        WorkflowStepIds.LandRawObject,
        WorkflowStepIds.GenerateKnowledgeChunks,
        WorkflowStepIds.AssembleIngestEvidence
    ];

    private readonly IProjectionPort projectionPort;

    public KnowledgeDropScenarioRunner(IProjectionPort projectionPort)
    {
        this.projectionPort = projectionPort;
    }

    public Task<ScenarioRunResult> RunAsync(bool disableLastHandler, CancellationToken cancellationToken)
    {
        IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>[] handlers =
        [
            new ValidateSourcePolicyHandler(),
            new LandRawObjectHandler(projectionPort),
            new GenerateKnowledgeChunksHandler(projectionPort),
            new AssembleIngestEvidenceHandler()
        ];

        ScenarioRuntime runtime = new(handlers, new InMemoryEvidenceSink(), StepIds);
        return runtime.RunAsync(new ScenarioRunRequest(ScenarioIds.KnowledgeDrop, disableLastHandler), cancellationToken);
    }
}

public sealed class FakeArcadeDbProjectionPort : IProjectionPort
{
    public string Provider => "fake-arcadedb";

    public Task<IReadOnlyList<ProjectionRecord>> ReadAsync(string projectionId, CancellationToken cancellationToken)
    {
        IReadOnlyList<ProjectionRecord> records = projectionId switch
        {
            "arcadedb-knowledge-source" =>
            [
                new ProjectionRecord(
                    "raw-object:platform-vision",
                    "RawObject",
                    new Dictionary<string, string>(StringComparer.Ordinal)
                    {
                        ["source_id"] = "source-platform-vision",
                        ["display_name"] = "Platform vision notes",
                        ["provider_ref"] = "arcadedb://RawObject/platform-vision"
                    })
            ],
            "arcadedb-knowledge-chunk" =>
            [
                new ProjectionRecord(
                    "chunk:platform-vision:001",
                    "Chunk",
                    new Dictionary<string, string>(StringComparer.Ordinal)
                    {
                        ["chunk_id"] = "chunk-platform-vision-001",
                        ["excerpt"] = "Middle-core compiles scenario contracts from model specs."
                    }),
                new ProjectionRecord(
                    "chunk:platform-vision:002",
                    "Chunk",
                    new Dictionary<string, string>(StringComparer.Ordinal)
                    {
                        ["chunk_id"] = "chunk-platform-vision-002",
                        ["excerpt"] = "Evidence packs prove graph changes before promotion."
                    })
            ],
            _ => []
        };

        return Task.FromResult(records);
    }
}

public sealed class ValidateSourcePolicyHandler : IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>
{
    public string StepId => WorkflowStepIds.ValidateSourcePolicy;
    public bool Enabled => true;

    public Task<ScenarioExecutionContext> HandleAsync(ScenarioExecutionContext input, CancellationToken cancellationToken)
    {
        DecisionRecordData decision = new(
            "decision-source-activation-policy",
            "accepted",
            "Prototype source passes deterministic activation policy.",
            "source-platform-vision");

        input.Graph.AddObject(decision.DecisionId, BusinessObjectTypes.DecisionRecord, decision);
        input.Bag["policy_status"] = "accepted";
        return Task.FromResult(input);
    }
}

public sealed class LandRawObjectHandler : IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>
{
    private readonly IProjectionPort projectionPort;

    public LandRawObjectHandler(IProjectionPort projectionPort)
    {
        this.projectionPort = projectionPort;
    }

    public string StepId => WorkflowStepIds.LandRawObject;
    public bool Enabled => true;

    public async Task<ScenarioExecutionContext> HandleAsync(ScenarioExecutionContext input, CancellationToken cancellationToken)
    {
        ProjectionRecord source = ScenarioGuards.RequireSingle(
            await projectionPort.ReadAsync("arcadedb-knowledge-source", cancellationToken),
            "arcadedb-knowledge-source projection record");
        KnowledgeSourceData data = new(
            source.Values["source_id"],
            source.Values["display_name"],
            "landed",
            source.Values["provider_ref"]);

        input.Graph.AddObject(data.SourceId, BusinessObjectTypes.KnowledgeSource, data);
        return input;
    }
}

public sealed class GenerateKnowledgeChunksHandler : IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>
{
    private readonly IProjectionPort projectionPort;

    public GenerateKnowledgeChunksHandler(IProjectionPort projectionPort)
    {
        this.projectionPort = projectionPort;
    }

    public string StepId => WorkflowStepIds.GenerateKnowledgeChunks;
    public bool Enabled => true;

    public async Task<ScenarioExecutionContext> HandleAsync(ScenarioExecutionContext input, CancellationToken cancellationToken)
    {
        ModelObject source = ScenarioGuards.RequireSingle(
            input.Graph.FindByType(BusinessObjectTypes.KnowledgeSource),
            "knowledge-source object");
        KnowledgeSourceData sourceData = (KnowledgeSourceData)source.Data;
        IReadOnlyList<ProjectionRecord> chunks = await projectionPort.ReadAsync("arcadedb-knowledge-chunk", cancellationToken);

        foreach (ProjectionRecord chunk in chunks)
        {
            KnowledgeChunkData data = new(
                chunk.Values["chunk_id"],
                sourceData.SourceId,
                chunk.Values["excerpt"],
                "searchable");

            input.Graph.AddObject(data.ChunkId, BusinessObjectTypes.KnowledgeChunk, data);
            input.Graph.AddEdge(sourceData.SourceId, "contains", data.ChunkId);
        }

        return input;
    }
}

public sealed class AssembleIngestEvidenceHandler : IWorkflowStepHandler<ScenarioExecutionContext, ScenarioExecutionContext>
{
    public string StepId => WorkflowStepIds.AssembleIngestEvidence;
    public bool Enabled => true;

    public Task<ScenarioExecutionContext> HandleAsync(ScenarioExecutionContext input, CancellationToken cancellationToken)
    {
        ModelObject source = ScenarioGuards.RequireSingle(
            input.Graph.FindByType(BusinessObjectTypes.KnowledgeSource),
            "knowledge-source object");
        KnowledgeSourceData sourceData = (KnowledgeSourceData)source.Data;
        int chunkCount = input.Graph.FindByType(BusinessObjectTypes.KnowledgeChunk).Count;
        string evidencePackId = "evidence-knowledge-drop-001";

        CapabilityExerciseData exercise = new(
            "exercise-knowledge-drop-001",
            ScenarioIds.KnowledgeDrop,
            "passed",
            evidencePackId);

        EvidencePackData evidence = new(
            evidencePackId,
            "complete",
            chunkCount + 2,
            ["fixture:model-runtime", "projection:fake-arcadedb"]);

        input.Graph.AddObject(exercise.ExerciseId, BusinessObjectTypes.CapabilityExercise, exercise);
        input.Graph.AddObject(evidence.EvidencePackId, BusinessObjectTypes.EvidencePack, evidence);
        input.Graph.AddEdge(exercise.ExerciseId, "proven-by", evidence.EvidencePackId);
        input.Graph.AddEdge(evidence.EvidencePackId, "supports", sourceData.SourceId);
        input.Graph.AddEdge(sourceData.SourceId, "produces", evidence.EvidencePackId);
        input.Evidence = evidence;
        return Task.FromResult(input);
    }
}
