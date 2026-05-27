# Data Vault ↔ Ontology Bridge

> **Status:** Strategic guidance from `data-vault-architect`. Anchors: [`strategy.md`](strategy.md) (DV 2.1), [`ARC-ADR-016`](../decisions/ARC-ADR-016-ontology-representation-reification-hyperedges.md) (reification + hyperedges), the [Knowledge & Ontology cluster](../../.claude/agents/categories/12-knowledge-ontology/README.md) (UFO primary, BFO interop).
>
> **Scope:** when does a DV construct correspond to a UFO/BFO construct, and when don't they? Mapping rules and worked examples — *not* schemas, *not* SQL, *not* a re-definition of stereotypes.

## 1. Why this note exists

The Data Vault layer and the ontology layer are two **separate disciplines that meet at the same world**. They are not isomorphic, and treating them as if they were is the fastest way to break both:

- **Data Vault** is a *warehousing* methodology. Its constructs (hub, link, sat) are optimized for **integration + history + auditability + parallel load**. The vault models *what sources asserted, and when*.
- **UFO/OntoUML** (primary authoring) and **BFO/CCO** (realist interop projection) are *foundational ontologies*. Their constructs (kind, role, relator, mode, quality; continuant, occurrent, disposition) are optimized for **truth conditions + identity + dependence + reasoning**. The ontology models *what is the case in the world*.

A hub is not a kind. A link is not a relator. A satellite is not a mode. **Sometimes they align cleanly; sometimes they diverge; the architect's job is to know which.**

This note is the decision rule. Modelers and ontologists use it as input; they do not derive their own work from it.

## 2. The fundamental gap

| Concern | Data Vault answers | UFO/BFO answers |
|---|---|---|
| What is this thing? | "A row keyed by `<entity>_hk` extracted from `record_source`" | "An instance of stereotype X with identity criterion Y" |
| When does it exist? | `load_date` — when it entered the warehouse | `valid_from`/`valid_to` over the real world; for BFO occurrents, the process's temporal region |
| When does it change? | New `hash_diff` ⇒ new sat row | Phase transition, role change, qualitative change of a `mode`/`quality` |
| Identity | Hash of the source's business key (per source, or post-resolution) | Provided by a `kind` (UFO) or by BFO's continuant/occurrent commitments |
| Multiplicity of "the same thing" | Multiple raw hubs + a business-vault same-as link | One entity with multiple `record_source` provenance assertions |
| n-ary relations | Link table with N parent hubs | Reified **relator** (UFO) / process or realizable entity (BFO) — see ARC-ADR-016 |
| Truth | "The source said this on `load_date`" | "This holds in the world during the valid interval" |

The mismatch is intentional. The vault is an **audit trail of assertions**. The ontology is a **theory of what those assertions are about**. They speak past each other if you force one onto the other.

## 3. Mapping rules

### 3.1 Hub ↔ UFO kind

| DV hub corresponds to a UFO kind when… | A hub does NOT correspond to a kind when… |
|---|---|
| The hub represents a **rigid, sortal** business entity (Customer, Product, Order, Patient) with a stable identity criterion | The hub represents a **role** (Reviewer, Borrower, Buyer) — these are anti-rigid; the underlying kind is Person/Organization |
| The business key really is the identity of the kind's instance in the source | The hub represents a **phase** of another entity (ActiveCustomer, ChurnedCustomer) — that's a phase, not a kind |
| Identity persists across sat changes (the entity is the same after a name change) | The hub conflates several kinds under one source label (a `hub_party` that mixes Person and Organization is a `«category»` or `«roleMixin»` — not a kind) |
| Cross-source identity is achieved (post same-as resolution) | Identity is fundamentally source-relative (`hub_customer_crm` and `hub_customer_billing` are **per-source identity anchors**, not the kind itself — the kind sits behind the same-as link) |

**Decision rule:** a raw vault hub is a **source-side identity anchor**. Whether that anchor *also* corresponds to a UFO kind is decided by the ontologist, not the modeler. The architect's call is whether to **resolve identity** (creating a business-vault same-as link that points at the kind-level identity) or **leave the per-source anchors as is** when no kind-level claim is being made.

### 3.2 Link ↔ UFO relator vs "just an association"

This is the highest-leverage decision in the bridge.

| A DV link rises to a UFO relator when… | A DV link is "just an association" when… |
|---|---|
| The relationship has its **own identity and lifecycle** (an Enrollment, a Marriage, an Employment, an Order itself) | The relationship is a pure formal/structural link (`lnk_product_category`, `lnk_order_customer` where the order *is* the relator — see below) |
| It mediates **3+ participants** as one semantic unit (source + chunks + exercise + evidence) | It is genuinely binary and has no whole-relation metadata |
| It carries **whole-relation metadata** beyond audit (confidence, role, qualifier, status) | The only metadata is `load_date` + `record_source` |
| It participates further (a Decision links a Mandate that links a Mitigation — statements-about-statements) | Nothing else points at the relationship itself |
| It corresponds to an **endurant** mediating typed roles (the UFO definition of a relator) | The "relationship" is just navigation — a foreign-key pointer in disguise |

**The ARC-ADR-016 angle (load-bearing):** DV link tables are **already a form of reification**. They take what could be a column-level FK and promote the relationship to a row-level object with its own `_hk`, its own `load_date`, and (potentially) its own satellites. That is structurally what ARC-ADR-016's "relator-vertex + typed role-binding" pattern does, just in tabular form.

What this means in practice:

- A DV link with **its own satellites** carrying whole-relation attributes (e.g. `sat_enrollment_status_bv`) is **operationally a relator already** — the IKW-GraphEngine projection should treat it as a `RelatorVertex`, not as a binary edge with edge properties.
- A DV link with **no satellites and no metadata beyond audit** is a candidate for the "degenerate 2-role relator" treatment in ADR-016 — projected as a binary edge, additively upgradable to a full relator if metadata appears.
- An n-ary link (3+ parent `_hk` columns) is **definitely** a relator in the projection; resist any urge to decompose it into binary links just because graph DBs prefer binary edges. ADR-016 is explicit: that decomposition loses the n-ary identity.

**Reify judiciously (D8 from ADR-016) applies here too.** Don't promote a `lnk_product_category` to a UFO relator just because you can. Formal relations (parthood, classification, subset) are *not* relators.

### 3.3 Satellite ↔ UFO mode / quality / phase

Satellites are descriptive context. UFO carves "description" into three categories:

| UFO category | What it is | DV satellite shape |
|---|---|---|
| **`«quality»`** | Intrinsic measurable feature (height, weight, color) inhering in its bearer | A sat attribute that is a directly observed measurement; `hash_diff` changes when the measured value changes |
| **`«mode»`** | Intrinsic non-measurable feature (a belief, a skill, a symptom) | A sat attribute that is descriptive but not on a quality dimension; often source-asserted |
| **`«phase»`** | A stage of an entity's lifecycle (ActiveCustomer, ChurnedCustomer) characterized by intrinsic conditions | **NOT a sat attribute.** A phase change is an entity-level state transition — model it as a phase-indicating attribute on a sat, with the **phase itself** being an ontology concern; or, when phase is the *only* thing that changes and it has its own attributes, consider an effectivity sat or a dedicated phase-sat |

**Decision rule:** the architect decides *which sat carries which attribute group* (by source, by PII classification, by change cadence). The ontologist decides *what stereotype each attribute carries*. These are independent dimensions. A single `sat_customer_crm` row can carry one quality (height), three modes (preferences), and one phase indicator without the sat needing to "be" any one of those things.

**Anti-pattern:** a satellite per stereotype. Do not split `sat_customer_qualities`, `sat_customer_modes`, `sat_customer_phases`. The sat split axis is **source + sensitivity + change cadence**, not ontological category. The ontology layer reads across the sats; it does not dictate their partitioning.

### 3.4 The reification angle (ARC-ADR-016 explicit)

DV link tables are *already* reified n-ary relations. State this plainly because it has consequences:

1. **For the IKW-GraphEngine graph projection** (strategy §2.3, patterns §15): when projecting a DV link to the graph, the link is a **`RelatorVertex` candidate**, not a binary edge by default. The architect's call per link: degenerate 2-role (project as edge) vs full relator (project as vertex + role-binding edges). ADR-016 makes this additive — degenerate first, upgrade on need.
2. **For the ontology**: a DV link with satellites is essentially the warehouse's pre-existing answer to "where does whole-relation metadata live?" — it lives on the link's satellites. When the ontologist asks "is there a relator here?", the existence of `sat_<link>_*` is strong evidence the team already treated this relationship as having its own identity.
3. **For modelers**: do not invent a `hub_<relationship>` to hold relationship metadata. The DV idiom is `lnk_X_Y` + `sat_lnk_X_Y_*`. A hub-for-a-relationship is a category error and breaks the projection.
4. **Bitemporal placement**: ADR-016 puts bitemporal + PROV on the *relator vertex*. In DV terms, that is **on the link** (and its satellites), not on the participant hubs. This aligns; the bridge here is one-to-one.

### 3.5 BFO projection: continuant vs occurrent for a hub

In the dual-foundation design (UFO authored, BFO projected), every hub gets asked: **continuant or occurrent?**

| Hub looks like a BFO continuant when… | Hub looks like a BFO occurrent when… |
|---|---|
| The entity **persists through time** with identity, gaining/losing attributes (Customer, Patient, Asset, Document) | The entity **unfolds in time** as a process or event (Order, Visit, Treatment-Episode, Build, Session) |
| Sats track **changing descriptive context of the persisting thing** | Sats track **the structure/outcome of the process itself** |
| The hub is the bearer of qualities | The hub is what bears a temporal region as its existence |

The split matters because BFO's relations differ across the continuant/occurrent boundary (time-indexed relations on continuants; ordinary relations on occurrents and across categories). The IKW-GraphEngine BFO sidecar needs the classification correct or its reasoner will be wrong.

**Ambiguity case:** `hub_order`. Is an Order a continuant (a persistent business object that goes through phases) or an occurrent (a process from placement to fulfilment)? Both readings exist; UFO would call it a relator between Customer and Product. **This is a coordination call between `ontologist-ufo` and `ontologist-bfo` — not the architect's, and not the modeler's.** The architect's contribution is to ensure the DV shape (a `lnk_customer_product` with order attributes on its sat) doesn't pre-empt the answer. The vault can serve either projection.

## 4. Worked example A — clean alignment (Customer)

**The DV picture:**

- `hub_customer_crm` (raw, source = CRM)
- `hub_customer_billing` (raw, source = billing)
- `lnk_same_as_customer_bv` (business vault; identity resolver `v1`)
- `sat_customer_crm` (name, email, phone)
- `sat_customer_crm_pii` (separate ACL)
- `sat_customer_billing` (billing address, payment method)
- `sat_customer_metrics_bv` (lifetime value, order count — computed, business rules `v1`)

**The UFO picture:**

- `Customer` is a **`«kind»`** — rigid, sortal, identity criterion = person-or-org-as-counterparty.
- `LifetimeValueScore` could be a **`«quality»`** (it has a value dimension) on the Customer.
- `PreferredChannel` could be a **`«mode»`** (intrinsic, non-measurable preference).
- `ActiveCustomer`/`DormantCustomer` are **`«phase»`s** distinguished by recent-activity predicates.

**The BFO picture:**

- `Customer` projects to a BFO **independent continuant** (most naturally a specifically dependent continuant *bearer*).
- Qualities project as `quality` (BFO 2020 IRI in PATO-like style).
- Phases project as BFO **roles** or **realizable entities** that the continuant bears.

**Why this aligns cleanly:**
- One UFO kind ↔ one logical entity ↔ two source-side hubs unified by a same-as link. The kind sits *behind* the same-as link, not on either raw hub.
- The sat split (source + PII) is orthogonal to the stereotype assignment. Attributes carry stereotypes; sats don't.
- The computed sat (`sat_customer_metrics_bv`) supplies values that, in the ontology layer, are qualities/modes of the kind. The vault computes them; the ontology types them.
- The graph projection is straightforward: Customer as a node, with the same-as link materialized as the canonical-identity edge to the per-source anchor nodes (or the per-source anchors elided in favor of the resolved identity).

**What the architect does:** confirms the same-as link belongs in business vault, picks the identity resolution method (here: normalized email), versions it (`identity-resolver-v1` in `record_source`), and *stops*. The kind/quality/mode assignments are the ontologist's call.

## 5. Worked example B — divergence (Evidence / Ingest-Evidence)

**The DV picture:**

- `hub_source` (a publication, document, transcript)
- `hub_chunk` (a sub-unit of the source)
- `hub_exercise` (the analytical exercise that produced an evidence claim)
- `hub_evidence_claim`
- `lnk_evidence_ingest` — joining **source + chunk + exercise + evidence_claim** (n-ary, 4 parents)
- `sat_lnk_evidence_ingest` — confidence score, extraction method, model version, reviewer

**The UFO picture:**

- This is **not** "an evidence with some columns." It is a **`«relator»`** — an Ingest-Evidence relator mediating four roles: `originating_source`, `supporting_chunk`, `produced_by_exercise`, `asserts_claim`.
- The relator has its own identity (this specific evidence event), its own lifecycle (created → reviewed → superseded), and is **referenced by further relations** (a Decision relator that points at multiple Ingest-Evidence relators).

**The BFO picture:**

- The Ingest-Evidence relator projects to a BFO **process** (an occurrent) — the act of evidence ingestion that unfolded in time.
- Alternatively, in a more conservative reading, it projects to a BFO **information artifact** (an IAO information content entity) that *represents* an evidence claim. The choice is a coordination call between `ontologist-ufo` and `ontologist-bfo`.
- Either way, the binary-edge projection would *lose the n-ary identity* — exactly the problem ARC-ADR-016 was raised to solve.

**Where DV and UFO/BFO diverge — and what to do:**

| The divergence | Resolution |
|---|---|
| DV's natural instinct is to flatten the relationship into FK columns or pairwise binary links. **Don't.** Keep the link n-ary | Architect ratifies the n-ary link; modeler designs the 4-parent link + sat; ADR-016's projection rules govern the graph shape |
| DV's `record_source` says "ingest-pipeline-v1" — that's an audit fact, not a UFO/BFO category | Both are correct in their own frame. The vault row is provenance; the ontology row is the relator. They co-exist; neither replaces the other |
| The graph projection: binary edge or relator vertex? | **Relator vertex with role-binding edges** (ADR-016 Option 1). The 2-role degenerate shortcut does not apply at n=4 |
| Statements about this evidence (e.g. a Decision that cites it) | Use the ADR-016 "relator-references-relator" pattern. In DV, that means another link whose parents include `evidence_ingest_hk` — which is structurally a hub-key-of-a-link. Document this clearly; it is the bridge's most counter-intuitive shape |

**What the architect does:** ratifies that this is n-ary (not a chain of binaries), confirms the placement (raw vault for the ingest event, business vault for any derived confidence aggregates), and *defers* the question "is this a process or an information artifact?" to the ontologists. See §8.

## 6. Quick-reference table

| DV construct | Default ontology read | When it diverges |
|---|---|---|
| **Raw hub** | Source-side identity anchor for a UFO kind | Hub is per-source — the kind sits behind the same-as link in business vault |
| **Business-vault hub** (rare) | Synthetic identity for a kind that has no single-source anchor | Often this is better as a same-as link than a new hub — challenge it |
| **Link (binary, no sats)** | Degenerate 2-role relator (per ADR-016) — projects as binary edge | If metadata appears, upgrade to full relator vertex (additive) |
| **Link (binary, with sats)** | Full UFO relator (has whole-relation metadata + lifecycle) | Project as `RelatorVertex` in the graph; bitemporal lives on the relator |
| **Link (n-ary, 3+ parents)** | Full UFO relator, definitionally | Never decompose to binaries; project as `RelatorVertex` + role-binding edges |
| **Standard satellite** | A bundle of attributes whose stereotypes vary (quality / mode / phase indicator) — the sat is not "an X" | Split sats by source + PII + cadence; **not** by stereotype |
| **Multi-active sat** | Multi-valued quality/mode (e.g. multiple email addresses) | If the multiple values are themselves identifiable entities, it's a child hub + link, not multi-active |
| **Effectivity sat (on a link)** | Temporal validity of the relator | Lives in business vault; aligns with ADR-016's bitemporal placement on the relator |
| **PIT table** | Pure performance artifact; no ontology counterpart | None — purely warehouse |
| **Bridge table** | Pure performance artifact; no ontology counterpart | None — purely warehouse |
| **Same-as link** | The bridge from per-source hubs to a single ontology-level kind identity | Versioned in `record_source` so a rule change is a new resolution generation, not a mutation |
| **Reference table** | A controlled vocabulary; lives in the `taxonomist`'s lane (SKOS) before any ontology lift | If the reference becomes axiomatized, it graduates to an enumeration in the ontology |

## 7. What the architect produces vs what is out of lane

| Architect produces | Architect does NOT produce |
|---|---|
| This mapping table | Specific hub/link/sat designs (→ `data-vault-modeler`) |
| The decision "this link is n-ary, keep it n-ary" | The link's DDL or load logic (→ `data-vault-engineer`) |
| The decision "resolve identity in business vault, version the rule" | Stereotype assignments per attribute (→ `ontologist-ufo`) |
| The decision "this divergence warrants a Decision Artifact" | BFO classification per hub (→ `ontologist-bfo`) |
| The decision "the graph projection treats this link as a relator vertex" | The Cypher/SQL that does the projection (→ `data-vault-engineer` + `knowledge-engineer`) |

## 8. Escalations / decisions deliberately punted

These are **cross-disciplinary judgment calls** that this note does *not* resolve. Each is a candidate for a Decision Artifact (`hitl-decision` label) if it comes up in real work:

1. **Order as continuant vs occurrent vs relator (BFO + UFO coordination).** The dual projection needs ontologist-ufo and ontologist-bfo to coordinate; the architect's role is to ensure the DV shape (link + sat) doesn't pre-empt either projection.
2. **Where does identity resolution truly live — in the vault (same-as link) or in the ontology (a single kind with multiple `record_source`-provenance attributes)?** The current strategy puts it in the vault (business-vault same-as link). The ontology-grade-persistence track (RT5) may push some of it ontology-side. This is a real architecture decision and probably warrants its own ADR when the ontology pipeline lands in production.
3. **Ingest-Evidence projection: process (BFO occurrent) vs information artifact (IAO/CCO)?** A coordination call between the two ontologists; the architect ratifies the DV n-ary link shape regardless of which way they go.
4. **Should reference tables (controlled vocabularies) live in the vault, in SKOS via the taxonomist, or in both?** Today the strategy places them in the vault (`ref_*`). A SKOS-first approach would invert this. Defer until the taxonomist track is staffed.
5. **Phase modeling — sat attribute vs effectivity sat vs separate phase-sat.** The architect's default is "phase indicator on a normal sat"; the modeler will sometimes want a dedicated effectivity-style construct. Coordinate with `ontologist-ufo` when this comes up.

## 9. Where the existing `strategy.md` now reads slightly wrong

Applying this bridge to the strategy doc as written surfaces two passages that should be tightened in a follow-up edit (not done here — that's a separate doc-edit task and would risk scope creep):

1. **§2.3 "Information Marts" — graph projection.** Currently says "Hubs → nodes, links → edges." After ARC-ADR-016 this is **only true for degenerate 2-role relators**. The accurate statement is: *hubs → vertices; binary links with no whole-relation metadata → edges; binary links with sats and n-ary links → relator vertices with typed role-binding edges (per ARC-ADR-016).* The current wording will mislead modelers into decomposing n-ary links.
2. **§6.5 "Right-to-be-forgotten — tombstone link."** Phrased as a vault-internal mechanism. In the ontology-grade-persistence world, suppression *also* needs to propagate to the BFO/CCO sidecar's exported triples — the vault tombstone is necessary but not sufficient. Worth a sentence acknowledging that downstream ontology consumers need their own suppression contract.

Both are tractable edits; neither is wrong enough to block the current PR.

## 10. References

- [DV 2.1 Strategy](strategy.md) — anchor doc (especially §2 layers, §3 hash strategy).
- [DV Patterns](patterns.md) — especially §15 (graph projection).
- [DV Glossary](glossary.md).
- [`ARC-ADR-016`](../decisions/ARC-ADR-016-ontology-representation-reification-hyperedges.md) — reification + hyperedges; the load-bearing connection for §3.4.
- [Knowledge & Ontology cluster README](../../.claude/agents/categories/12-knowledge-ontology/README.md) — formality gradient, dual projection.
- [`ontologist-ufo`](../../.claude/agents/categories/12-knowledge-ontology/ontologist-ufo.md), [`ontologist-bfo`](../../.claude/agents/categories/12-knowledge-ontology/ontologist-bfo.md) — the stereotype/category vocabulary this note treats as input.
- [`ARC-ADR-009`](../decisions/ARC-ADR-009-canonical-data-model-arrow.md) — the canonical model contract the vault implements.
