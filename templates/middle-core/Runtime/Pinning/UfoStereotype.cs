using MiddleCore.Generated;

namespace MiddleCore.Runtime.Pinning;

/// <summary>
/// UFO/gUFO stereotype assigned to a middle-core concept.
///
/// Aligned to the concepts in <c>model/middle-core/ontology/top-level-ufo-lite.ttl</c>
/// and <c>middle-core.ttl</c>:
///   - Endurants  — objects with identity that persist through time.
///   - Perdurants — events/processes that unfold through time.
///   - Relators   — n-ary endurants that mediate other objects via typed roles.
/// </summary>
public enum UfoStereotype
{
    /// <summary>Stereotype is not yet mapped or is unknown.</summary>
    Unknown = 0,

    /// <summary>
    /// A <c>gufo:Kind</c> endurant — a rigid sortal that supplies identity
    /// criteria for its instances.  Business objects (SemanticAsset, EvidenceBundle,
    /// CapabilityObservation, GovernedDecision, etc.) are Kinds.
    /// </summary>
    Kind,

    /// <summary>
    /// A <c>gufo:SubKind</c> endurant — a rigid sortal that inherits identity
    /// criteria from a parent Kind.  LifecycleState is modelled as a SubKind.
    /// </summary>
    SubKind,

    /// <summary>
    /// A <c>gufo:EventType</c> perdurant — a type of temporal event, e.g. a
    /// state transition or scenario execution.
    /// </summary>
    EventType,

    /// <summary>
    /// A UFO relator endurant — mediates n participants via typed role bindings
    /// (hyperedge-as-vertex pattern).  Carries bitemporal and PROV-O metadata.
    /// </summary>
    Relator,
}

/// <summary>
/// Maps middle-core ontology concept names (as stored in
/// <see cref="BusinessObjectContract.OntologyConcept"/>) to their
/// <see cref="UfoStereotype"/>, aligned to the .ttl files.
/// </summary>
public static class ConceptToUfo
{
    // Hand-written v1 map; PIN-EN2 will generate this from the model.
    //
    // Concepts from top-level-ufo-lite.ttl (gufo:Kind / gufo:SubKind / gufo:EventType):
    //   mc:BusinessObjectKind   → Kind
    //   mc:LifecycleState       → SubKind
    //   mc:StateTransition      → EventType
    //   mc:ScenarioExecution    → EventType
    //   mc:EvidenceBundle       → Kind
    //   mc:CapabilityObservation→ Kind
    //   mc:SemanticAsset        → Kind
    //   mc:GovernedDecision     → Kind
    //
    // Concepts from middle-core.ttl (rdfs:Class — treated as Kind in our model):
    //   mc:ActorIntent          → Kind
    //   mc:ScenarioContract     → Kind
    //   mc:ToolCandidate        → Kind
    //
    // Relator concepts (declared in IR; not yet in .ttl — will land with PIN-EN2):
    //   ingest-evidence         → Relator

    private static readonly Dictionary<string, UfoStereotype> Map =
        new(StringComparer.Ordinal)
        {
            // gUFO Kinds from top-level-ufo-lite.ttl
            ["BusinessObjectKind"] = UfoStereotype.Kind,
            ["EvidenceBundle"] = UfoStereotype.Kind,
            ["CapabilityObservation"] = UfoStereotype.Kind,
            ["SemanticAsset"] = UfoStereotype.Kind,
            ["GovernedDecision"] = UfoStereotype.Kind,

            // gUFO SubKinds
            ["LifecycleState"] = UfoStereotype.SubKind,

            // gUFO EventTypes
            ["StateTransition"] = UfoStereotype.EventType,
            ["ScenarioExecution"] = UfoStereotype.EventType,

            // Middle-core.ttl Kinds (rdfs:Class, treated as Kind)
            ["ActorIntent"] = UfoStereotype.Kind,
            ["ScenarioContract"] = UfoStereotype.Kind,
            ["ToolCandidate"] = UfoStereotype.Kind,

            // Relators (hyperedge-as-vertex; see Reification-and-Hyperedges.md)
            ["ingest-evidence"] = UfoStereotype.Relator,
        };

    /// <summary>
    /// Returns the <see cref="UfoStereotype"/> for the given ontology concept name.
    /// Returns <see cref="UfoStereotype.Unknown"/> if the concept is not mapped.
    /// </summary>
    public static UfoStereotype Resolve(string ontologyConcept)
    {
        if (string.IsNullOrWhiteSpace(ontologyConcept))
        {
            return UfoStereotype.Unknown;
        }

        return Map.TryGetValue(ontologyConcept, out UfoStereotype stereotype)
            ? stereotype
            : UfoStereotype.Unknown;
    }

    /// <summary>
    /// Returns <c>true</c> if the concept maps to <see cref="UfoStereotype.EventType"/>
    /// (i.e. it is a perdurant).
    /// </summary>
    public static bool IsPerdurant(string ontologyConcept) =>
        Resolve(ontologyConcept) == UfoStereotype.EventType;

    /// <summary>
    /// Returns <c>true</c> if the concept maps to <see cref="UfoStereotype.Relator"/>.
    /// </summary>
    public static bool IsRelator(string ontologyConcept) =>
        Resolve(ontologyConcept) == UfoStereotype.Relator;
}
