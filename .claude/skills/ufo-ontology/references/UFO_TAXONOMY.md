# UFO — Taxonomy and Theory (UFO-A / UFO-B / UFO-C)

UFO is layered. Know which layer you are in: most structural modeling is **UFO-A** (endurants); dynamics are **UFO-B** (events); social/intentional reality is **UFO-C**.

## The three layers

| Layer | Domain | Key categories |
|---|---|---|
| **UFO-A** | Endurants (objects & their aspects) — structural conceptual modeling | Substantial, Moment (Quality/Mode/Relator), the type taxonomy (Kind/Role/Phase/…), rigidity, sortality, identity |
| **UFO-B** | Perdurants (events, processes), causation, temporal structure | Event, situation, participation, causation, temporal ordering, dispositions manifested in events |
| **UFO-C** | Social & intentional entities (built on A + B) | Agent, Object (non-agentive), social role, social relator, commitment, claim, goal, intention, belief, normative description, social object |

## The top split: Individuals vs Types

- **Individual** (particular) — a single thing (this person, this marriage, this run).
- **Type / Universal** — a repeatable pattern individuals instantiate. UFO's type taxonomy classifies *types* by their meta-properties (the OntoUML stereotypes are types of types).

## Endurant vs Perdurant

- **Endurant** — persists in time, wholly present at each moment, can change (≈ BFO continuant). Subdivides into **Substantials** and **Moments**.
- **Perdurant / Event** — happens in time, has temporal parts (≈ BFO occurrent). Events are *immutable* once they occur.

### Substantials vs Moments
- **Substantial** — an **existentially independent** endurant (a person, a car, an organization). The bearer.
- **Moment** (aspect / trope) — an **existentially dependent** endurant; it can only exist *in* something else:
  - **Intrinsic moment** — depends on a single bearer:
    - **Quality** — has a value in a **quality structure / quality space** (Gärdenfors conceptual spaces): a color, a weight, a temperature. The value is a *quale* in the space.
    - **Mode** — a more complex aspect that may itself bear qualities and need not have a single value space: a skill, a belief, a symptom, an intention, an electric charge.
  - **Relational moment / Relator** — depends on **several** bearers at once; it **mediates** them and is the **truthmaker** of a material relation (a marriage, an enrollment, a contract, an employment).

## Identity meta-kinds (which *kind of* identity a sortal supplies)

Every substantial instantiates exactly one **ultimate sortal** that supplies its **principle of identity**. There are three identity meta-kinds, giving three "kind-level" stereotypes:

| Identity meta-kind | Stereotype | Identity criterion | Examples |
|---|---|---|---|
| **Functional complex** | «kind» | parts arranged for a function; identity survives part replacement within limits | Person, Car, Organization, Heart |
| **Collective** | «collective» | a collection with uniform structure; identity tied to membership | Forest, Deck of cards, Committee, Crowd |
| **Quantity** | «quantity» | an amount of matter; maximally-connected portion of stuff | Water, Gold, Wine, Sand (as stuff) |

A substantial gets its identity from **one** of these and keeps it for life (rigidity of the kind).

## Rigidity (the modal backbone)

Rigidity is about identity across **possible worlds** (modal necessity), not just across time:

- **Rigid (R)** — applies to every instance in *every world* in which the instance exists. If `x` is a Person, `x` is a Person in every world it exists; losing Person-hood means `x` ceases to be. Kinds, subkinds, categories are rigid.
- **Anti-rigid (~R)** — applies to its instances only *contingently*: there is some world where the very same instance exists but is **not** of that type. Student, Child, Customer — a person can stop being a student and still exist. Phases, roles, roleMixins, phaseMixins are anti-rigid.
- **Semi-rigid** — rigid for some instances, anti-rigid for others. Mixins are semi-rigid.

**Why it matters:** a rigid type must never specialize an anti-rigid type (a rigid thing can't depend on a contingent condition for its identity). This is a core OntoUML constraint and the basis of several anti-patterns.

## Sortality (the identity backbone)

- **Sortal** — carries/inherits a single principle of identity; you can count its instances. Kinds, subkinds, phases, roles.
- **Non-sortal (mixin-like)** — carries *no* identity of its own; it classifies instances that get identity from different kinds. You cannot count "physical objects" as a single kind because they span Cars, Rocks, Phones. Categories, mixins, roleMixins, phaseMixins.

**Rule:** every object class diagram must let every instance trace up to exactly one ultimate **kind** for identity. A model where some object instantiates no kind is incomplete.

## Dependence → Phase vs Role (the anti-rigid split)

Both phases and roles are anti-rigid sortals; they differ by **why** the type is contingent:

- **«phase»** — contingent on an **intrinsic** property change. Phases come in **partitions** that exhaustively cover the kind by a changing intrinsic condition: {Child, Adolescent, Adult} of Person by age; {Available, Busy} of a Resource. An instance is always in exactly one phase of the partition.
- **«role»** — contingent on a **relational/extrinsic** property: the instance plays the role *because it participates in a relationship*. Student (enrolled-at a School), Husband (married-to someone), Employee (employed-by an Organization). A role is always connected to a relator via «mediation».

## UFO-C essentials (social layer)

- **Agent** vs (non-agentive) **Object** — agents bear intentional moments (beliefs, desires, intentions, goals).
- **Social role** — a role defined within a social/institutional context.
- **Social relator** — a relator made of reciprocal **commitments** and **claims** between agents (an employment is a bundle of commitments/claims).
- **Normative description** — defines social/institutional types and the rules creating social moments (a law, a contract template, a policy).
- **Social object** — money, a passport, a corporation: objects whose existence depends on collective intentionality.

These map onto the gUFO/IR layer as relators + modes; in the AgentArmy pipeline, commitments/claims/mandates are exactly the **material relations reified as relators** (mitigation cases, mandates, evidence bundles).

## Quality structures (a UFO idea BFO lacks emphasis on)

UFO grounds qualities in **quality structures** (conceptual spaces): a quality (e.g. a specific color) is a point (**quale**) in a structured domain (the color spindle). This gives a principled way to model attribute value spaces, comparability, and similarity — useful when designing «quality» types and their datatypes/value partitions.
