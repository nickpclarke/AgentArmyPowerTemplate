using Xunit;
using MiddleCore.Runtime;
using MiddleCore.Generated;

namespace MiddleCore.Tests;

public sealed class ModelGraphTests
{
    // -----------------------------------------------------------------------
    // AddObject — unknown objectType throws InvalidOperationException
    // -----------------------------------------------------------------------
    [Fact]
    public void AddObject_UnknownObjectType_ThrowsInvalidOperationException()
    {
        var graph = new ModelObjectGraph();

        var ex = Assert.Throws<InvalidOperationException>(
            () => graph.AddObject("id-1", "not-a-real-type", new object()));

        Assert.Contains("not-a-real-type", ex.Message, StringComparison.Ordinal);
    }

    // -----------------------------------------------------------------------
    // AddObject — duplicate id on the same graph throws
    // -----------------------------------------------------------------------
    [Fact]
    public void AddObject_DuplicateId_ThrowsInvalidOperationException()
    {
        var graph = new ModelObjectGraph();
        graph.AddObject("ks-1", BusinessObjectTypes.KnowledgeSource, new object());

        var ex = Assert.Throws<InvalidOperationException>(
            () => graph.AddObject("ks-1", BusinessObjectTypes.KnowledgeChunk, new object()));

        Assert.Contains("ks-1", ex.Message, StringComparison.Ordinal);
    }

    // -----------------------------------------------------------------------
    // AddEdge — unknown fromObjectId throws
    // -----------------------------------------------------------------------
    [Fact]
    public void AddEdge_UnknownFromObjectId_ThrowsInvalidOperationException()
    {
        var graph = new ModelObjectGraph();
        graph.AddObject("target", BusinessObjectTypes.WorkPacket, new object());

        var ex = Assert.Throws<InvalidOperationException>(
            () => graph.AddEdge("ghost-source", "relates-to", "target"));

        Assert.Contains("ghost-source", ex.Message, StringComparison.Ordinal);
    }

    // -----------------------------------------------------------------------
    // AddEdge — unknown toObjectId throws
    // -----------------------------------------------------------------------
    [Fact]
    public void AddEdge_UnknownToObjectId_ThrowsInvalidOperationException()
    {
        var graph = new ModelObjectGraph();
        graph.AddObject("source", BusinessObjectTypes.KnowledgeSource, new object());

        var ex = Assert.Throws<InvalidOperationException>(
            () => graph.AddEdge("source", "relates-to", "ghost-target"));

        Assert.Contains("ghost-target", ex.Message, StringComparison.Ordinal);
    }

    // -----------------------------------------------------------------------
    // FindByType — returns only objects of the requested type
    // -----------------------------------------------------------------------
    [Fact]
    public void FindByType_ReturnsOnlyMatchingObjects()
    {
        var graph = new ModelObjectGraph();

        graph.AddObject("ks-1", BusinessObjectTypes.KnowledgeSource, new object());
        graph.AddObject("ks-2", BusinessObjectTypes.KnowledgeSource, new object());
        graph.AddObject("wp-1", BusinessObjectTypes.WorkPacket, new object());

        var sources = graph.FindByType(BusinessObjectTypes.KnowledgeSource);
        var packets = graph.FindByType(BusinessObjectTypes.WorkPacket);
        var chunks  = graph.FindByType(BusinessObjectTypes.KnowledgeChunk);

        Assert.Equal(2, sources.Count);
        Assert.All(sources, obj => Assert.Equal(BusinessObjectTypes.KnowledgeSource, obj.ObjectType));

        Assert.Single(packets);
        Assert.Equal("wp-1", packets[0].Id);

        Assert.Empty(chunks);
    }

    // -----------------------------------------------------------------------
    // Snapshot.CountsByType reflects the actual type breakdown
    // -----------------------------------------------------------------------
    [Fact]
    public void Snapshot_CountsByType_ReflectsObjectBreakdown()
    {
        var graph = new ModelObjectGraph();

        graph.AddObject("ks-1", BusinessObjectTypes.KnowledgeSource, new object());
        graph.AddObject("ks-2", BusinessObjectTypes.KnowledgeSource, new object());
        graph.AddObject("kc-1", BusinessObjectTypes.KnowledgeChunk, new object());
        graph.AddObject("ep-1", BusinessObjectTypes.EvidencePack, new object());

        graph.AddEdge("ks-1", "produced", "kc-1");
        graph.AddEdge("ks-1", "produced", "ep-1");

        var snapshot = graph.Snapshot();

        Assert.Equal(2, snapshot.CountsByType[BusinessObjectTypes.KnowledgeSource]);
        Assert.Equal(1, snapshot.CountsByType[BusinessObjectTypes.KnowledgeChunk]);
        Assert.Equal(1, snapshot.CountsByType[BusinessObjectTypes.EvidencePack]);

        // Types that were never added must not appear in the dictionary.
        Assert.False(snapshot.CountsByType.ContainsKey(BusinessObjectTypes.WorkPacket));

        Assert.Equal(2, snapshot.Edges.Count);
    }

    // -----------------------------------------------------------------------
    // Snapshot is a point-in-time copy — mutations after the snapshot do not
    // change the snapshot's counts.
    // -----------------------------------------------------------------------
    [Fact]
    public void Snapshot_IsImmutablePointInTime()
    {
        var graph = new ModelObjectGraph();
        graph.AddObject("ks-1", BusinessObjectTypes.KnowledgeSource, new object());

        var before = graph.Snapshot();
        Assert.Equal(1, before.Objects.Count);

        graph.AddObject("ks-2", BusinessObjectTypes.KnowledgeSource, new object());

        var after = graph.Snapshot();
        Assert.Equal(1, before.Objects.Count);  // unchanged
        Assert.Equal(2, after.Objects.Count);
    }

    // -----------------------------------------------------------------------
    // AddObject — returned ModelObject carries the correct id and objectType
    // -----------------------------------------------------------------------
    [Fact]
    public void AddObject_ReturnsModelObjectWithCorrectProperties()
    {
        var graph = new ModelObjectGraph();
        var data  = new { Value = 42 };

        var obj = graph.AddObject("tool-1", BusinessObjectTypes.ToolOffering, data);

        Assert.Equal("tool-1", obj.Id);
        Assert.Equal(BusinessObjectTypes.ToolOffering, obj.ObjectType);
        Assert.Same(data, obj.Data);
    }
}
