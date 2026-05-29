/// The sift ladder (ARC-ADR-033) — propose has happened; here the formal layer
/// DISPOSES.
///
/// Two category-theoretic structures, used deliberately:
///   * L1 short-circuits with the **Result monad** — an ill-formed fragment cannot
///     even be projected, so there is nothing for L2-L4 to judge; bind stops.
///   * L2-L4 ACCUMULATE with a **Validation applicative** — they are independent
///     checks, so all their violations are gathered into a list (a free monoid)
///     rather than failing fast. (A monad would discard the later failures.)
/// The outcome is the coproduct `Snapped | Quarantined`: by the universal property
/// every consumer must handle both arms — there is no third "maybe promoted" state.
module OntologySift.Sift

open OntologySift.Ir
open OntologySift.Project

type Level =
    | L1Schema
    | L2Antipattern
    | L3Reasoner
    | L4Shacl

type Violation = { Level: Level; Detail: string }

type SiftOutcome =
    | Snapped of Triple list
    | Quarantined of Violation list

/// gUFO endurants are BFO continuants; events/situations are occurrents.
let private impliesContinuant =
    function
    | Event | Situation -> false
    | Kind | SubKind | Role | Phase | Category | Mixin | Relator | Quality | Mode -> true

let private bfoIsContinuant =
    function
    | Process -> false
    | IndependentContinuant | SpecificallyDependentContinuant
    | GenericallyDependentContinuant | BfoQuality | BfoRole | Disposition -> true

/// L1 — structural well-formedness. The stereotype/BFO spaces are already total by
/// construction (you cannot build an invalid stereotype), so the only L1 failures
/// are an empty fragment or an entity with no id / no source spans.
let l1 (f: Fragment) : Result<unit, Violation> =
    if List.isEmpty f.Entities && List.isEmpty f.Relations then
        Error { Level = L1Schema; Detail = "fragment has no entities or relations" }
    elif f.Entities |> List.exists (fun e -> e.Id = "" || List.isEmpty e.Spans) then
        Error { Level = L1Schema; Detail = "an entity has an empty id or no source spans" }
    else
        Ok()

/// L2 — OntoUML anti-pattern: every role filler must reference a declared entity.
let l2 (f: Fragment) : Result<unit, Violation> =
    let ids = f.Entities |> List.map (fun e -> e.Id) |> Set.ofList
    let dangling =
        [ for r in f.Relations do
            for role in r.Roles do
                if not (ids.Contains role.Filler) then
                    sprintf "relator '%s' role '%s' binds undeclared entity '%s'" r.Id role.Role role.Filler ]
    if List.isEmpty dangling then Ok()
    else Error { Level = L2Antipattern; Detail = String.concat "; " dangling }

/// L3 — the gUFO and BFO classifications must AGREE on continuant-vs-occurrent. A
/// concept typed Event (occurrent) but grounded to IndependentContinuant is
/// inconsistent, not merely implausible. Relations are Relators (continuants), so
/// their BFO grounding must be continuant too.
let l3 (f: Fragment) : Result<unit, Violation> =
    let bad =
        [ for e in f.Entities do
            if impliesContinuant e.Stereotype <> bfoIsContinuant e.Bfo then
                sprintf "%s: gUFO %A and BFO %A disagree (continuant/occurrent)" e.Id e.Stereotype e.Bfo
          for r in f.Relations do
            if not (bfoIsContinuant r.Bfo) then
                sprintf "%s: a relator cannot be grounded to occurrent BFO %A" r.Id r.Bfo ]
    if List.isEmpty bad then Ok()
    else Error { Level = L3Reasoner; Detail = String.concat "; " bad }

/// L4 — the core SHACL shape: a relator must mediate at least two DISTINCT
/// participants (under-mediation is the canonical OntoUML relator anti-pattern).
let l4 (f: Fragment) : Result<unit, Violation> =
    let bad =
        [ for r in f.Relations do
            let distinct = r.Roles |> List.map (fun x -> x.Filler) |> List.distinct
            if List.length distinct < 2 then
                sprintf "%s mediates %d distinct participant(s); a relator needs >= 2" r.Id (List.length distinct) ]
    if List.isEmpty bad then Ok()
    else Error { Level = L4Shacl; Detail = String.concat "; " bad }

/// The loop: L1 gates (monadic), then L2-L4 accumulate (applicative), then snap
/// (= project, the catamorphism) iff nothing failed, else quarantine with the full
/// violation report. Only the PROVEN reaches canonical.
let sift (f: Fragment) : SiftOutcome =
    match l1 f with
    | Error v -> Quarantined [ v ]
    | Ok() ->
        let violations =
            [ l2 f; l3 f; l4 f ]
            |> List.choose (function
                | Error v -> Some v
                | Ok() -> None)
        if List.isEmpty violations then Snapped(project f)
        else Quarantined violations
