# Lifecycle Promotion Template

Use this template when a platform or spoke workload repository needs full lifecycle CI/CD rather than a single smoke workflow.

Do not apply this lifecycle to the AgentArmy template repository itself. AgentArmy publishes the standard and reusable files; workload repos copy and own the runtime implementation.

The default profile is `platform-workload`: `local -> dev -> staging -> prod`, with `mock` as a parallel Postman/contract simulation target. AgentArmy template development uses the separate `template` profile: `local -> main`.

| File | Destination | Purpose |
|---|---|---|
| `github-actions-local-docker-gate-to-dev.yml` | `.github/workflows/local-docker-gate-to-dev.yml` | Local Docker quality gate that promotes a Dev source ref after tests pass. |
| `promotion-manifest.example.json` | `.agent/promotion.json` | Cloud-neutral lifecycle routing manifest. |
| `promotion.env.example` | `.agent/promotion.env.example` | Non-secret lifecycle promotion settings. |

Provider-specific handoffs live in target adapters:

```text
templates/azure-container-apps-dev/
templates/gcp-cloud-run/
```

The key rule is source promotion first, cloud build second. The local machine proves the branch. The selected target adapter builds or deploys the shared environment artifact.
