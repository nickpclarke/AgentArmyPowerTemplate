# OntoUML Profile — every stereotype with constraints

OntoUML is a UML class-diagram profile. Classes get **class stereotypes** (the type's ontological category); associations get **relation stereotypes**. This is the full vocabulary plus the constraints a reasoner/validator enforces.

## Class stereotypes — object (substantial) types

| Stereotype | Sortal? | Rigidity | Identity | Use for | Example |
|---|---|---|---|---|---|
| **«kind»** | sortal | rigid | **provides** | functional-complex objects (the default object kind) | Person, Car, Organization |
| **«collective»** | sortal | rigid | provides | collections with uniform structure | Forest, Committee, Deck |
| **«quantity»** | sortal | rigid | provides | amounts of matter | Water, Gold, Sand |
| **«subkind»** | sortal | rigid | **inherits** | rigid specialization of a kind | Man/Woman (of Person), SUV (of Car) |
| **«phase»** | sortal | anti-rigid | inherits | contingent specialization by **intrinsic** change; in partitions | Child/Adult, Available/Busy |
| **«role»** | sortal | anti-rigid | inherits | contingent specialization by **relational** participation | Student, Husband, Employee |

**Constraints:**
- Every «kind»/«collective»/«quantity» is an **ultimate sortal**; every object instance instantiates exactly one. A sortal hierarchy must have a unique ultimate kind at the top.
- «subkind», «phase», «role» **must** ultimately specialize a single kind (they inherit its identity).
- «phase» appears in **phase partitions** ({…} disjoint + complete over the supertype).
- «role» **must** be connected (directly or transitively) to a «relator» via «mediation» — a role without a relator is the *FreeRole* anti-pattern.
- A rigid type (kind/subkind/category) must **not** specialize an anti-rigid type (phase/role/mixin).

## Class stereotypes — non-sortal (mixin) types

| Stereotype | Rigidity | Use for | Example |
|---|---|---|---|
| **«category»** | rigid | rigid properties common to **multiple kinds** | PhysicalObject, RationalEntity |
| **«roleMixin»** | anti-rigid | a **role** spanning multiple kinds (relational) | Customer (Person *or* Organization), Insured |
| **«phaseMixin»** | anti-rigid | a **phase** spanning multiple kinds (intrinsic) | Living (of Person *or* Animal *or* Plant) |
| **«mixin»** | semi-rigid | properties rigid for some instances, anti-rigid for others | Seatable (rigid for Chair, contingent for Rock) |

**Constraints:**
- Non-sortals **cannot** be directly instantiated and **cannot** provide identity; their instances always also instantiate some kind.
- A non-sortal must generalize types of **≥2 different kinds** (else it should be a sortal). Violating this is the *MixinIdentity*/over-use smell.
- Non-sortals should be **abstract** (no direct instances).

## Class stereotypes — aspects (moments) and dynamics

| Stereotype | Category | Use for | Example |
|---|---|---|---|
| **«relator»** | relational moment | reified n-ary relationship; truthmaker of a material relation | Marriage, Enrollment, Employment, MitigationCase |
| **«mode»** | intrinsic moment | complex aspect that may bear its own qualities | Skill, Belief, Intention, Symptom |
| **«quality»** | intrinsic moment | aspect with a value in a quality space | Color, Weight, Temperature |
| **«event»** | perdurant | something that happened (immutable, has temporal parts) | Marriage Ceremony, Purchase, Ingest Run |
| **«situation»** | state of affairs | a snapshot of reality that can activate dispositions / trigger events | "patient is feverish", "account overdrawn" |
| **«type»** | high-order type | a type whose instances are types (powertype) | CarModel (instances are types of Car) |
| **«datatype»** | value type | structured values, no identity | Date, MonetaryValue, GeoCoordinate |
| **«enumeration»** | value type | enumerated literals | SeverityLevel {Low, Med, High} |

## Relation stereotypes

### Existential-dependency relations (moment ↔ bearer)
| Stereotype | Connects | Meaning |
|---|---|---|
| **«mediation»** | «relator» → participant | the relator existentially depends on each mediated participant (this is how a relator binds its roles). |
| **«characterization»** | «mode»/«quality» → bearer | the moment inheres in / characterizes its bearer. |
| **«derivation»** | «material» relation → «relator» | the material relation is derived from (made true by) the relator. |

### Material vs formal relations
| Stereotype | Meaning | Example |
|---|---|---|
| **«material»** | a relation **founded on a relator** (has relational moments); always derived from a «relator» | "is enrolled at", "is married to" |
| **«formal»** | a direct relation holding **without** a mediating relator (comparative, mathematical, mereological-formal) | "taller than", "older than", "subset of" |

### Parthood relations (mereology, by whole/part kind)
| Stereotype | Whole / Part | Meaning |
|---|---|---|
| **«componentOf»** | functional complex / functional complex | a part with a function in a complex (Engine componentOf Car) |
| **«memberOf»** | collective / member | membership in a collective (Tree memberOf Forest) |
| **«subCollectionOf»** | collective / sub-collective | a sub-collection (Defense subCollectionOf Team) |
| **«subQuantityOf»** | quantity / portion | a portion of an amount of matter (Alcohol subQuantityOf Wine) |
| **«containment»** | (spatial) | non-functional spatial containment |

Parthood meta-properties to set: **shareability** (can a part belong to >1 whole?), **essentiality** (is the part essential to the whole's identity?), **inseparability** (is the whole essential to the part?), and **immutability** of parts.

### Dynamic / event relations (UFO-B)
| Stereotype | Connects | Meaning |
|---|---|---|
| **«participation»** | endurant → «event» | an endurant participates in an event. |
| **«manifestation»** | «mode»/disposition → «event» | a disposition is manifested in an event. |
| **«bringsAbout» / «triggers»** | «event» → «situation» / «situation» → «event» | causation between events and the situations they create/are triggered by. |
| **«creation» / «termination»** | «event» → endurant | the event that creates/ends an endurant. |
| **«historicalDependence»** | endurant → endurant/event | dependence on a past event/entity. |

## Cardinality & role-binding discipline

- Set cardinalities on **«mediation»** ends to express how many participants each role binds (1..1, 1..*, etc.).
- Keep **role types disjoint** across a relator's mediations — overlapping role-type extensions cause **RelOver** (ambiguous which role an individual fills). See anti-patterns reference.
- A relator binding *n* participants → *n* «mediation» links. In the AgentArmy IR this is exactly the `relators:` block with typed `roles:`; in ArcadeDB it is the relator vertex + *n* `BINDS_ROLE` edges.

## Minimal worked diagram (textual)

```
«kind» Person
«kind» School
«role» Student  ──(specializes)──▶ Person
«relator» Enrollment
   «mediation» enrolledStudent  Enrollment ─▶ Student   [1..*]
   «mediation» enrollingSchool  Enrollment ─▶ School    [1..1]
«material» isEnrolledAt  Student ─▶ School   «derivation»▶ Enrollment
«quality» GPA  ──«characterization»──▶ Student
```
Reads: a Person *contingently* becomes a Student by participating in an Enrollment relator that mediates one School; "isEnrolledAt" is the material relation derived from Enrollment; GPA is an intrinsic quality of the Student.
