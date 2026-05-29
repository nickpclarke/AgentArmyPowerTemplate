/// The ontology IR — the coproduct at the heart of the compiler core (ARC-ADR-033).
///
/// Every type here is a SUM of cases. A discriminated union is a coproduct in the
/// category of types: a projection *out* of it (Stereotype -> anything) is defined
/// by giving an arm per case, and the compiler (FS0025-as-error, see the .fsproj)
/// refuses any projection missing an arm. So the "every concept must be handled,
/// nothing silently dropped" property the Python reference enforces with tests is
/// here a structural guarantee of the build.
module OntologySift.Ir

/// The OntoUML / gUFO stereotype space — the IR's spine.
type Stereotype =
    | Kind | SubKind | Role | Phase | Category | Mixin
    | Relator | Quality | Mode | Event | Situation

/// BFO 2020 upper categories — the dual grounding (ARC-ADR-032 facet B). The L3
/// gate forces the gUFO stereotype and this BFO class to agree.
type BfoClass =
    | IndependentContinuant | SpecificallyDependentContinuant
    | GenericallyDependentContinuant | BfoQuality | BfoRole | Disposition | Process

/// A character span in the source document — the anchor PROV-O lineage traces to.
type Span = { Start: int; End: int }

type Entity =
    { Id: string
      Label: string
      Stereotype: Stereotype
      Bfo: BfoClass
      Spans: Span list }

type RoleBinding = { Role: string; Filler: string }

/// A reified n-ary relation (hyperedge-as-vertex, ADR-016). Its gUFO stereotype is
/// always Relator, so it is not stored — the type already says so; only the BFO
/// grounding varies.
type Relation =
    { Id: string
      Label: string
      Bfo: BfoClass
      Roles: RoleBinding list
      Spans: Span list }

type Source = { Doc: string }

type Fragment =
    { FragmentId: string
      Source: Source
      Entities: Entity list
      Relations: Relation list }
