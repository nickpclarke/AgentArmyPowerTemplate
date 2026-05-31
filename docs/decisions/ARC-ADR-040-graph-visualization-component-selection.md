# ARC-ADR-040 — Graph Visualization Component Selection (standing program)

- **Status:** Accepted
- **Date:** 2026-05-30
- **Deciders:** platform / frontend-core; informed by a 2026-05-30 component evaluation (research-analyst) + visual design pass (ui-designer)
- **Anchors:** [ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md) (relator-vertex + typed role-binding hyperedges) · `ontology/platform-self-model/` (the digital-twin consumer)

## Context and problem statement

The platform renders a **hypergraph digital twin** (reified relators as nodes, typed role-binding edges; properties drive visual encoding) and needs strong interactivity and visual polish across **web (now), desktop (Electron), and mobile (planned React Native spoke)**. Graph-viz is a fast-moving field (WebGL renderers, 3D, commercial engines) and the wrong long-lived choice is expensive. We need (a) a current decision and (b) a **standing program** so the selection never silently drifts from the state of the art or from what's actually installed.

## Decision drivers

- Hypergraph / compound-node fit (relators-as-vertices, ARC-ADR-016).
- Property-driven visual encoding (type, evolutionStage, status, degree, criticality → color/size/glow/ring/pulse).
- Interactivity + "wow" ceiling; performance at scale; 2D now, 3D later.
- License/cost; maintenance health; device fit (web/desktop/mobile); Next.js + Electron + React Native fit; offline/embeddable.

## Considered options

Cytoscape.js · Sigma.js (+Graphology) · vis-network · D3/d3-force · react-force-graph / 3d-force-graph · AntV G6 5.x · Neo4j NVL · reagraph · Ogma (commercial) · KeyLines/ReGraph (commercial) · yFiles (commercial) · mobile-native (RN Skia, Flutter graph libs). Full matrix in the evaluation (see *More information*).

## Decision outcome

**Selected per tier:**

| Tier | Choice | When |
|---|---|---|
| **Web — interactive (default)** | **Cytoscape.js** (MIT) | now. Native compound nodes fit the relator-vertex model; CSS-like style engine covers property encoding; proven Next.js `dynamic(ssr:false)` + Electron. The current `ontology/platform-self-model/viz/` viewer uses it + webcola physics + navigator + cxtmenu. |
| **Web — at scale / WebGL** | **Sigma.js v3 + Graphology** | when element count (nodes + role-binding edges) crosses ~3–5k at interactive FPS, or a GPU-only effect is required. No native compound → relators render as distinct hub nodes, not containment. |
| **"Wow" / 3D** | **3d-force-graph** (Three.js) or **AntV G6 5.x** (compound + 3D) | when a 3D/immersive twin tile appears on the roadmap. Coexists as a separate viewer. |
| **Mobile (RN / Flutter)** | **WebView bridge** to the same web component (`postMessage` hydration); evaluate native only if WebView proves insufficient | when the mobile spoke is commissioned. No RN-native graph lib matches the requirement as of 2026. |
| **Desktop (Electron)** | **same as web tier, verbatim** | Chromium renderer = full WebGL; no separate selection. |

**Exit triggers off Cytoscape.js (quantitative):** sustained <30 FPS on real data; 3–5k elements with the relator-vertex topology; compound-interaction pan/zoom >500 ms; Cytoscape WebGL preview still missing dashed/segmented edges after two releases; or a 3D requirement. Any trigger → schedule a Sigma/WebGL (or 3D) spike within one sprint.

## Standing program

**Charter.** Govern which rendering libraries are approved, trialed, and retired across web/mobile/desktop; keep *selected ↔ in-use ↔ state-of-the-art* aligned; drive changes by **measured signals**, not preference; make every selection change visible and traceable.

**Cadence.**
- **Quarterly spike** (1 sprint): benchmark the production library at current real-data scale (FPS × node-count × the *real* relator-vertex topology), evaluate the top alternative against the checklist, append a row to this ADR's revision history.
- **Trigger review** (unscheduled): any exit trigger above fires → spike next sprint.
- **Major-version watch:** Cytoscape WebGL graduating preview; Sigma v4 → stable; G6 major API change → compatibility spike within 4 weeks.
- **New spoke:** evaluate device-native options when (not before) the spoke team exists.

**Selection criteria checklist** (apply every review / before adopting any lib): compound/hyperedge fit · property-driven encoding · pan/zoom/select/hover/drag · relator-activation animation · measured FPS at 1k/5k/10k on real topology (≥30 FPS interactive) · ≤500 MB renderer heap @10k · ≤3 s TTI @2k · Next.js `ssr:false` clean · Electron WebGL confirmed · WebView round-trip ≤100 ms · ≤200 KB gz bundle · license fits distribution model · last release ≤6 mo · ≥2 maintainers / corporate sponsor · no critical CVEs · vendor benchmarks cross-validated.

**Recording.** This ADR is the canonical record (revision history appended each review). Each quarterly spike also drops a short note in `planning/synthesis/viz-lib-selection-<YYYY-Qn>.md` with the benchmark table + keep/migrate/spike verdict.

**Fleet-heartbeat integration.** Add a read-only drift check to `tools/fleet-heartbeat.mjs`: compare the approved lib + semver here against the installed version in each spoke's `package.json`; on major-version drift or a *rejected* lib being installed, file a deduped `agent-army-task` Enabler tagged `viz-lib-drift`. Start dry-run-report-only; promote to `--apply` after two stable quarterly cycles (same graduation path as other heartbeat checks).

## Companion lane — static diagram-as-code (Mermaid now, Kroki later) — *Proposed*

> **Scope note.** The tier table above governs the **interactive** graph (a live, pannable
> hypergraph viewer). This section governs the **static diagram-as-code** lane — narrative
> diagrams emitted *from the model* as text and rendered to SVG/PNG for docs, ADRs, and the
> Obsidian arch-views. They are different problems with different tools; do not conflate them.
> This lane is **Proposed** (captured here so a prior verbal decision stops being lost); the
> interactive-tier decision above remains **Accepted**.

**What exists today (built).** `tools/selfmodel/emit.py` already projects the self-model to
**Mermaid** — `viz/self-model.contracts.mmd` (contract integration web) and
`viz/self-model.tiers.mmd` (containers by tier). The docs site renders Mermaid inline via
`pymdownx.superfences`. So the **model → diagram-text** half of this lane is real and shipping;
Mermaid is the default static format.

**The gap (why this section exists).** Mermaid is one notation. The platform also wants
**richer / formal** diagram families the model can project into — notably **ArchiMate** (formal
EA layered views, pairing with the TOGAF/EA agent roster) and others (PlantUML, C4-PlantUML,
GraphViz/DOT, D2, BPMN). Authoring a bespoke renderer per format is the wrong move.

**Proposed choice — [Kroki](https://kroki.io) as the unified render gateway.** One HTTP endpoint
that renders ~25 diagram-as-code formats (Mermaid, PlantUML, ArchiMate, C4-PlantUML, GraphViz,
D2, BPMN, Excalidraw, …) from text → SVG/PNG. The model keeps emitting *text*; Kroki turns any
supported notation into an image with no per-format renderer to own.

| Concern | Direction |
|---|---|
| **Default format** | **Mermaid** (already emitted; native in mkdocs) — keep for most narrative diagrams |
| **Formal EA views** | **ArchiMate** via Kroki — backlog; C4 (Mermaid-native) is the simpler interim |
| **Render gateway** | **Kroki**, **self-hosted** (container) so ontology/diagram text never leaves the box — same data-egress posture as the rest of the fleet |
| **Boundary** | Static images for docs/ADRs/Obsidian. NOT the interactive viewer (that's the tier table). NOT a replacement for `.mmd` emission (Kroki renders what `emit.py` emits) |

**Open questions before this graduates to Accepted:** (1) self-hosted Kroki container tier +
image.json, or call the public service for non-sensitive diagrams only? (2) does `emit.py` gain
an ArchiMate projection, or do we hand-author ArchiMate? (3) build-time pre-render to committed
SVG vs. live Kroki fetch in mkdocs. Resolve via a spike before flipping to Accepted.

## Consequences

- **Good:** a defensible current choice (MIT, zero cost, fits the hypergraph), an explicit measured exit ramp, and a process that prevents silent drift. The web component is reused on desktop and (via WebView) mobile — one investment, three targets.
- **Cost / risk:** Cytoscape's canvas renderer ceiling (~3–5k elements) means a migration is *expected* as the twin grows — budgeted, not surprising. Compound-node UX does not survive a move to Sigma (flat projection instead) — a known UX shift to plan for.
- **Static lane:** the Mermaid emission is live; Kroki + ArchiMate are *Proposed* — captured here so the prior verbal decision isn't lost again, not yet built.

## More information

2026-05-30 component evaluation matrix + sources (Cytoscape 3.33 WebGL preview, Sigma v3/v4, G6 5.x, Ogma/KeyLines/yFiles, RN/Flutter options). Reserve `viz-lib-drift` label + the `planning/synthesis/` note on first quarterly spike. Revisit: Q3 2026.

### Revision history
| Date | Change |
|---|---|
| 2026-05-30 | Initial decision: Cytoscape.js (web/desktop), Sigma.js (scale), 3d-force-graph/G6 (3D), WebView (mobile). Program established. |
| 2026-05-31 | Added the **static diagram-as-code companion lane** (*Proposed*): Mermaid (already emitted by `emit.py`) as default, **Kroki** as the unified render gateway, **ArchiMate** as the formal-EA backlog format. Captures a prior verbal decision that was never written down; interactive-tier decision unchanged. |
