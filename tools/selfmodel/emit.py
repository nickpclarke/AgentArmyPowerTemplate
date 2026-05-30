#!/usr/bin/env python3
"""
emit.py - deterministic first-cut compiler for the AgentArmy platform self-model.

Reads the canonical IR (ontology/platform-self-model/model/model.yaml) and the
A-Box (instances.yaml) and emits explicit projections - never collapsing them
(the one rule from templates/ontology-project/README.md):

  persistence/arcadedb-schema.sql  - hyperedge-as-vertex DDL (ARC-ADR-016)
  generated/SystemModel.g.cs       - C# object model (records + hypergraph base)
  semantic/model.gufo.ttl          - basic gUFO OWL projection (Level-3 target)
  instances/fragments.json         - A-Box as ARC-ADR-016 fragments (loader input)
  viz/self-model.contracts.mmd     - Mermaid: the contract integration web
  viz/self-model.tiers.mmd         - Mermaid: containers by tier + deployment
  provenance/build-manifest.json   - input/output content hashes

This is a FIRST CUT, not the full six-projection compiler. It deliberately
advances the open "build the generator vs adopt LinkML" question (Labs
Open-Questions) with a working, deterministic Python emitter.

Usage:  python tools/selfmodel/emit.py
Deps:   PyYAML (pip install pyyaml) + stdlib only.
"""
from __future__ import annotations
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ERROR: PyYAML required. Run: python -m pip install pyyaml")

ROOT = Path(__file__).resolve().parents[2]
PROJ = ROOT / "ontology" / "platform-self-model"
MODEL = PROJ / "model" / "model.yaml"
INSTANCES = PROJ / "model" / "instances.yaml"
SNAPSHOT = "2026-05-30"

# Instance group name -> nothing special; we read every list-of-dicts group.
INSTANCE_GROUPS = [
    "repositories", "contracts", "containers", "platforms",
    "organizations", "armies", "capabilities", "surfaces", "decisions", "releasetrains",
]
RELATOR_GROUPS = ["contract-binding", "deployment", "governed-by-decision", "partner-engagement",
                  "capability-realization", "capability-exposure", "release-delivery"]

# ---- brand / tech icons (Simple Icons, vendored in viz/icons/; inlined as data URIs so the
# viewer stays offline + canvas/PNG-safe). White marks ride on the colored type-disc. ----
ICON_DIR = Path(__file__).resolve().parents[2] / "ontology" / "platform-self-model" / "viz" / "icons"
ICON_BY_ID = {
    "org-anthropic": "anthropic", "org-microsoft": "microsoftazure", "org-openai": "openai",
    "org-google": "googlecloud", "org-cloudflare": "cloudflare", "org-postman": "postman",
    "org-cerebras": "@Cerebras",
    "plat-aca": "microsoftazure", "plat-keyvault": "microsoftazure", "plat-github": "github",
    "plat-gcp": "googlecloud", "plat-cf": "cloudflare", "plat-postman": "postman",
    "plat-nats": "natsdotio", "plat-postgres": "postgresql", "plat-fuseki": "apache", "plat-arcadedb": "@ArcadeDB",
    "army-claude": "anthropic", "army-copilot": "githubcopilot",
    "repo-agentarmy": "github", "repo-forge": "github",
}
ICON_BY_TYPE = {
    "HubRepository": "github", "SpokeRepository": "git", "Contract": "openapiinitiative",
    "PlatformContainer": "docker", "ApplicationContainer": "docker", "FunctionContainer": "docker",
}
# Architecture-icon variant (official cloud service icons, in viz/icons/arch/). Where a node has
# no service icon it falls back to its brand logo. Toggled live in the viewer (icon set: brand|arch).
ARCH_DIR = ICON_DIR / "arch"
ARCH_BY_ID = {"plat-aca": "azure-appservice", "plat-keyvault": "azure-keyvault", "plat-postgres": "azure-postgres"}
ARCH_BY_TYPE = {"PlatformContainer": "azure-container", "ApplicationContainer": "azure-container",
                "FunctionContainer": "azure-container"}
def _lettermark(text):
    t = "".join(c for c in str(text) if c.isalnum())[:2] or "?"
    t = t[0].upper() + (t[1].lower() if len(t) > 1 else "")
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><text x="12" y="16.5" '
            'font-family="ui-monospace,monospace" font-size="11" font-weight="700" '
            f'text-anchor="middle" fill="#ffffff">{t}</text></svg>')


def _data_uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


def resolve_icon(v):
    """(data_uri, kind): 'logo' = full-colour brand SVG (rides a white chip); 'letter' = lettermark."""
    spec = ICON_BY_ID.get(v["id"]) or ICON_BY_TYPE.get(v["type"])
    if spec and not spec.startswith("@"):
        p = ICON_DIR / (spec + ".svg")
        if p.exists():
            return _data_uri(p.read_text(encoding="utf-8")), "logo"
    text = spec[1:] if (spec and spec.startswith("@")) else v["props"].get("name", v["id"])
    return _data_uri(_lettermark(text)), "letter"


def resolve_arch_icon(v):
    """Official cloud-service icon where one exists; otherwise fall back to the brand icon."""
    name = ARCH_BY_ID.get(v["id"]) or ARCH_BY_TYPE.get(v["type"])
    if name:
        p = ARCH_DIR / (name + ".svg")
        if p.exists():
            return _data_uri(p.read_text(encoding="utf-8")), "logo"
    return resolve_icon(v)


def node_url(v):
    """A real artifact URL for the node, for the viewer's 'open' action (None if not constructible)."""
    t, nm = v["type"], v["props"].get("name", "")
    if t in ("HubRepository", "SpokeRepository"):
        return "https://github.com/nickpclarke/" + nm
    if t == "ArchitecturalDecision":
        return "https://nickpclarke.github.io/AgentArmy/architecture-decisions/"
    if t == "Contract":
        return "https://nickpclarke.github.io/AgentArmy/contracts/"
    return None


def load_yaml(p: Path) -> dict:
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def safe(s: str) -> str:
    """mermaid/C#-safe identifier."""
    return re.sub(r"[^A-Za-z0-9_]", "_", str(s))


def sql_type(rng: str, _enums: set[str]) -> str:
    if rng in ("integer",):
        return "INTEGER"
    return "STRING"  # enums + type refs + strings all persist as STRING


def cs_type(rng: str, enums: set[str]) -> str:
    if rng == "integer":
        return "int?"
    if rng == "string":
        return "string?"
    if rng in enums:
        return rng + "?"
    return "string?"  # type reference -> id string


# ---------------------------------------------------------------------------
def main() -> int:
    model = load_yaml(MODEL)
    inst = load_yaml(INSTANCES)

    types = model.get("types", [])
    relators = model.get("relators", [])

    enums = {t["id"]: t.get("literals", []) for t in types if t["stereotype"] == "enumeration"}
    enum_ids = set(enums)
    # vertex-bearing types: category + kinds + subkinds (exclude enumerations + roles)
    vtypes = [t for t in types if t["stereotype"] in ("category", "kind", "subkind")]
    vtype_ids = {t["id"] for t in vtypes}

    out = {}

    # --- 1. ArcadeDB DDL (hyperedge-as-vertex) ------------------------------
    sql = [
        "-- GENERATED by tools/selfmodel/emit.py from model/model.yaml - do not hand-edit.",
        "-- Hyperedge-as-vertex persistence (ARC-ADR-016): a relator is a VERTEX joined to",
        "-- participants by BINDS_ROLE edges; bitemporal validity lives on the relator vertex.",
        "",
        "CREATE VERTEX TYPE OntologyElement IF NOT EXISTS;",
        "CREATE VERTEX TYPE HyperNode      IF NOT EXISTS EXTENDS OntologyElement;",
        "CREATE VERTEX TYPE RelatorVertex  IF NOT EXISTS EXTENDS OntologyElement;",
        "CREATE EDGE   TYPE BINDS_ROLE  IF NOT EXISTS;",
        "CREATE EDGE   TYPE CONTAINER_OF IF NOT EXISTS;",  # binary: container -> owning repo
        "CREATE PROPERTY OntologyElement.ontologyIri IF NOT EXISTS STRING;",
        "CREATE PROPERTY OntologyElement.label       IF NOT EXISTS STRING;",
        "CREATE PROPERTY BINDS_ROLE.roleName IF NOT EXISTS STRING;",
        "CREATE PROPERTY BINDS_ROLE.ordinal  IF NOT EXISTS INTEGER;",
        "",
        "-- Object types (category -> kinds -> subkinds)",
    ]

    def extends_of(t: dict) -> str:
        parent = t.get("parent")
        if parent and parent in vtype_ids:
            return parent
        return "HyperNode"

    # order: category, kinds, subkinds  (guarantees parent emitted first)
    order = (
        [t for t in vtypes if t["stereotype"] == "category"]
        + [t for t in vtypes if t["stereotype"] == "kind"]
        + [t for t in vtypes if t["stereotype"] == "subkind"]
    )
    for t in order:
        sql.append(f"CREATE VERTEX TYPE {t['id']} IF NOT EXISTS EXTENDS {extends_of(t)};")
        for p in t.get("properties", []):
            sql.append(f"CREATE PROPERTY {t['id']}.{p['id']} IF NOT EXISTS {sql_type(p['range'], enum_ids)};")
    sql.append("")
    sql.append("-- Relator vertices (reified n-ary relations)")
    for r in relators:
        rid = safe(r["id"])
        sql.append(f"CREATE VERTEX TYPE {rid} IF NOT EXISTS EXTENDS RelatorVertex;")
        for p in r.get("properties", []):
            sql.append(f"CREATE PROPERTY {rid}.{p['id']} IF NOT EXISTS {sql_type(p['range'], enum_ids)};")
        for col in (r.get("temporal") or {}).values():
            sql.append(f"CREATE PROPERTY {rid}.{col} IF NOT EXISTS DATETIME;")
    sql.append("")
    sql.append("CREATE INDEX IF NOT EXISTS ON OntologyElement (ontologyIri) UNIQUE;")
    sql.append("CREATE INDEX IF NOT EXISTS ON BINDS_ROLE (roleName) NOTUNIQUE;")
    out["persistence/arcadedb-schema.sql"] = "\n".join(sql) + "\n"

    # --- 2. C# object model -------------------------------------------------
    cs = [
        "// GENERATED by tools/selfmodel/emit.py - do not hand-edit.",
        "// Hypergraph object model for the AgentArmy platform self-model (ARC-ADR-016).",
        "#nullable enable",
        "using System;",
        "using System.Collections.Generic;",
        "",
        "namespace AgentArmy.SelfModel.Generated;",
        "",
        "public interface IHyperElement { string Id { get; } string OntologyIri { get; } }",
        "public sealed record RoleBinding(string RoleName, string ParticipantId, int Ordinal);",
        "",
    ]
    for eid, lits in enums.items():
        members = ", ".join(safe(l) for l in lits)
        cs.append(f"public enum {eid} {{ {members} }}")
    cs.append("")
    for t in order:
        fields = ['string Id', 'string OntologyIri', 'string Name']
        for p in t.get("properties", []):
            if p["id"] == "name":
                continue
            fields.append(f"{cs_type(p['range'], enum_ids)} {safe(p['id'][:1].upper() + p['id'][1:])}")
        body = ",\n        ".join(fields)
        cs.append(f"/// <summary>{t.get('description','').replace(chr(10),' ')}</summary>")
        cs.append(f"public sealed record {t['id']}(\n        {body}) : IHyperElement;")
        cs.append("")
    for r in relators:
        rid = safe(r["id"][:1].upper() + r["id"][1:].replace("-", " ").title().replace(" ", ""))
        props = ['string Id', 'string OntologyIri', 'IReadOnlyList<RoleBinding> Bindings']
        for p in r.get("properties", []):
            props.append(f"{cs_type(p['range'], enum_ids)} {safe(p['id'][:1].upper()+p['id'][1:])}")
        body = ",\n        ".join(props)
        cs.append(f"/// <summary>Relator: {r.get('description','').replace(chr(10),' ')}</summary>")
        cs.append(f"public sealed record {rid}(\n        {body}) : IHyperElement;")
        cs.append("")
    out["generated/SystemModel.g.cs"] = "\n".join(cs) + "\n"

    # --- 3. gUFO TTL (basic Level-3 projection) -----------------------------
    ns = model["ontology"]["default_namespace"]
    ttl = [
        "# GENERATED by tools/selfmodel/emit.py - basic gUFO projection (do not hand-edit).",
        "@prefix : <%s> ." % ns,
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix gufo: <http://purl.org/nemo/gufo#> .",
        "",
        "<%s> a owl:Ontology ." % ns.rstrip("#"),
        "",
    ]
    for t in vtypes:
        cls = f":{safe(t['id'])}"
        ttl.append(f"{cls} a owl:Class ;")
        gt = t.get("gufo_type")
        if gt:
            ttl.append(f"    rdfs:subClassOf {gt} ;")
        if t.get("parent") in vtype_ids:
            ttl.append(f"    rdfs:subClassOf :{safe(t['parent'])} ;")
        ttl.append(f'    rdfs:label "{t["id"]}" ;')
        ttl.append(f'    rdfs:comment "{t.get("description","").replace(chr(34), chr(39))}" .')
        ttl.append("")
    for r in relators:
        ttl.append(f":{safe(r['id'])} a owl:Class ; rdfs:subClassOf gufo:Relator ;")
        ttl.append(f'    rdfs:comment "{r.get("description","").replace(chr(34), chr(39))}" .')
        ttl.append("")
    out["semantic/model.gufo.ttl"] = "\n".join(ttl) + "\n"

    # --- 4. fragments.json (A-Box for the loader) ---------------------------
    vertices = []
    for g in INSTANCE_GROUPS:
        for item in inst.get(g, []) or []:
            props = {k: v for k, v in item.items() if k not in ("id", "type", "owner")}
            vertices.append({"id": item["id"], "type": item["type"],
                             "iri": ns + item["id"], "props": props})
    edges = []  # binary edges (container-of from owner)
    for c in inst.get("containers", []) or []:
        if c.get("owner"):
            edges.append({"type": "CONTAINER_OF", "from": c["id"], "to": c["owner"]})

    frag_relators = []
    role_keys = {
        "contract-binding": [("producer", False), ("consumers", True), ("contract", False)],
        "deployment": [("deployed", False), ("onto", False)],
        "governed-by-decision": [("decision", False), ("governs", True)],
        "partner-engagement": [("partner", False), ("regarding", True)],
        "capability-realization": [("capability", False), ("realizedBy", True)],
        "capability-exposure": [("surface", False), ("exposes", True)],
        "release-delivery": [("train", False), ("delivers", True)],
    }
    for rg in RELATOR_GROUPS:
        for item in inst.get(rg, []) or []:
            bindings = []
            ordinal = 0
            for role, is_list in role_keys[rg]:
                val = item.get(role)
                if val is None:
                    continue
                targets = val if is_list else [val]
                for tgt in targets:
                    bindings.append({"role": role, "target": tgt, "ordinal": ordinal})
                    ordinal += 1
            props = {k: v for k, v in item.items()
                     if k not in ["id"] + [rk for rk, _ in role_keys[rg]]}
            frag_relators.append({"id": item["id"], "type": safe(rg), "iri": ns + item["id"],
                                  "props": props, "bindings": bindings})

    fragments = {
        "schema_ref": "ontology/platform-self-model/model/model.yaml",
        "snapshot": SNAPSHOT,
        "namespace": ns,
        "base_types": {"node": "HyperNode", "relator": "RelatorVertex", "role_edge": "BINDS_ROLE"},
        "vertices": vertices,
        "edges": edges,
        "relators": frag_relators,
    }
    out["instances/fragments.json"] = json.dumps(fragments, indent=2, sort_keys=False) + "\n"

    # --- 5. Mermaid: the contract integration web ---------------------------
    con_status = {c["id"]: c.get("status", "") for c in inst.get("contracts", [])}
    mm = ["flowchart LR",
          "    %% GENERATED by emit.py - the contract integration web (producer -> contract -> consumers)",
          "    classDef shipped fill:#d6f5d6,stroke:#2e7d32,color:#000;",
          "    classDef proposed fill:#fff3cd,stroke:#b8860b,color:#000;",
          "    classDef repo fill:#e3f0ff,stroke:#1565c0,color:#000;"]
    for r in inst.get("repositories", []):
        mm.append(f'    {safe(r["id"])}["{r["name"]}"]:::repo')
    for c in inst.get("contracts", []):
        cls = "shipped" if con_status.get(c["id"]) == "Shipped" else "proposed"
        mm.append(f'    {safe(c["id"])}(["{c["name"]}"]):::{cls}')
    for cb in inst.get("contract-binding", []):
        mm.append(f'    {safe(cb["producer"])} ==>|produces| {safe(cb["contract"])}')
        for cons in cb["consumers"]:
            if cons != cb["producer"]:
                mm.append(f'    {safe(cb["contract"])} -->|consumed by| {safe(cons)}')
    out["viz/self-model.contracts.mmd"] = "\n".join(mm) + "\n"

    # --- 6. Mermaid: containers by tier + deployment ------------------------
    tiers = {"Platform": [], "Application": [], "Function": []}
    for c in inst.get("containers", []):
        tiers.setdefault(c["tier"], []).append(c)
    mt = ["flowchart TB",
          "    %% GENERATED by emit.py - containers by tier (ARC-ADR-023) + deployment",
          "    classDef plat fill:#ffe0b2,stroke:#e65100,color:#000;"]
    for tier, items in tiers.items():
        mt.append(f"    subgraph {safe(tier)}[\"{tier} tier\"]")
        for c in items:
            mt.append(f'        {safe(c["id"])}["{c["name"]}"]')
        mt.append("    end")
    for p in inst.get("platforms", []):
        mt.append(f'    {safe(p["id"])}[("{p["name"]}")]:::plat')
    for d in inst.get("deployment", []):
        mt.append(f'    {safe(d["deployed"])} -.->|deploys to| {safe(d["onto"])}')
    out["viz/self-model.tiers.mmd"] = "\n".join(mt) + "\n"

    # --- 7. Interactive graph viewer (Cytoscape, self-contained HTML) --------
    # lift viz-driving properties to top-level node data so the viewer can use clean
    # selectors (e.g. node[evolutionStage="Genesis"]) and property-driven style mappers.
    LIFT = ("evolutionStage", "status", "tier", "layer", "repoRole",
            "criticality", "level", "format", "platformKind")
    cy_nodes = []
    for v in vertices:
        p = v["props"]
        nd = {"id": v["id"], "label": str(p.get("name", v["id"])),
              "ntype": v["type"], "group": "object", "props": p}
        for k in LIFT:
            if k in p:
                nd[k] = p[k]
        nd["icon"], nd["iconKind"] = resolve_icon(v)
        nd["iconArch"], nd["iconArchKind"] = resolve_arch_icon(v)
        _url = node_url(v)
        if _url:
            nd["url"] = _url
        cy_nodes.append({"data": nd})
    for r in frag_relators:
        cy_nodes.append({"data": {"id": r["id"], "label": r["type"].replace("_", " "),
                                  "ntype": r["type"], "group": "relator", "props": r.get("props", {})}})
    cy_edges = []
    for r in frag_relators:
        for b in r["bindings"]:
            cy_edges.append({"data": {"id": f'{r["id"]}~{b["role"]}~{b["target"]}',
                                      "source": r["id"], "target": b["target"], "label": b["role"],
                                      "etype": "role", "relatorType": r["type"]}})
    for e in edges:
        cy_edges.append({"data": {"id": f'{e["from"]}~co~{e["to"]}',
                                  "source": e["from"], "target": e["to"], "label": "container-of", "etype": "binary"}})
    _tmpl = (Path(__file__).parent / "graph-viewer.template.html").read_text(encoding="utf-8")
    out["viz/self-model-graph.html"] = (_tmpl
        .replace("__ELEMENTS__", json.dumps({"nodes": cy_nodes, "edges": cy_edges}))
        .replace("__SNAPSHOT__", SNAPSHOT))

    # --- 8. Lexicon: agent-facing canonical vocabulary (verbs + spaces) -----
    # The one artifact every agent reads to use platform names correctly.
    cap_real = {cr["capability"]: cr.get("realizedBy", [])
                for cr in inst.get("capability-realization", []) or []}
    exp_by_surface = {}
    for ce in inst.get("capability-exposure", []) or []:
        exp_by_surface.setdefault(ce["surface"], []).extend(ce.get("exposes", []))
    lex = [
        "# @generated by tools/selfmodel/emit.py — DO NOT EDIT.",
        "# Agent-facing canonical vocabulary of the AgentArmy system ontology.",
        "# Source of truth: ontology/platform-self-model/model/*.yaml.",
        "# Regenerate: python tools/selfmodel/emit.py",
        f"snapshot: {SNAPSHOT}",
        "",
        "# Capabilities — the VERBS (functional dispositions, independent of implementation).",
        "capabilities:",
    ]
    for c in sorted(inst.get("capabilities", []) or [], key=lambda x: x["id"]):
        rb = ", ".join(cap_real.get(c["id"], []))
        lex.append(f'  - {{ id: {c["id"]}, name: "{c["name"]}", realized_by: [{rb}] }}')
    lex += ["", "# Surfaces — the SPACES (UX you interface a capability through).", "surfaces:"]
    for s in sorted(inst.get("surfaces", []) or [], key=lambda x: x["id"]):
        exp = ", ".join(exp_by_surface.get(s["id"], []))
        lex.append(f'  - {{ id: {s["id"]}, name: "{s["name"]}", exposes: [{exp}] }}')
    out["generated/lexicon.yaml"] = "\n".join(lex) + "\n"

    # --- write all + manifest ----------------------------------------------
    manifest = {"snapshot": SNAPSHOT, "inputs": {}, "outputs": {}}
    for name, content in {"model/model.yaml": MODEL.read_text(encoding="utf-8"),
                          "model/instances.yaml": INSTANCES.read_text(encoding="utf-8")}.items():
        manifest["inputs"][name] = hashlib.sha256(content.encode()).hexdigest()[:16]

    for rel, content in out.items():
        dest = PROJ / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        manifest["outputs"][rel] = hashlib.sha256(content.encode()).hexdigest()[:16]

    (PROJ / "provenance").mkdir(parents=True, exist_ok=True)
    (PROJ / "provenance" / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # summary
    print("self-model emitted:")
    print(f"  vertices : {len(vertices)}")
    print(f"  edges    : {len(edges)} (binary)")
    print(f"  relators : {len(frag_relators)} (n-ary, hyperedge-as-vertex)")
    print(f"  vtypes   : {len(order)} object types + {len(relators)} relator types + {len(enums)} enums")
    for rel in list(out) + ["provenance/build-manifest.json"]:
        print(f"  wrote    : ontology/platform-self-model/{rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
