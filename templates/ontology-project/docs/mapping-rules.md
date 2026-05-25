# Mapping rules & divergence list — UFO → BFO/CCO

Ships with every BFO/CCO projection (the pipeline's "documented mapping, not lossless round-trip" rule). This is the per-element record for `model/model.yaml`. General theory: see the `ufo-ontology` and `bfo-ontology` skills (`UFO_BFO_MAPPING.md`).

## Element-by-element

| IR element | Stereotype | gUFO | BFO/CCO target | Fidelity | Note |
|---|---|---|---|---|---|
| `Person` | kind | gufo:Kind / gufo:Object | `cco:Person` ⊑ obo:BFO_0000030 (object) | high | clean. |
| `Control` | kind | gufo:Kind | `obo:BFO_0000031` (GDC, a specified measure) *or* `cco:Act` | medium | depends on whether "control" means the plan (GDC) or the activity (process). Chose GDC; revisit if controls are modeled as running processes. |
| `EvidenceBundle` | kind | gufo:Kind | `obo:IAO_0000030` (information content entity, GDC) | high | informational → GDC, not a quality. |
| `RiskOwner` | role | gufo:Role ⊑ ex:Person | `obo:BFO_0000023` (role) **borne by** Person via `obo:RO_0000052` (inheres in) | medium | **placement restructures**: UFO role-as-type → BFO role-as-borne-entity. The instance changes from "a Person who is a RiskOwner" to "a Person bearing a RiskOwnerRole". |
| `RiskSeverity` | quality | gufo:QualityType | `obo:BFO_0000019` (quality) | high | values in SeverityLevel ↔ a quality space (PATO-style). |
| `Risk` | kind | gufo:Kind | `obo:BFO_0000016` (disposition) | **low — DIVERGENCE** | "Risk" has no agreed BFO home. Modeled as a disposition borne by the at-risk entity; could alternatively be a role or an SDC bundle. Flagged. |
| `mitigation-case` | relator | gufo:RelatorType / gufo:Relator | **no single counterpart** → `bfo_pattern: interdependent-roles`: an `ex:MitigationProcess` ⊑ obo:BFO_0000015 (process) that `realizes` (obo:BFO_0000055) a bundle of roles inhering in the participants and `has participant` (obo:RO_0000057) each bearer | **low — DIVERGENCE** | the single UFO relator fans out into process + roles. |
| `SeverityLevel` / `LikelihoodLevel` | enumeration | value partition | `rdfs:Datatype` / SKOS scheme | n/a | data-level; a `taxonomist` may own these as a controlled vocabulary. |

## Divergence list (must read before trusting the BFO projection)

1. **`mitigation-case` (relator) has no single BFO category.** Chosen pattern: `interdependent-roles` (process realizing roles). The reciprocal commitments/claims (UFO-C) are not separately represented.
2. **`Risk` placement is contested.** Projected as a disposition; if your domain treats risk as a relational/contextual standing, switch to a role-bundle. Do not assume the BFO `Risk` and UFO `Risk` instances line up 1:1.
3. **`RiskOwner` restructures the instance graph** (type → borne role).
4. **Modal meta-properties are lost**: `rigidity: anti-rigid` on `RiskOwner` and identity meta-kinds on the kinds have no BFO representation — they remain only in the IR.
5. **BFO-only structure not present in the source**: spatial/temporal/spatiotemporal regions, fiat boundaries, GDC/SDC concretization — added in projection if needed, never derived from the UFO model.

## Persistence note

Regardless of upper ontology, `mitigation-case` persists as **one relator vertex + four `BINDS_ROLE` edges** (see `../persistence/arcadedb-schema.sql`). The mapping above only changes the *labels/axioms* attached in each `semantic/` projection, not the physical graph.
