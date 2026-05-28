// spikes/ir-to-shacl.fsx — F# on a REAL surface: project an OntoUML IR model into
// SHACL shapes (one of the north-star's projections). Every stereotype MUST yield
// a shape rule — FS0025 means you cannot add a stereotype and silently emit an
// unconstrained class. Run:  dotnet fsi ir-to-shacl.fsx   (emits Turtle to stdout)

type Stereotype =
    | Kind | SubKind | Role | Phase | Category | Mixin
    | Relator | Quality | Mode | Event | Situation

type RoleDef = { Name: string; Filler: string }
type EntityDef = { Id: string; Stereotype: Stereotype; Roles: RoleDef list }
type Model = { Ns: string; Entities: EntityDef list }

/// The projection: stereotype -> the SHACL constraint lines for a class of that
/// stereotype. TOTAL over Stereotype — add a case to the union above and this
/// will not compile until you decide its shape. That is the guarantee.
let private constraintsFor (e: EntityDef) : string list =
    match e.Stereotype with
    | Relator ->
        let roleProps =
            e.Roles
            |> List.map (fun r ->
                sprintf "    sh:property [ sh:path model:%s ; sh:minCount 1 ; sh:maxCount 1 ] ;" r.Name)
        [ "    sh:property [ sh:path gufo:mediates ; sh:minCount 2 ;"
          "        sh:message \"a relator must mediate at least two distinct participants\" ] ;" ]
        @ roleProps
    | Role ->
        [ "    sh:property [ sh:path gufo:inheresIn ; sh:minCount 1 ;"
          "        sh:message \"a role must inhere in an independent continuant\" ] ;" ]
    | Phase ->
        [ "    sh:property [ sh:path gufo:isPhaseOf ; sh:minCount 1 ;"
          "        sh:message \"a phase partitions the kind it depends on\" ] ;" ]
    | Quality | Mode ->
        [ "    sh:property [ sh:path gufo:inheresIn ; sh:minCount 1 ] ;" ]
    | Kind | SubKind ->
        [ "    # sortal: supplies or inherits a principle of identity (no extra cardinality)" ]
    | Category | Mixin ->
        [ "    # non-sortal: abstract dispersive type, no direct instances expected" ]
    | Event | Situation ->
        [ "    # perdurant: occurs in time (temporal constraints projected separately)" ]

let shapeFor (e: EntityDef) : string =
    let body = constraintsFor e |> String.concat "\n"
    sprintf "model:%sShape a sh:NodeShape ;\n    sh:targetClass model:%s ;\n%s\n    .\n" e.Id e.Id body

let emitShacl (m: Model) : string =
    let header =
        [ "@prefix sh:    <http://www.w3.org/ns/shacl#> ."
          "@prefix gufo:  <http://purl.org/nemo/gufo#> ."
          sprintf "@prefix model: <%s> ." m.Ns ]
        |> String.concat "\n"
    header + "\n\n" + (m.Entities |> List.map shapeFor |> String.concat "\n")

// A tiny model — the risk/control domain from the thin slice.
let demo =
    { Ns = "https://agentarmy.dev/ontology-sift/model#"
      Entities =
        [ { Id = "Risk"; Stereotype = Kind; Roles = [] }
          { Id = "Control"; Stereotype = Kind; Roles = [] }
          { Id = "RiskOwner"; Stereotype = Role; Roles = [] }
          { Id = "MitigationCase"; Stereotype = Relator
            Roles = [ { Name = "mitigatedRisk"; Filler = "Risk" }
                      { Name = "mitigatingControl"; Filler = "Control" } ] } ] }

printfn "%s" (emitShacl demo)
