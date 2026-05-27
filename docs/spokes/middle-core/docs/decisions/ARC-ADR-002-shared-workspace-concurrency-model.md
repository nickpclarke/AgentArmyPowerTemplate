# ARC-ADR-002 — Shared Workspace and Concurrency Model for the Agent Fleet

- **Status:** Proposed
- **Date:** 2026-05-26
- **Deciders:** middle-core maintainers
- **Consulted:** backend-core, frontend-core, agent_runtime
- **Informed:** AgentArmy hub

## Context and Problem Statement

The AgentArmy fleet is multiple agents (some .NET, some Python, some JS)
that need to coordinate over the same business objects: a `knowledge-source`
being ingested, an `evidence-pack` being assembled, a `tool-offering` being
gated for promotion. Middle-core already declares an in-memory object graph
as the canonical home for these — the charter pipeline says
`... -> in-memory object graph -> scenario runtime -> evidence`.

What is missing is a **concurrency and access model** for that graph that
answers three questions at once:

1. How do two agents avoid clobbering each other when they both touch the
   same business object?
2. Can a .NET agent live *inside* middle-core's runtime and share its
   working memory directly, instead of calling itself over HTTP?
3. Can a Python or JS agent participate in the same workspace without
   being demoted to a second-class citizen?

Today middle-core has a POCO object graph, no concurrency story, no
in-process agent hosting story, and no durability story. Different agents
already coordinate via HTTP request/response; once two of them touch the
same object in the same scenario, the lack of a single-writer invariant
becomes a correctness bug.

### Scope

This ADR covers **how agents share working state** inside middle-core's
runtime and across the polyglot fleet. It does not cover:

- The pub/sub transport itself — see ARC-ADR-001.
- Durable workflow execution (BPMN scenarios, HITL waits) — separate ADR.
- The ArcadeDB persistence schema — owned by backend-core.

## Decision Drivers

1. **Single-writer-per-business-object** is the invariant that makes
   state machines work. Two writers to the same object's state machine
   at the same time is undefined behavior.
2. **Polyglot fleet.** Python (modelgen + agent_runtime), C# (middle-core
   runtime), JS (frontend-core). None can be a second-class citizen.
3. **Charter: state machines are first-class.** Lifecycle transitions are
   ontology commitments, not UI labels.
4. **Charter: evidence is a primitive.** Every state change must be
   capturable as evidence.
5. **Charter: provider-neutral.** Whatever runtime we pick must run on
   ACA, GCP, on-prem, and a developer laptop with `docker compose up`.
6. **Fast path for co-located agents.** .NET agents that live in the same
   process as the graph should not pay HTTP serialization for every read.
7. **Operational floor.** No new clustered control plane just to add a
   concurrency model.

## Considered Options

1. **Microsoft Orleans grains + in-process hosting + HTTP/gRPC façade**
2. **DAPR actors with a sidecar per agent**
3. **Plain HTTP with optimistic concurrency (ETag/version)**
4. **Akka.NET actors with the same dual-access pattern**

## Decision Outcome

**Chosen: Microsoft Orleans grains as the unit of shared state, with
three access modes against one canonical workspace.**

Every business object becomes a **single-threaded grain** keyed by its
canonical ID (`knowledge-source/abc123`, `evidence-pack/def456`). The
grain owns its state machine, enforces transitions, and emits evidence
on every transition. The grain *is* the blackboard cell — the same
object exists at exactly one place in the cluster at a time.

Three access modes sit on top of that one workspace:

| Access mode | Who uses it | How |
|---|---|---|
| **In-process grain reference** | .NET agents co-hosted in middle-core | `IGrainFactory.GetGrain<IKnowledgeSourceGrain>(id)`; zero serialization on the local silo |
| **HTTP/gRPC façade** | Polyglot agents (Python, JS, future Go) | `POST /objects/{kind}/{id}/transition` → middle-core resolves to the same grain |
| **CloudEvents on NATS** | Any agent that wants to react to changes | Subscribes to `aax.middle.<kind>.<event>.v1` per ARC-ADR-001 |

All three modes funnel through the grain. The grain is single-threaded,
so concurrent callers — regardless of access mode — are serialized
inside the grain's turn-based scheduler. No distributed locks, no
optimistic-retry loops, no clobbering.

Grain state persists asynchronously to ArcadeDB via backend-core's
projection ports; middle-core never writes to ArcadeDB directly.

### Positive Consequences

- **One mental model.** Grain = business object = state machine =
  blackboard cell. The same thing seen from three sides.
- **Single-writer invariant for free.** Orleans guarantees one active
  grain instance per ID across the cluster; the state machine never
  sees a race.
- **In-process fast path.** .NET agents inside middle-core take direct
  grain references and pay no HTTP serialization. This is the
  "shared in-process memory" mode without giving up correctness.
- **Polyglot stays first-class.** Python and JS agents call the
  HTTP/gRPC façade and land in the exact same grain. Identical
  semantics; different transport.
- **Notifications already solved.** Grain transitions publish via
  ARC-ADR-001's NATS + CloudEvents fabric — out-of-process agents
  subscribe instead of polling.
- **Charter alignment.** State machines and evidence emission live
  inside the grain — the two charter primitives are co-located with the
  state they govern.
- **Durability path.** Orleans persistence providers exist; a
  backend-core projection port becomes the persistence target without
  redesigning the runtime.

### Negative Consequences

- **Orleans is .NET on the host side.** Only .NET agents can co-locate
  for the in-process fast path. Polyglot agents always use RPC. We
  accept this — the alternative (forcing every agent to be .NET)
  contradicts driver #2.
- **Clustering complexity arrives early.** Once middle-core scales
  past one replica, Orleans needs a membership provider
  (ADO.NET/Azure Table/Consul). Mitigated by running single-silo until
  load justifies clustering.
- **In-process hosting needs a discipline.** Agents that co-locate are
  *libraries hosted by middle-core*, not independent daemons. We need
  an agent-SDK contract (lifecycle, cancellation, capability declaration).
- **Reentrancy decisions.** Each grain method must decide whether it's
  reentrant. Default non-reentrant is safest but limits throughput on
  hot grains; we'll need a policy.

## Pros and Cons of the Options

### Orleans grains + in-process + HTTP/gRPC façade

- ✅ Single-writer invariant per business object
- ✅ Three access modes against one workspace
- ✅ In-process fast path for .NET agents
- ✅ Charter-aligned: state machine + evidence live inside the grain
- ✅ Persistence and clustering are configurable, not architectural rewrites
- ❌ .NET-only on the host
- ❌ Clustering operationally non-trivial at scale
- ❌ Reentrancy and deactivation policies need design work

### DAPR actors + sidecar per agent

- ✅ Language-agnostic actor model — Python and JS agents can host
  actors natively
- ✅ Pluggable state stores
- ❌ Sidecar-per-agent is heavy ops; doubles container count
- ❌ Loses the "agents as libraries inside middle-core" mode entirely
- ❌ Less mature .NET tooling than Orleans; weaker LINQ/Roslyn story
- ❌ Couples to DAPR runtime (a meaningful provider lock-in)

### Plain HTTP + optimistic concurrency (ETag/version)

- ✅ Simplest; no new runtime
- ✅ Stateless middle-core scales horizontally trivially
- ❌ No in-process fast path at all
- ❌ Concurrent writers retry-loop instead of being serialized; livelock
  risk on hot objects
- ❌ State machine has to handle concurrent transition attempts in
  every method; defensive code everywhere
- ❌ Doesn't give the "shared in-process memory" feel the fleet wants

### Akka.NET actors

- ✅ Mature actor model with the same dual-access shape
- ✅ More flexible routing than Orleans
- ❌ Less opinionated about persistence — we'd be designing a persistence
  layer ourselves
- ❌ Smaller community than Orleans in 2026; fewer .NET-shop hires
- ❌ Same .NET-only-host limitation as Orleans, with less Microsoft
  tooling

## Confirmation

The decision is confirmed when:

1. One business-object kind (proposed: `knowledge-source`) is migrated
   from POCO to an Orleans grain, with its state machine running inside
   the grain.
2. A .NET agent example takes an `IKnowledgeSourceGrain` reference via
   `IGrainFactory` and drives a transition — no HTTP hop.
3. The Python `agent_runtime` example drives the same transition via
   the HTTP façade and lands in the same grain.
4. Each grain transition emits a CloudEvent on
   `aax.middle.knowledge.source.transitioned.v1` (per ARC-ADR-001) and
   a subscriber receives it.
5. Grain state is persisted via a backend-core projection port — no
   direct ArcadeDB writes from middle-core.
6. A round-trip test fires two concurrent transitions on the same
   grain from two different access modes and asserts they are
   serialized, not interleaved.
7. The ADR is referenced from `docs/middle-core-model-runtime.md` as
   the concurrency model for the runtime layer.

## More Information

- **Related:**
  - ARC-ADR-001 — pub/sub broker selection (provides the
    change-notification fabric).
  - Future ADR — durable workflow engine (Temporal-class) for BPMN
    scenarios and HITL waits.
  - Future ADR — grain persistence and projection strategy against
    backend-core's ArcadeDB.
- **Standards:** Microsoft Orleans 8+, gRPC, CloudEvents v1.0.
- **Follow-ups:**
  - Define the agent-SDK contract for in-process co-hosting
    (lifecycle, cancellation, capability declaration, evidence
    emission API).
  - Decide grain reentrancy policy per object kind.
  - Decide grain ID scheme — natural keys vs. surrogate IDs.
  - Decide cluster membership provider (single-silo vs.
    ADO.NET/Consul/Azure Table) and when to flip the switch.
  - Decide whether the HTTP façade is auto-generated from grain
    interfaces by modelgen.
