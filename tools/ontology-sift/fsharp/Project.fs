/// project : Fragment -> RDF — the FUNCTOR (ARC-ADR-033).
///
/// A structure-preserving map from the IR category into the RDF-graph category:
/// entities and relations (objects) and their role bindings (morphisms) map to
/// triples in a way that respects composition. Because it folds the whole fragment
/// down to a list of triples, it is a catamorphism over the IR. Total over both
/// Stereotype and BfoClass (the gufoIri / bfoIri arms are exhaustive — FS0025).
module OntologySift.Project

open OntologySift.Ir

type Triple = { S: string; P: string; O: string; OIsLiteral: bool }

/// Stereotype -> gUFO OWL class IRI. Total: add a stereotype and this won't build.
let gufoIri =
    function
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

/// BfoClass -> BFO IRI. Total over the BFO union.
let bfoIri =
    function
    | IndependentContinuant -> "bfo:IndependentContinuant"
    | SpecificallyDependentContinuant -> "bfo:SpecificallyDependentContinuant"
    | GenericallyDependentContinuant -> "bfo:GenericallyDependentContinuant"
    | BfoQuality -> "bfo:Quality"
    | BfoRole -> "bfo:Role"
    | Disposition -> "bfo:Disposition"
    | Process -> "bfo:Process"

let private ex (id: string) = "ex:" + id

/// Each entity -> dual gUFO+BFO type triples + label; each relation -> a gufo:Relator
/// vertex with one gufo:mediates edge per role binding. Mirrors the Python project().
let project (f: Fragment) : Triple list =
    [ for e in f.Entities do
        { S = ex e.Id; P = "rdf:type"; O = gufoIri e.Stereotype; OIsLiteral = false }
        { S = ex e.Id; P = "rdf:type"; O = bfoIri e.Bfo; OIsLiteral = false }
        { S = ex e.Id; P = "rdfs:label"; O = e.Label; OIsLiteral = true }
      for r in f.Relations do
        { S = ex r.Id; P = "rdf:type"; O = "gufo:Relator"; OIsLiteral = false }
        { S = ex r.Id; P = "rdf:type"; O = bfoIri r.Bfo; OIsLiteral = false }
        { S = ex r.Id; P = "rdfs:label"; O = r.Label; OIsLiteral = true }
        for role in r.Roles do
          { S = ex r.Id; P = "gufo:mediates"; O = ex role.Filler; OIsLiteral = false } ]

let toTurtle (triples: Triple list) : string =
    let header =
        "@prefix ex: <https://agentarmy.dev/ontology-sift/data#> .\n"
        + "@prefix gufo: <http://purl.org/nemo/gufo#> .\n"
        + "@prefix bfo: <http://purl.obolibrary.org/obo/bfo#> .\n"
        + "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\n"
    let line t =
        if t.OIsLiteral then sprintf "%s %s \"%s\" ." t.S t.P t.O
        else sprintf "%s %s %s ." t.S t.P t.O
    header + (triples |> List.map line |> String.concat "\n") + "\n"
