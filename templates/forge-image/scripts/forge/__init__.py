"""agentarmy-forge — fleet code generator.

Reads an ontology (YAML model, or RDF/OWL: Turtle / JSON-LD / N-Triples) from
any of three sources — backend-core's /ontology/snapshot HTTP endpoint, a
local file, or an Azure Blob URI — and emits typed source files for any
combination of the three application-tier spokes (C#, TypeScript, Python).

Phases (per ARC-ADR-029):
  v0 — YAML in, C# out (lift-and-shift middle-core modelgen)
  v1 — RDF parsers + multi-source input + FastAPI server + HMAC webhook
  v2 — TypeScript + Python emitters
  v3 — DEFERRED (binary builds / artifact publishing)
"""

__version__ = "0.1.0"
