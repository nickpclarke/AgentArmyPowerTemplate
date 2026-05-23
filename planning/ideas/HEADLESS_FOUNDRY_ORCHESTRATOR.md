# Headless Foundry Orchestrator

**Status:** Innovation Proposal  
**Date:** 2026-05-23  
**Proposed by:** Claude Code  
**Category:** Infrastructure Automation / AI-Driven DevOps  

---

## Executive Summary

Transform AgentArmy's infrastructure deployment from manual/workflow-driven to **fully autonomous AI-orchestrated**. A headless microVM running in Azure Container Apps continuously monitors infrastructure health, analyzes desired vs. current state, and makes intelligent decisions to trigger deployments, scale resources, and optimize costs—all without human intervention or console access.

**Vision:** Infrastructure that manages itself through AI decision-making.

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

1. **Autonomous vs. Approval-Gated**
   - Should orchestrator deploy to prod without human approval?
   - Or should it recommend (create HITL decision artifact)?
   - **Recommendation:** Start with recommendations → gradual autonomy

2. **Decision Confidence Threshold**
   - Deploy only if decision confidence > 80%?
   - Or more conservative (> 90%)?
   - **Recommendation:** 85% for staging, 95% for prod

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
| Runaway deployments | Medium | High | Deploy only if confidence > 95%, max 1 deploy/hour |
| Cost explosion (unintended scaling) | Medium | High | Scale-down only during office hours, manual approval for prod |
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

### Near-term (Next 2 months)
- [ ] Phase 1-3: Core orchestrator with observability
- [ ] GitHub Projects integration (log decisions as items)
- [ ] Slack notifications of major decisions

### Mid-term (Months 2-4)
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
- **Make decisions from iPhone** — Foundry models reason about infrastructure
- **Autonomous execution** — AI makes decisions you approve async
- **Audit trail** — Everything logged and queryable

**Example workflow from iPhone:**
1. Notification: "Orchestrator detected API latency spike"
2. Review in Azure Portal/Log Analytics
3. Approve/reject proposed deployment (or let it auto-approve if confidence > threshold)
4. Monitor deployment progress in GitHub Actions
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

- [azure-deploy-pipeline.yml](.github/workflows/azure-deploy-pipeline.yml) — Current CI/CD pipeline
- [api-validator.py](api-validator.py) — Infrastructure health checking
- [main.bicep](infra/main.bicep) — Infrastructure-as-Code definition
- [HITL Decision Pattern](../meta/hitl_system.md) — Human-in-the-loop decisions
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
**Stakeholder Input Needed:** Yes (autonomy level, approval requirements)
