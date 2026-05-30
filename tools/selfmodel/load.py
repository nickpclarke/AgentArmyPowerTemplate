#!/usr/bin/env python3
"""
load.py - load the platform self-model A-Box into ArcadeDB as a hypergraph.

Follows the proven ARC-ADR-016 pattern from backend-core/app/ontology/arcade_schema.py
(relator-as-vertex + BINDS_ROLE role edges). Idempotent: re-running upserts.

  --dry-run : parse fragments + build the command plan, NO network (pure stdlib).
  (default) : connect via httpx, ensure schema, upsert vertices/relators/edges.

httpx is imported lazily (only the live path needs it), so --dry-run runs with
zero third-party deps. Connection env (same contract as backend-core/app/config.py):
  ARCADEDB_URL  default http://localhost:2480   ARCADEDB_USER  default root
  ARCADEDB_PASSWORD  default ""                  DB_NAME        default knowledge
"""
from __future__ import annotations
import base64
import json
import os
import sys
import urllib.parse
from pathlib import Path

_here = Path(__file__).resolve()
ROOT = _here.parents[2] if len(_here.parents) > 2 else _here.parent
PROJ = ROOT / "ontology" / "platform-self-model"  # only used for default paths; overridable via env
FRAGMENTS = Path(os.environ.get("SELFMODEL_FRAGMENTS", str(PROJ / "instances" / "fragments.json")))
SCHEMA_SQL = Path(os.environ.get("SELFMODEL_SCHEMA", str(PROJ / "persistence" / "arcadedb-schema.sql")))

URL = os.environ.get("ARCADEDB_URL", "http://localhost:2480").rstrip("/")
USER = os.environ.get("ARCADEDB_USER", "root")
PW = os.environ.get("ARCADEDB_PASSWORD", "")
DB = os.environ.get("DB_NAME", "knowledge")


class Arcade:
    """Minimal ArcadeDB REST client over httpx (mirrors backend-core/app/arcade.py)."""

    def __init__(self, url: str, user: str, pw: str):
        scheme = urllib.parse.urlparse(url).scheme.lower()
        if scheme not in ("http", "https"):
            raise ValueError(f"ARCADEDB_URL must be http(s), got scheme {scheme!r}")
        import httpx  # lazy: only the live load path needs a network client
        self._httpx = httpx
        auth = "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()
        self._client = httpx.Client(base_url=url, timeout=8.0,
                                    headers={"Authorization": auth, "Content-Type": "application/json"})

    def _post(self, path: str, payload: dict) -> list[dict]:
        r = self._client.post(path, json=payload)
        if r.is_error:
            raise self._httpx.HTTPStatusError(
                f"HTTP {r.status_code} on {path}: {r.text[:400]}", request=r.request, response=r)
        return r.json().get("result", []) if r.text else []

    def ready(self) -> bool:
        try:
            return self._client.get("/api/v1/ready", timeout=4.0).status_code in (200, 204)
        except Exception:
            return False

    def ensure_db(self, db: str):
        try:
            self._post("/api/v1/server", {"command": f"create database {db}"})
        except self._httpx.HTTPStatusError as e:
            if e.response.status_code not in (400, 409):  # already exists -> fine
                raise

    def cmd(self, db: str, sql: str, params: dict | None = None) -> list[dict]:
        return self._post(f"/api/v1/command/{db}",
                          {"language": "sql", "command": sql, "params": params or {}})


def build_plan() -> dict:
    frag = json.loads(FRAGMENTS.read_text(encoding="utf-8"))
    ns = frag["namespace"]
    # strip `-- ...` line comments BEFORE splitting on ';' (a comment may contain ';')
    raw = SCHEMA_SQL.read_text(encoding="utf-8")
    nocomment = "\n".join(line.split("--", 1)[0] for line in raw.splitlines())
    ddl = [s.strip() for s in nocomment.split(";") if s.strip()]

    vertex_cmds = []
    for v in frag["vertices"]:
        props = {"ontologyIri": v["iri"], "label": v["props"].get("name", v["id"])}
        props.update(v["props"])
        sets = ", ".join(f"{k} = :{k}" for k in props)
        vertex_cmds.append((f"UPDATE {v['type']} SET {sets} UPSERT WHERE ontologyIri = :ontologyIri", props))

    relator_cmds = []
    for r in frag["relators"]:
        props = {"ontologyIri": r["iri"], "label": r["id"]}
        props.update(r.get("props", {}))
        sets = ", ".join(f"{k} = :{k}" for k in props)
        relator_cmds.append((f"UPDATE {r['type']} SET {sets} UPSERT WHERE ontologyIri = :ontologyIri", props))
        relator_cmds.append((
            f"DELETE FROM (SELECT expand(outE('BINDS_ROLE')) FROM {r['type']} WHERE ontologyIri = :riri)",
            {"riri": r["iri"]}))
        for b in r["bindings"]:
            relator_cmds.append((
                "CREATE EDGE BINDS_ROLE "
                f"FROM (SELECT FROM {r['type']} WHERE ontologyIri = :riri) "
                "TO (SELECT FROM OntologyElement WHERE ontologyIri = :tiri) "
                "SET roleName = :role, ordinal = :ord",
                {"riri": r["iri"], "tiri": ns + b["target"], "role": b["role"], "ord": b["ordinal"]}))

    edge_cmds = []
    for e in frag.get("edges", []):
        edge_cmds.append((
            f"CREATE EDGE {e['type']} "
            "FROM (SELECT FROM OntologyElement WHERE ontologyIri = :f) "
            "TO (SELECT FROM OntologyElement WHERE ontologyIri = :t)",
            {"f": ns + e["from"], "t": ns + e["to"]}))

    return {"ddl": ddl, "vertices": vertex_cmds, "relators": relator_cmds, "edges": edge_cmds,
            "counts": {"ddl": len(ddl), "vertices": len(vertex_cmds),
                       "relator_ops": len(relator_cmds), "edges": len(edge_cmds)}}


def main() -> int:
    dry = "--dry-run" in sys.argv
    plan = build_plan()
    c = plan["counts"]
    print(f"plan: {c['ddl']} DDL stmts, {c['vertices']} vertex upserts, "
          f"{c['relator_ops']} relator ops, {c['edges']} binary edges")

    if dry:
        print("\n--dry-run: sample commands (not executed):")
        for label, key in [("DDL", "ddl"), ("VERTEX", "vertices"), ("RELATOR", "relators")]:
            sample = plan[key][0]
            print(f"  [{label}] {sample if isinstance(sample, str) else sample[0]}")
        print(f"\nTarget when live: {URL} db={DB} user={USER}")
        return 0

    try:
        arc = Arcade(URL, USER, PW)
    except ImportError:
        print("\nlive load needs httpx: python -m pip install httpx  (then re-run). "
              "--dry-run needs no deps.")
        return 3
    if not arc.ready():
        print(f"\nArcadeDB not reachable at {URL} (ready check failed).")
        print("Bring one up, then re-run `python tools/selfmodel/load.py`:")
        print("  local : start the docker engine, then `fleet_up arcadedb` (or docker run arcadedata/arcadedb -p 2480:2480)")
        print("  azure : set ARCADEDB_URL=http://arcadedb-<label>.<region>.azurecontainer.io:2480  (rg-arcadedb-test)")
        return 2

    print(f"connected: {URL} db={DB}")
    arc.ensure_db(DB)
    for stmt in plan["ddl"]:
        arc.cmd(DB, stmt)
    for sql, params in plan["vertices"] + plan["relators"] + plan["edges"]:
        arc.cmd(DB, sql, params)
    n = arc.cmd(DB, "SELECT count(*) AS n FROM OntologyElement")
    print(f"loaded. OntologyElement vertices in graph: {n[0]['n'] if n else '?'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
