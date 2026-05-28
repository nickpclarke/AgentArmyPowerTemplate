// spikes/ontouml-ir.fsx — EXPLORATORY (no commitment). Does F#'s exhaustiveness
// guarantee earn a second .NET language for the IR -> projections compiler?
// (ARC-ADR-032 / Ontology-Pipeline north-star). Run:  dotnet fsi ontouml-ir.fsx
//
// The point to FEEL: every projection is a TOTAL function over the stereotype
// space. Add a stereotype to the union and the compiler refuses to build any
// projection that doesn't handle it (FS0025). That is "snapped, not plausible"
// enforced at the code level — you cannot ship a projection with a silent gap.

/// The OntoUML / gUFO stereotype space — the IR's spine, as a discriminated union.
type Stereotype =
    | Kind | SubKind | Role | Phase | Category | Mixin
    | Relator | Quality | Mode | Event | Situation

/// BFO 2020 top-level (the dual grounding — ADR-032 facet B).
type BfoClass =
    | IndependentContinuant | SpecificallyDependentContinuant
    | GenericallyDependentContinuant | BfoQuality | BfoRole | Disposition | Process

type Entity = { Id: string; Stereotype: Stereotype; Bfo: BfoClass }

// --- Projection 1: stereotype -> gUFO OWL class IRI (one of many projections) ---
let gufoIri (s: Stereotype) =
    match s with
    | Kind -> "gufo:Kind"
    | SubKind -> "gufo:SubKind"
    | Role -> "gufo:Role"
    | Phase -> "gufo:Phase"
    | Category -> "gufo:Category"
    | Mixin -> "gufo:Mixin"
    | Relator -> "gufo:Relator"
    | Quality -> "gufo:Quality"
    | Mode -> "gufo:Mode"
    | Event -> "gufo:Event"
    | Situation -> "gufo:Situation"

// --- Projection 2: the BFO upper bound a stereotype IMPLIES (the cross-check) ---
// gUFO endurants are BFO continuants; events/situations are occurrents.
let stereotypeImpliesContinuant (s: Stereotype) =
    match s with
    | Event | Situation -> false   // occurrents
    | Kind | SubKind | Role | Phase | Category | Mixin
    | Relator | Quality | Mode -> true

let declaredBfoIsContinuant (b: BfoClass) =
    match b with
    | Process -> false
    | IndependentContinuant | SpecificallyDependentContinuant
    | GenericallyDependentContinuant | BfoQuality | BfoRole | Disposition -> true

/// L3 cross-check as a total function: the gUFO and BFO classifications must agree.
/// (Same check the Python doctor proves at runtime — here it is structural.)
let l3Consistent (e: Entity) =
    stereotypeImpliesContinuant e.Stereotype = declaredBfoIsContinuant e.Bfo

let demo =
    [ { Id = "Risk";           Stereotype = Kind;    Bfo = GenericallyDependentContinuant }   // ok
      { Id = "MitigationCase"; Stereotype = Relator; Bfo = SpecificallyDependentContinuant }  // ok
      { Id = "RiskAssessment"; Stereotype = Event;   Bfo = IndependentContinuant } ]          // INCONSISTENT

printfn "%-16s %-9s %-32s gufo=%-12s L3consistent=%b" "id" "stereo" "bfo" "iri" true
printfn "%s" (String.replicate 92 "-")
for e in demo do
    printfn "%-16s %-9s %-32s gufo=%-12s L3consistent=%b"
        e.Id (string e.Stereotype) (string e.Bfo) (gufoIri e.Stereotype) (l3Consistent e)
