/// F# sift doctor — proves PARITY with the Python reference (tools/ontology-sift):
/// the conformant fragment SNAPS (project -> canonical RDF); the two violators
/// QUARANTINE at the same level the Python doctor blocks them (L3 reasoner, L4
/// SHACL). Exit 0 on parity, 1 otherwise. Run:  dotnet run --project tools/ontology-sift/fsharp
module OntologySift.Program

open OntologySift.Ir
open OntologySift.Project
open OntologySift.Sift

let private span s e = { Start = s; End = e }

// Fixtures mirror the Python discipline fixtures (the risk/control thin slice).
let private conformant =
    { FragmentId = "frag-conformant-001"
      Source = { Doc = "risk-control.txt" }
      Entities =
        [ { Id = "Risk"; Label = "Risk"; Stereotype = Kind; Bfo = GenericallyDependentContinuant; Spans = [ span 0 4 ] }
          { Id = "Control"; Label = "Control"; Stereotype = Kind; Bfo = IndependentContinuant; Spans = [ span 5 12 ] }
          { Id = "RiskOwner"; Label = "Risk Owner"; Stereotype = Role; Bfo = BfoRole; Spans = [ span 13 23 ] } ]
      Relations =
        [ { Id = "MitigationCase"
            Label = "Mitigation Case"
            Bfo = SpecificallyDependentContinuant
            Roles = [ { Role = "mitigatedRisk"; Filler = "Risk" }; { Role = "mitigatingControl"; Filler = "Control" } ]
            Spans = [ span 24 39 ] } ] }

// Event stereotype + IndependentContinuant BFO -> the gUFO/BFO grounding disagree (L3).
let private violatingReason =
    { FragmentId = "frag-violating-reason-001"
      Source = { Doc = "risk-control.txt" }
      Entities = [ { Id = "RiskAssessment"; Label = "Risk Assessment"; Stereotype = Event; Bfo = IndependentContinuant; Spans = [ span 0 14 ] } ]
      Relations = [] }

// A relator mediating fewer than two distinct participants -> under-mediation (L4).
let private violatingShacl =
    { FragmentId = "frag-violating-shacl-001"
      Source = { Doc = "risk-control.txt" }
      Entities = [ { Id = "Risk"; Label = "Risk"; Stereotype = Kind; Bfo = GenericallyDependentContinuant; Spans = [ span 0 4 ] } ]
      Relations =
        [ { Id = "DanglingMitigation"; Label = "Dangling Mitigation"; Bfo = SpecificallyDependentContinuant
            Roles = [ { Role = "mitigatedRisk"; Filler = "Risk" } ]; Spans = [ span 5 13 ] } ] }

let private outcomeLine (f: Fragment) (expected: string) =
    match sift f with
    | Snapped triples ->
        let actual = "snapped"
        (actual = expected), sprintf "SNAPPED (%d triples)" (List.length triples), []
    | Quarantined vs ->
        let levels = vs |> List.map (fun v -> sprintf "%A" v.Level) |> String.concat ","
        ("quarantined" = expected), sprintf "QUARANTINED [%s]" levels, vs

[<EntryPoint>]
let main _ =
    let cases = [ conformant, "snapped"; violatingReason, "quarantined"; violatingShacl, "quarantined" ]
    printfn "F# sift doctor (ARC-ADR-033) -- parity with the Python reference"
    printfn "%s" (String.replicate 66 "-")
    let mutable allPass = true
    for f, expected in cases do
        let pass, summary, violations = outcomeLine f expected
        allPass <- allPass && pass
        printfn "[%s] %-28s %s" (if pass then "PASS" else "FAIL") f.FragmentId summary
        for v in violations do
            printfn "        - %A: %s" v.Level v.Detail
    printfn "%s" (String.replicate 66 "-")
    match sift conformant with
    | Snapped triples -> printfn "\ncanonical projection of %s (the functor's output):\n\n%s" conformant.FragmentId (toTurtle triples)
    | Quarantined _ -> ()
    if allPass then
        printfn "ALL PASS -- the F# core snaps the proven and quarantines the rest (parity)."
        0
    else
        eprintfn "PARITY FAILURE -- F# outcome diverged from the expected sift result."
        1
