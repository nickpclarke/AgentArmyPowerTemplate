"""Proposers feed the sift engine. The engine doesn't care where fragments come
from — a fixture file (deterministic, offline doctor) or the live Cerebras gateway.
ARC-ADR-032 facet: the LLM only proposes; the formal layer decides."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


class FixtureProposer:
    """Loads pre-baked IR fragments from fixtures/proposals/*.json. repair() returns
    None — a static fixture can't repair itself — so violating fixtures QUARANTINE.
    That is exactly the property the doctor proves: nothing unproven is promoted."""

    name = "fixture"

    def __init__(self, proposals_dir: Path):
        self.dir = Path(proposals_dir)

    def load(self, names: list[str] | None = None) -> list[dict]:
        frags = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(self.dir.glob("*.json"))]
        if names:
            frags = [f for f in frags if f.get("fragment_id") in names]
        return frags

    def repair(self, fragment: dict, violations: list[str]):  # noqa: ARG002
        return None

    def prompt_hash(self, fragment: dict) -> str:
        digest = hashlib.sha256(json.dumps(fragment, sort_keys=True).encode()).hexdigest()
        return "fixture:" + digest[:12]


class GatewayProposer:
    """Live proposer — calls the backend-core llm-gateway (ARC-ADR-021) with Cerebras
    and a json_schema response_format so the model emits IR fragments DIRECTLY (not
    prose), then repairs by feeding the structured violation report back. Not
    exercised by the offline doctor; this documents the production call shape the
    backend-core service uses. Needs LLM_GATEWAY_URL (+ a bearer token)."""

    name = "cerebras-gateway"

    def __init__(self, base_url: str | None = None, model: str = "llama-3.3-70b",
                 token: str | None = None, schema: dict | None = None):
        self.base_url = (base_url or os.environ.get("LLM_GATEWAY_URL", "")).rstrip("/")
        self.model = os.environ.get("CEREBRAS_MODEL", model)
        self.token = token or os.environ.get("LLM_GATEWAY_TOKEN", "")
        self.schema = schema

    def _chat(self, messages: list[dict]) -> dict:
        import urllib.request
        from urllib.parse import urlparse
        url = self.base_url + "/v1/chat/completions"
        # Scheme allowlist: only the operator-configured http(s) gateway is
        # reachable. base_url comes from LLM_GATEWAY_URL (operator config), never
        # from request/user data — this blocks file:// and other scheme abuse.
        if urlparse(url).scheme not in ("http", "https"):
            raise ValueError(f"refusing non-http(s) gateway URL: {url!r}")
        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "ir_fragment", "schema": self.schema, "strict": True},
            },
        }).encode()
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"},
        )
        # nosemgrep — URL is scheme-guarded above and operator-configured (env), not request data.
        with urllib.request.urlopen(req, timeout=60) as resp:  # nosemgrep
            payload = json.loads(resp.read())
        return json.loads(payload["choices"][0]["message"]["content"])

    def propose(self, source_text: str) -> list[dict]:
        if not self.base_url:
            raise RuntimeError("LLM_GATEWAY_URL not set — GatewayProposer needs the live gateway")
        system = (
            "You are an ontology extractor. Propose entities and reified relations from the "
            "text, each classified under BOTH a gUFO stereotype and a BFO class, citing source "
            "character spans. Stay inside the provided vocabulary. Emit ONLY the IR fragment JSON."
        )
        return [self._chat([{"role": "system", "content": system},
                            {"role": "user", "content": source_text}])]

    def repair(self, fragment: dict, violations: list[str]):
        if not self.base_url:
            return None
        system = (
            "Repair this ontology IR fragment so it conforms. Fix ONLY what the violations "
            "require: reclassify stereotypes, reify relations with >=2 distinct role bindings, "
            "and make the gUFO and BFO classifications agree. Emit ONLY the corrected JSON."
        )
        msg = json.dumps({"fragment": fragment, "violations": violations})
        return self._chat([{"role": "system", "content": system},
                           {"role": "user", "content": msg}])

    def prompt_hash(self, fragment: dict) -> str:  # noqa: ARG002
        return f"{self.name}:{self.model}"
