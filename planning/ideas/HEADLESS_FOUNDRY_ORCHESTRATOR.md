# Headless Foundry Orchestrator

**Status:** Innovation Proposal (governance-aligned revision)  
**Date:** 2026-05-23  
**Proposed by:** Claude Code  
**Category:** Infrastructure Automation / AI-Driven DevOps  

---

## Executive Summary

Transform AgentArmy's infrastructure deployment from manual/workflow-driven to **fully autonomous AI-orchestrated**. A headless microVM running in Azure Container Apps continuously monitors infrastructure health, analyzes desired vs. current state, and makes intelligent decisions to trigger deployments, scale resources, and optimize costs—autonomously for low-risk dev/staging changes, and by surfacing production changes as Decision Artifacts for human sign-off (no standing console access required).

**Vision:** Infrastructure that manages itself through AI decision-making — *within the army's existing governance, not around it.*

---

## Scope (v1)

**In scope:**
- Read-only health + drift detection across dev/staging/prod (via `api-validator.py` + Azure resource state)
- Autonomous, reversible actions in **dev/staging only**, behind guardrails (dry-run default, max 1 deploy/hr)
- Prod handled by **recommendation → Decision Artifact** via `hitl-coordinator` (no self-approval)
- Structured decision logging to Log Analytics (ARMY_PRINCIPLES #7)

**Out of scope for v1** (revisit once a track record exists, gated by an ADR):
- Autonomous prod deploys
- Foundry/LLM-driven decisions (Phase 4) — rule-based engine only in v1
- Cost-driven auto-scale-down
- Multi-region / cross-landscape orchestration, predictive scaling, federated decision-making

---

## Problem Statement

**Current State:**
- Infrastructure deployments triggered manually via GitHub Actions or CI/CD events
- Infrastructure decisions require human approval (scaling, rollback, optimization)
- No continuous monitoring of infrastructure drift or optimization opportunities
- Scaling and cost optimization are reactive, not proactive

**Opportunity:**
- Autonomous orchestrator makes deployment decisions 24/7
- Infrastructure continuously analyzes its own health and evolves
- Foundry AI models make intelligent decisions about resource allocation
- Enables multi-environment (dev/staging/prod) self-management

---

## Proposed Solution

### Architecture

```
Azure Container Apps Environment
├── agentarmy-app (deployed application)
├── foundry-orchestrator (NEW - autonomous manager)
└── api-validator (healthcheck script)

Foundry Orchestrator Loop (runs hourly or event-driven):
  1. Check infrastructure health (via api-validator.py)
  2. Analyze Azure resource state (via Azure CLI/SDK)
  3. Compare against desired state (Bicep templates)
  4. Make intelligent decisions:
     - Deploy/update infrastructure
     - Scale resources up/down
     - Optimize costs
     - Trigger rollbacks
  5. Execute decision via GitHub Actions API
  6. Monitor deployment progress
  7. Log results to Azure Monitor (observable, queryable)
```

### Key Innovations

1. **Managed Identity Authentication**
   - Zero credentials stored in code
   - Uses Azure Managed Identity for auto-auth
   - GitHub PAT stored only in Key Vault
   - Headless = no credential management

2. **Autonomous Decision-Making**
   - Continuous infrastructure health monitoring
   - Drift detection (manual changes vs. desired state)
   - Cost-optimized scaling (scale down off-peak, up at peak)
   - Intelligent rollback on degradation

3. **Multi-Environment Awareness**
   - Same orchestrator manages dev/staging/prod
   - Environment-specific parameters via Bicep
   - Isolated decision logic per environment
   - Cross-environment optimization (e.g., promote from staging→prod)

4. **Observable & Auditable**
   - All decisions logged to Azure Log Analytics
   - Full decision reasoning captured
   - GitHub Actions workflow visible as execution record
   - Infrastructure changes tracked in git history

---

## Governance Alignment (ARMY_PRINCIPLES + HITL)

The orchestrator is an autonomous actor in the army, so it inherits the army's governance model. It is **not** a license to bypass human judgment — it is a faster, always-on path *to* the existing decision surface.

### Autonomy boundary: act vs. escalate

| Environment | Action class | Behavior |
|---|---|---|
| dev / staging | Reversible, low-cost (drift correction, scale within budget, dry-run) | **Act autonomously** within guardrails, then log + feed back |
| prod | Any deploy, spend-increasing scale-up, rollback | **Emit a Decision Artifact** via `hitl-coordinator` — do not self-approve |
| any | A failure it cannot resolve | **Escalate to `error-coordinator`** (no unbounded retries) |

This replaces "deploy to prod if confidence > 95%". In v1 the orchestrator never self-approves a prod change; high confidence shortens the human's review, it does not remove the human. Production autonomy is *earned* incrementally (see Roadmap), unlocked by an explicit ADR — not flipped on by a threshold.

### Mapping to the 7 principles

| Principle | How the orchestrator complies |
|---|---|
| **1. Error Escalation** | On deploy failure, API-unreachable, auth error, or unknown Azure state, it calls `error-coordinator` instead of retrying blindly. Directly mitigates the "runaway deployments" risk. |
| **2. Knowledge Feedback** | After each run it feeds outcomes (decision → result, false-positive rate, cost delta) to `knowledge-synthesizer` so decision rules improve over time. |
| **3. Skill Scaffolding** | Exposes `health-check`, `analyze-state`, and `propose-deployment` as composable, structured-output skills other agents/workflows can call. |
| **4. Hook Integration** | Event-driven runs are triggered by infra/CI lifecycle events, not only a polling timer. |
| **5. Delegation Direction** | Delegates DOWN/ACROSS only — to `error-coordinator` (escalation) and `hitl-coordinator` (decision surfacing). It never self-approves a prod action. |
| **6. MECE** | Owns *infrastructure deploy/scale decisioning*. It does **not** author HITL issues itself — it hands context to `hitl-coordinator`, which owns Decision Artifacts; and it does **not** implement Bicep changes — it triggers the existing pipeline. |
| **7. Observable Decisions** | Every decision is logged in the army's structured format (`timestamp, agent, decision_type, decision, reasoning, confidence`) to Log Analytics — the JSON in Phase 3 already matches this. |

### Decision Artifacts instead of self-approval (prod)

When the orchestrator concludes prod needs a change, it does **not** call the GitHub Actions API directly. It hands context to `hitl-coordinator`, which creates a Decision Artifact (`Type: Decision`, `hitl-decision` label, `Status: Awaiting Decision`) on the GitHub Projects board. The orchestrator's analysis JSON maps cleanly onto the artifact template:

| Orchestrator field | Decision Artifact section |
|---|---|
| `analysis` | Context |
| candidate strategies | Options |
| `recommended_action` + `decision_confidence` | Agent Recommendation |
| `decision_reasoning` | Impact of Each Option |
| affected resources | Blocks |

The orchestrator's calls map onto the HITL decision-type taxonomy: a prod deploy is **Risk Acceptance**, a spend-increasing scale-up is **Budget/Capacity**, and a change needing explicit authorization is a **Security Gate**. A human (or AI app) comments + closes the artifact, the existing HITL automation unblocks the work, and the orchestrator executes the approved action.

---

## Implementation Approach

### Phase 1: Core Orchestrator (Week 1)

**Deliverable:** Headless microVM that monitors and reports

**Files to Create:**
- `foundry-orchestrator.py` — Main orchestrator loop
  - `check_infrastructure_health()` — runs api-validator
  - `analyze_infrastructure_state()` — fetches current Azure resources
  - `make_deployment_decision()` — logic for when to deploy
  - `trigger_github_deployment()` — calls GitHub Actions API
  - `monitor_deployment_progress()` — polls GitHub workflow status

- `Dockerfile` — Container image for orchestrator
  - Base: `python:3.11-slim`
  - Pre-installed: Azure CLI, Python dependencies
  - Entrypoint: `foundry-orchestrator.py`

- `.azure/container-app-foundry.bicep` — Infrastructure for orchestrator
  - Azure Container Apps deployment config
  - Managed Identity assignment
  - Environment variables and Key Vault bindings
  - Log Analytics integration

**Deployment:**
```bash
# Build and push to ACR
az acr build --registry agentarmy-acr --image foundry-orchestrator:v1 --file Dockerfile .

# Deploy to Container Apps
az containerapp create --name foundry-orchestrator --environment agentarmy-prod-env \
  --system-assigned-identity --cpu 0.5 --memory 1Gi
```

**Testing:**
- Manual invocation: `az containerapp up` in debug mode
- Check logs in Log Analytics: `orchestrator | search "orchestrator"`
- Verify GitHub API connectivity (test with dry-run flag)

---

### Phase 2: Decision Logic (Week 2)

**Deliverable:** Intelligent deployment decisions

**Enhancement to `foundry-orchestrator.py`:**

```python
class DeploymentDecisionEngine:
    """Intelligent logic for when/how to deploy"""
    
    def should_deploy(self, analysis: dict) -> Tuple[bool, str]:
        """Determine if deployment is needed"""
        # Decision factors:
        # - Infrastructure drift detected
        # - API health degraded
        # - Resource scaling needed
        # - Scheduled maintenance window
        # - Cost optimization opportunity
        
    def select_deployment_strategy(self) -> str:
        """Choose deployment approach"""
        # Options:
        # - Full redeploy (infrastructure changed)
        # - Scale-only (adjust replicas/throughput)
        # - Targeted update (specific resource)
        # - Rollback (previous version)
        
    def estimate_deployment_risk(self) -> float:
        """Calculate risk score (0-1)"""
        # Consider:
        # - Change magnitude
        # - Current traffic load
        # - Infrastructure utilization
        # - Recent failure history
```

**Deployment Strategies:**
- **Drift Correction:** Current state ≠ desired state → trigger Bicep redeploy
- **Auto-Scale:** API latency > threshold → increase replicas/throughput
- **Cost Optimization:** Off-peak hours → scale down resources
- **Health Recovery:** API failures > threshold → rollback to previous version
- **Scheduled Maintenance:** Deploy updates during low-traffic windows

**Testing:**
- Simulate infrastructure drift (manually change Azure resource)
- Verify orchestrator detects and recommends redeploy
- Test scaling triggers (simulate high load)
- Verify rollback logic (manually break an API)

---

### Phase 3: Observability & Reporting (Week 3)

**Deliverable:** Full visibility into orchestrator decisions and actions

**Add to orchestrator:**
- Structured logging with decision context
- Metrics export to Azure Monitor (decisions/hour, deployment success rate)
- Decision audit log (what decision was made, why, with what confidence)
- PR comments showing orchestrator activity (like existing validation reports)
- Dashboard in Azure Portal showing:
  - Recent orchestrator decisions
  - Deployment frequency
  - Infrastructure health trends
  - Cost savings attribution

**Example Log Output:**
```json
{
  "timestamp": "2026-05-23T10:30:00Z",
  "agent": "foundry-orchestrator",
  "decision_type": "Budget/Capacity",
  "orchestrator_run_id": "orch-20260523-103000",
  "phase": "decision",
  "analysis": {
    "infrastructure_health": "degraded",
    "api_failures": 3,
    "api_latency_ms": 2500,
    "cosmos_throughput_utilization": 95,
    "container_app_cpu_usage": 78
  },
  "decision": "deploy",
  "decision_reasoning": [
    "API failures detected (3 in last 5 min)",
    "Cosmos DB throughput near limit (95%)",
    "Latency above threshold (2500ms > 1000ms target)"
  ],
  "decision_confidence": 0.92,
  "recommended_action": "scale_cosmos_db",
  "deployment_triggered": true,
  "github_workflow_run_id": 12345678
}
```

---

### Phase 4: Foundry Integration (Future)

**Deliverable:** AI model-driven decisions (not just rule-based)

**Enhancement:** Replace simple decision rules with Foundry API calls:
```python
def make_intelligent_decision(self, analysis: dict) -> dict:
    """Use Foundry to reason about infrastructure decisions"""
    
    prompt = f"""
    Current Infrastructure State:
    {json.dumps(analysis, indent=2)}
    
    Available Actions:
    1. Deploy full infrastructure update
    2. Scale Cosmos DB throughput up
    3. Scale Container App replicas up
    4. Scale Container App replicas down
    5. Rollback to previous version
    6. Do nothing
    
    Provide your reasoning and recommended action.
    """
    
    response = foundry_client.complete(
        model="grok-4.2-reasoning",
        prompt=prompt,
        temperature=0.2  # Lower temp = more deterministic
    )
    
    return {
        "recommended_action": response.action,
        "confidence": response.confidence_score,
        "reasoning": response.reasoning
    }
```

---

## Files to Create/Modify

### New Files
```
foundry-orchestrator/
├── foundry-orchestrator.py          (main orchestrator loop)
├── Dockerfile                       (container image)
├── requirements.txt                 (Python dependencies)
├── config/
│   ├── decision-rules.yaml         (deployment decision thresholds)
│   └── environments.yaml           (per-environment orchestrator config)
└── tests/
    ├── test_orchestrator.py
    ├── test_decision_engine.py
    └── test_github_integration.py

.azure/
└── container-app-foundry.bicep     (infrastructure for orchestrator)

planning/ideas/
└── HEADLESS_FOUNDRY_ORCHESTRATOR.md (this document)
```

### Modified Files
```
.github/workflows/
└── azure-deploy-pipeline.yml       (add GitHub PAT to Key Vault injection)

infra/
└── main.bicep                      (add Container App for orchestrator)
```

---

## Decision Points & Approvals

### Critical Decisions Needed

1. **Autonomous vs. Approval-Gated** — *resolved (see [Governance Alignment](#governance-alignment-army_principles--hitl))*
   - **Decided:** prod changes emit a Decision Artifact via `hitl-coordinator`; dev/staging act autonomously within guardrails. No threshold self-approves prod in v1.
   - Increasing prod autonomy is a separate, ADR-gated decision once a track record exists.

2. **Decision Confidence Threshold**
   - In dev/staging, act autonomously only if confidence > 85%; below that, emit a Decision Artifact instead.
   - In prod, confidence never authorizes action on its own — it only informs the human's review on the Decision Artifact.

3. **Deployment Frequency**
   - Check infrastructure every hour? Every 5 minutes?
   - Risk of thrashing if too frequent
   - **Recommendation:** Hourly checks + event-driven (API health alerts)

4. **Rollback Strategy**
   - Auto-rollback on deployment failure?
   - Or manual rollback to git-tagged version?
   - **Recommendation:** Auto-rollback with alerting

5. **Cost Optimization Scope**
   - Allow scale-down during off-peak?
   - Risk of unplanned downtime
   - **Recommendation:** Scale-down only if within business hours (start conservative)

---

## Success Criteria

### Phase 1 (Core Orchestrator)
- [ ] Orchestrator runs in Container Apps without errors
- [ ] Successfully detects infrastructure health via api-validator
- [ ] Can parse Azure resource state
- [ ] Logs all decisions to Log Analytics
- [ ] GitHub API integration works (dry-run mode)

### Phase 2 (Decision Logic)
- [ ] Decision engine makes correct deployment recommendations
- [ ] Detected infrastructure drift correctly
- [ ] Correctly identifies when scaling is needed
- [ ] No false-positive deployments (>95% precision)

### Phase 3 (Observability)
- [ ] All decisions logged with full context
- [ ] Audit trail queryable in Log Analytics
- [ ] Azure Monitor dashboard shows orchestrator activity
- [ ] PR comments show orchestrator involvement

### Phase 4 (Production Ready)
- [ ] 30 days running without human intervention
- [ ] Cost savings demonstrable (attribution to orchestrator decisions)
- [ ] Zero unplanned downtime caused by orchestrator
- [ ] All decisions explainable and auditable

---

## Timeline & Effort

| Phase | Duration | Effort | Blockers |
|-------|----------|--------|----------|
| Phase 1: Core | 1 week | 2 developer-days | None |
| Phase 2: Decision Logic | 1 week | 2 developer-days | API thresholds tuning |
| Phase 3: Observability | 1 week | 1 developer-day | Log Analytics schema |
| Phase 4: Foundry Integration | 2 weeks | 3 developer-days | Foundry API access |

**Total:** ~4 weeks to production-ready (if done sequentially)  
**Fast-track:** ~2 weeks (Phase 1 + 2 in parallel, Phase 3 post-launch)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Runaway deployments | Medium | High | Prod gated behind a Decision Artifact (no self-approval); dev/staging capped at 1 deploy/hr; failures escalate to `error-coordinator` (Principle 1) |
| Cost explosion (unintended scaling) | Medium | High | Prod spend changes routed through a Decision Artifact (Budget/Capacity type); dev/staging scale-down disabled in v1 (out of scope) |
| Orchestrator itself crashes | Low | High | Use Managed Identity (built-in recovery), Container Apps auto-restart |
| GitHub API rate limit exceeded | Low | Medium | Check GitHub rate limits before deploy, implement backoff |
| Infrastructure drift undetected | Low | Medium | Run health checks every 5 min, automated tests |
| Foundry API latency impacts decisions | Medium | Low | Cache Foundry responses, use rule-based fallback |

---

## Testing Strategy

### Unit Tests
- Decision engine logic (when should deploy?)
- Azure resource parsing
- GitHub API mock responses

### Integration Tests
- Full orchestrator run against staging environment
- Simulate infrastructure drift
- Simulate API health degradation
- Verify GitHub Actions triggered correctly

### Chaos Engineering
- Kill Container App → verify auto-restart
- Manually change Azure resources → verify drift detection
- Disable API keys → verify graceful failure
- Simulate GitHub API downtime

### Dry-Run Mode
- Orchestrator runs normally but doesn't call GitHub API
- Logs decisions without executing
- Test decision logic against real infrastructure

---

## Roadmap & Future Enhancements

> The items below are the **earned-autonomy path**. Everything past v1 (see [Scope](#scope-v1)) ships only after a track record exists, and the step from "recommend prod" to "act on prod" is gated by an explicit ADR — not a roadmap checkbox.

### Near-term (Next 2 months) — v1
- [ ] Phase 1-3: Core orchestrator with observability (dev/staging autonomous, prod recommend-only)
- [ ] HITL integration: prod recommendations land as Decision Artifacts via `hitl-coordinator`
- [ ] Slack notifications of major decisions

### Mid-term (Months 2-4)
- [ ] **ADR: graduate selected prod actions to autonomous** (precondition for everything below)
- [ ] Phase 4: Foundry integration for intelligent decisions
- [ ] Multi-region orchestration (orchestrate across multiple Azure regions)
- [ ] Cost attribution (show which orchestrator decisions saved money)
- [ ] A/B testing of decision strategies

### Long-term (4+ months)
- [ ] Cross-landscape orchestration (manage multiple AgentArmy instances)
- [ ] Predictive scaling (forecast demand and pre-scale)
- [ ] Self-healing infrastructure (detect and fix common issues automatically)
- [ ] Federated decision-making (multiple orchestrators coordinate)

---

## How This Enables the "iPhone Version"

The headless orchestrator means:
- **No console access needed** — runs entirely in the cloud
- **Check status from anywhere** — Azure Portal, Log Analytics, GitHub
- **Approve from your phone** — prod changes arrive as Decision Artifacts on the GitHub Projects board; comment + close to approve, exactly like any HITL decision. The board *is* the mobile approval surface — no bespoke app needed.
- **Autonomous execution where safe** — dev/staging changes apply themselves within guardrails; prod waits for your call
- **Audit trail** — Everything logged and queryable

**Example workflow from iPhone:**
1. GitHub notification: a Decision Artifact was assigned to you ("Orchestrator detected API latency spike → recommend scale Cosmos DB")
2. Open the issue — Context, Options, and the orchestrator's recommendation are self-contained
3. Approve or reject by commenting + closing (the same HITL flow humans already use)
4. HITL automation unblocks the work; orchestrator triggers the deploy and monitors GitHub Actions
5. Get notification when complete

---

## Questions for Stakeholders

1. **Comfort level:** How much do we trust autonomous deployments to prod?
2. **Decision confidence:** What threshold should unlock production auto-deploy?
3. **Cost optimization:** Can we scale down resources during off-peak hours?
4. **Scope:** Start with staging/dev only, or include production?
5. **Approval gates:** Should orchestrator recommendations go through HITL for prod?

---

## References & Related Documents

- [azure-deploy-pipeline.yml](../../.github/workflows/azure-deploy-pipeline.yml) — Current CI/CD pipeline
- [api-validator.py](../../api-validator.py) — Infrastructure health checking
- [main.bicep](../../infra/main.bicep) — Infrastructure-as-Code definition
- [HITL Decision Pattern](../../docs/hitl.md) — Human-in-the-loop decisions
- [hitl-coordinator agent](../../.claude/agents/categories/09-meta-orchestration/hitl-coordinator.md) — Creates Decision Artifacts on the board
- [ARMY_PRINCIPLES](../meta/principles/ARMY_PRINCIPLES.md) — Governance principles

---

## Next Steps

### Immediate (This Sprint)
- [ ] Get stakeholder feedback on vision and autonomy level
- [ ] Review decision-making thresholds and logic
- [ ] Assign Phase 1 implementation

### This Week
- [ ] Create orchestrator.py skeleton
- [ ] Write Dockerfile
- [ ] Set up Container App infrastructure
- [ ] Test orchestrator in dry-run mode

### Following Week
- [ ] Implement decision engine
- [ ] Deploy to staging environment
- [ ] Test against real infrastructure
- [ ] Add observability

---

**Status:** Ready for discussion / technical spike  
**Owner:** TBD  
**Stakeholder Input Needed:** Yes — v1 autonomy model is resolved (dev/staging autonomous, prod via Decision Artifact); open question is the *earned-autonomy ADR* for graduating prod actions later.
