namespace MiddleCore.Runtime;

public interface IModelObject
{
    string Id { get; }
    string ObjectType { get; }
    object Data { get; }
}

public interface IModelObjectGraph
{
    IReadOnlyList<ModelObject> Objects { get; }
    IReadOnlyList<ModelEdge> Edges { get; }
    ModelObject AddObject(string id, string objectType, object data);
    void AddEdge(string fromObjectId, string relationshipType, string toObjectId);
    IReadOnlyList<ModelObject> FindByType(string objectType);
    ModelObjectGraphSnapshot Snapshot();
}

public sealed record ModelObject(string Id, string ObjectType, object Data) : IModelObject;

public sealed record ModelEdge(string FromObjectId, string RelationshipType, string ToObjectId);

public sealed record ModelObjectGraphSnapshot(
    IReadOnlyList<ModelObject> Objects,
    IReadOnlyList<ModelEdge> Edges,
    IReadOnlyDictionary<string, int> CountsByType);

public sealed class ModelObjectGraph : IModelObjectGraph
{
    private readonly Dictionary<string, ModelObject> objects = new(StringComparer.Ordinal);
    private readonly List<ModelEdge> edges = [];

    public IReadOnlyList<ModelObject> Objects => objects.Values.ToArray();

    public IReadOnlyList<ModelEdge> Edges => edges;

    public ModelObject AddObject(string id, string objectType, object data)
    {
        ModelObject modelObject = new(id, objectType, data);
        objects[id] = modelObject;
        return modelObject;
    }

    public void AddEdge(string fromObjectId, string relationshipType, string toObjectId)
    {
        if (!objects.ContainsKey(fromObjectId))
            throw new InvalidOperationException($"Graph edge references unknown source object '{fromObjectId}'.");
        if (!objects.ContainsKey(toObjectId))
            throw new InvalidOperationException($"Graph edge references unknown target object '{toObjectId}'.");

        edges.Add(new ModelEdge(fromObjectId, relationshipType, toObjectId));
    }

    public IReadOnlyList<ModelObject> FindByType(string objectType) =>
        objects.Values.Where(item => item.ObjectType == objectType).ToArray();

    public ModelObjectGraphSnapshot Snapshot()
    {
        Dictionary<string, int> counts = objects.Values
            .GroupBy(item => item.ObjectType)
            .ToDictionary(group => group.Key, group => group.Count(), StringComparer.Ordinal);

        return new ModelObjectGraphSnapshot(Objects, edges.ToArray(), counts);
    }
}
