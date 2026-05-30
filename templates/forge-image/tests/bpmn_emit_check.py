"""Verifies the §process loop docker-free: ontology IR (with a `processes` block) → forge
BPMN emit → the runbook-orchestrator kernel's OWN validator accepts it (ARC-ADR-031 Q5).

Runnable directly (`python bpmn_emit_check.py`) or via pytest. Uses pyyaml + defusedxml,
both shipped in the forge / runbook images.
"""
from __future__ import annotations

import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_FORGE_SCRIPTS = os.path.abspath(os.path.join(_HERE, "..", "scripts"))
_RUNBOOK_SCRIPTS = os.path.abspath(
    os.path.join(_HERE, "..", "..", "runbook-orchestrator-image", "scripts")
)
for _p in (_RUNBOOK_SCRIPTS, _FORGE_SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from forge.emitters import bpmn, cacao   # noqa: E402
from forge.parsers import yaml_parser    # noqa: E402
import validators                        # noqa: E402  (runbook-orchestrator kernel)

_SAMPLE = """
version: "1.0.0"
namespace: "AgentArmy.Demo"
objectTypes: []
processes:
  - id: ingest-and-review
    name: Ingest and Review
    trigger: { kind: message, subject: fleet.knowledge.dropped }
    steps:
      - { name: analyze, kind: service, agent: knowledge-synthesizer, next: [severity] }
      - { name: severity, kind: decision, condition: "${level == 'HIGH'}", next: [escalate, log] }
      - { name: escalate, kind: service, agent: hitl-coordinator, next: [done-escalated] }
      - { name: log, kind: emit-event, subject: fleet.knowledge.logged, next: [done-logged] }
      - { name: done-escalated, kind: end }
      - { name: done-logged, kind: end }
"""


def test_forge_bpmn_validates_in_kernel() -> None:
    model = yaml_parser.parse(_SAMPLE, source_uri="sample.yaml")
    assert [p.id for p in model.processes] == ["ingest-and-review"]

    with tempfile.TemporaryDirectory() as out_dir:
        written = bpmn.emit(model, out_dir)
        assert written == ["ingest-and-review.bpmn"], written
        with open(os.path.join(out_dir, written[0]), encoding="utf-8") as fh:
            xml = fh.read()

    # The kernel's OWN validator must accept the emitted file — the loop's proof.
    errors = validators.validate_bpmn(xml)
    assert errors == [], errors

    # Dialect spot-checks the kernel keys on.
    assert '<process id="ingest-and-review"' in xml
    assert "messageEventDefinition" in xml
    assert "exclusiveGateway" in xml
    assert 'default="sf-severity-log"' in xml


def test_forge_cacao_validates_in_kernel() -> None:
    import json

    model = yaml_parser.parse(_SAMPLE, source_uri="sample.yaml")
    with tempfile.TemporaryDirectory() as out_dir:
        written = cacao.emit(model, out_dir)
        assert written == ["ingest-and-review.cacao.json"], written
        with open(os.path.join(out_dir, written[0]), encoding="utf-8") as fh:
            obj = json.loads(fh.read())

    # The kernel's OWN CACAO validator must accept the emitted playbook.
    errors = validators.validate_cacao(obj)
    assert errors == [], errors
    assert obj["type"] == "playbook" and obj["spec_version"] == "cacao-2.0"
    assert obj["workflow"]["severity"]["type"] == "if-condition"


if __name__ == "__main__":
    test_forge_bpmn_validates_in_kernel()
    test_forge_cacao_validates_in_kernel()
    print("forge bpmn_emit_check: OK (BPMN + CACAO)")
