using System.Text.Json;
using System.Text.Json.Serialization;
using HotChocolate;
using MiddleCore.Generated;

namespace MiddleCore.Runtime.GraphQL;

// A graph node flattened for GraphQL. The runtime stores heterogeneous data
// objects as `object`, so the payload is exposed as a JSON string the agent
// can parse rather than a single static GraphQL type.
public sealed record GraphNode(string Id, string ObjectType, string DataJson);

public sealed record GraphEdge(string From, string Relationship, string To);

public sealed record GraphNeighborhood(
    GraphNode Node,
    IReadOnlyList<GraphEdge> Outgoing,
    IReadOnlyList<GraphEdge> Incoming,
    IReadOnlyList<GraphNode> Neighbors);

public sealed class Query
{
    private static readonly JsonSerializerOptions DataJsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        Converters = { new JsonStringEnumConverter(JsonNamingPolicy.KebabCaseLower) },
    };

    // --- Schema tier: backed entirely by the generated contracts, so it tracks
    // the model automatically every time the authoring loop regenerates. ---

    public GeneratedModelDescription Model() => GeneratedModelValidator.Describe();

    public IReadOnlyList<BusinessObjectContract> BusinessObjects() => GeneratedModel.BusinessObjects;

    public BusinessObjectContract? BusinessObject(string id) =>
        GeneratedModel.BusinessObjects.FirstOrDefault(item => item.Id == id);

    public IReadOnlyList<ScenarioContract> Scenarios() => ScenarioContracts.Scenarios;

    public ScenarioContract? Scenario(string id) =>
        ScenarioContracts.Scenarios.FirstOrDefault(item => item.Id == id);

    public IReadOnlyList<StateMachineContract> StateMachines() => GeneratedModel.StateMachines;

    public StateMachineContract? StateMachine(string id) =>
        GeneratedModel.StateMachines.FirstOrDefault(item => item.Id == id);

    // --- Graph tier: reads the immutable knowledge-drop snapshot. ---

    public IReadOnlyList<GraphNode> GraphObjects(string? objectType, [Service] ModelGraphSnapshotProvider snapshots)
    {
        IEnumerable<ModelObject> objects = string.IsNullOrEmpty(objectType)
            ? snapshots.Snapshot.Objects
            : snapshots.Snapshot.Objects.Where(item => item.ObjectType == objectType);
        return objects.Select(ToNode).ToArray();
    }

    public IReadOnlyList<GraphEdge> GraphEdges([Service] ModelGraphSnapshotProvider snapshots) =>
        snapshots.Snapshot.Edges.Select(ToEdge).ToArray();

    public GraphNeighborhood? Node(string id, [Service] ModelGraphSnapshotProvider snapshots)
    {
        ModelObject? node = snapshots.GetObject(id);
        if (node is null)
            return null;

        IReadOnlyList<ModelEdge> edges = snapshots.Snapshot.Edges;
        GraphEdge[] outgoing = edges.Where(edge => edge.FromObjectId == id).Select(ToEdge).ToArray();
        GraphEdge[] incoming = edges.Where(edge => edge.ToObjectId == id).Select(ToEdge).ToArray();

        HashSet<string> neighborIds = new(StringComparer.Ordinal);
        foreach (GraphEdge edge in outgoing) neighborIds.Add(edge.To);
        foreach (GraphEdge edge in incoming) neighborIds.Add(edge.From);

        GraphNode[] neighbors = neighborIds
            .Select(snapshots.GetObject)
            .Where(neighbor => neighbor is not null)
            .Select(neighbor => ToNode(neighbor!))
            .ToArray();

        return new GraphNeighborhood(ToNode(node), outgoing, incoming, neighbors);
    }

    private static GraphNode ToNode(ModelObject node) =>
        new(node.Id, node.ObjectType, JsonSerializer.Serialize(node.Data, DataJsonOptions));

    private static GraphEdge ToEdge(ModelEdge edge) =>
        new(edge.FromObjectId, edge.RelationshipType, edge.ToObjectId);
}
