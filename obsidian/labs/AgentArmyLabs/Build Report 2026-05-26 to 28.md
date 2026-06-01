---
tags: [report, platform, build-log]
track: platform
date: 2026-05-28
---
# 🧱 Build Report — 2026-05-26 → 28

**🗺 [[Architecture Atlas — Conceptual to Contract]] · 🧭 [[Platform Atlas]]**

> [!abstract] Scale
> ~**60 PRs** merged to the hub `main` in ~2.5 days, plus a **new standalone repo** (`nickpclarke/agentarmy-forge`) and spoke-side merges. Eight major initiatives shipped; ~10 ADRs authored. Evidence = merged PR numbers; status marked ✅ live / ◐ partial / ⏳ in flight.

## 1. Fleet container architecture — tiering + the image fleet
The structural backbone the rest hangs on.
- **ARC-ADR-023 container tiering** (Platform / Application / Function) — #211; schema + heartbeat tier-report (#213); hub owns the platform deploy lane (#214).
- **`templates/local-stack/`** unified docker-compose for the data platform (#210).
- **The Image Standard** — every image = `image.json` + schema + `agentarmy-doctor` + `setup.sh`/doctor.
- **5 function-tier images scaffolded** (#278) then implemented with passing doctors: otel-collector (#285), local-embedder (#286), jwt-introspect (#287), hmac-verify (#288), schema-migrator (#289); plus event-bridge.
- **Status:** ✅ on `main`; 13 image manifests inventoried by the heartbeat.

## 2. agentarmy-forge — ontology→code generator
- **v0+v1+v2** (#295): IR + YAML/RDF parsers + C#/TS/Python emitters + FastAPI server + pr_opener + 7-check doctor. 6 security findings fixed during the build.
- **[[ARC-ADR-029]] → standalone repo (Option 1b)** — extracted to `nickpclarke/agentarmy-forge` with its own CI; hub keeps a frozen mirror + tiering governance (#298, #301, #308).
- **XC-11 forge control API** — OpenAPI spec + live Postman mock (#300, #302).
- **ARC-ADR-030** — data→ontology ingestion pipeline (backend-core service, Proposed) + contracts BE-7/BE-8/BE-9/BE-10; **BE-8 ingest seam decided** (multipart **and** JSON-`{uri}`).
- **Status:** ✅ merged + accepted + relocated. Open: Rust emitter (#305), backend-core BE-7/BE-8 producers (#120/#121).

## 3. Runbook orchestrator — security automation
- **ARC-ADR-031 + #315** — automated **BPMN 2.0 + OASIS CACAO 2.0** runbook engine (shared-IR kernel, SafeExecutor, NATS dispatcher, control API). v1 scoped safe (no real shell exec / timers / JWS).
- **Live-validated 4/4** on a real Docker host (`fleet.siem.phishing → runbook runs → fleet.runbook.completed`); fixed port-coexistence with the running fleet.
- **ARC-ADR-031 Accepted** (#320); **CI workflow** open for review (#321).
- **Status:** ✅ merged + accepted + proven. Open: #321 (CI), #316 (pytest, copilot).

## 4. untool fleet suite — cloud-agent → local Docker control plane
- **Local-fleet MCP server** (Phase 1, #253) — observe/drive the local Docker fleet without exposing the socket.
- **Security:** CF Access edge enforcement (#259), multi-token bearer registry + per-agent identity/revocation (#258), CF Access Managed OAuth (#276), read-only auto-approve (#272).
- **`fleet_inspect_all`** batch tool (#277); operating manual + branding (#255, #268).
- **Auto-enrolling allowlist** (#310/#312) — new fleet members get MCP access the moment their `image.json` merges; fixed the docker-tier gate.
- **Status:** ✅ live; external via `mcp.untool.ai` behind CF Access service tokens.

## 5. Health monitoring
- **WSL/Docker storage + uptime monitor** (#309) — probe→grade→alert→remediate; safe auto-remediation (dangling prune only, no `-a`/volumes).
- **Alerting:** ntfy (live + tested) + Twilio SMS (#314) → pivoted to **WhatsApp** (#318) after US A2P 10DLC blocked SMS; PS-5.1 installer fixes (#313).
- **Status:** ◐ code merged + ntfy live. Operator steps pending: WhatsApp sandbox join + elevated scheduled-task install. Twilio token moved to env-only (security review).

## 6. Observability, security & ops hardening
- **Platform Maturity Audit ([[ARC-ADR-024]])** — 8-agent audit (#215); run-vs-design segregation.
- **OTel Collector + Application Insights** Bicep (#235); heartbeat OTel-readiness / DORA / SLO / contract-skew (#227, #229).
- **Supply chain:** Trivy CVE gate + CycloneDX SBOM + digest-pinned bases (#233).
- **Secrets:** rotation policy (#230) + KV-as-source-of-truth tooling (#248) + heartbeat `--secrets` staleness (#231).
- **Azure budget** module + 50/75/90/100% alerts (#228).

## 7. Contracts, ADRs & architecture
- **LLM gateway** (ARC-ADR-021, #203) · **agent gateway A2A+MCP** (ARC-ADR-028, #279) · event bus bridges (ADR-022).
- **Data Vault 2.1 adoption** — strategy + agent team + toolkit (#271).
- **[[Architecture Atlas — Conceptual to Contract]]** (L0→L4, #299) — conceptual→contract EA views, 7 validated diagrams.
- Contract backlog + registry expansion; Tavily upstream vendoring pattern (#245).

## 8. Fleet automation & DX
- **fleet-heartbeat** gained `--disk` (#237), `--secrets`, `--dora`, `--slo`, OTel/contract-skew; bug fixes (#208, #254).
- **`new-spoke.sh`** scaffolder (#234); **dev tunnel + log multiplexer** (#253).
- **CLAUDE.md** slimmed under 40k (#275); agent descriptions compressed (#243); `/ea-adr` routing fix (#251); environments registry (#242) + getting-started guide (#241).

---

## Incident recovery (2026-05-28)
- **Docker dead** → root-caused to a clobbered `.wslconfig` (`swap=2048` + trailing whitespace → swap.vhdx failure → `HCS_E_CONNECTION_TIMEOUT`). Cleaned it; engine back in ~8s; 18 images / 10 containers intact. (~220 GB WSL disk recovered earlier in the window.)

## Hub-owner decisions (2026-05-28)
forge → standalone repo · BE-8 ingest = multipart **and** JSON-`{uri}` · ARC-ADR-029 + ARC-ADR-031 accepted · keep 4 GB WSL alloc · WhatsApp over SMS.

## Open / in flight
- #321 (runbook CI — review) · #305 (forge Rust emitter) · backend-core #120/#121 (BE-7/BE-8) · #316 (runbook pytest, copilot) · health WhatsApp join + scheduled-task install (operator).

---

Related: [[Architecture Atlas — Conceptual to Contract]] · [[Platform Atlas]] · [[L4 — Contract-Flow Graph]] · [[Model-Driven Platform]]
