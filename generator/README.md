# AgentArmy Generator Harness

AgentArmy owns the generative programming harness for platform proofs. Product/service repos such as `middle-core`, `backend-core`, and `frontend-core` should consume generated outputs, but the deterministic generator pipeline, target manifests, tests, and acceptance proof live here.

The current working slice is:

```text
generator target manifest
  -> canonical model specs
  -> deterministic generator tools
  -> generated target contracts/assets
  -> target-local runtime/demo
  -> browser/API/platform proof
```

## Targets

| Target | Status | Purpose |
|---|---|---|
| `middle-core` | active | Generate C# contracts from the middle-core model and prove scenario runtime behavior. |
| `backend-core` | planned | Generate provider-facing contracts, projection adapters, ArcadeDB schema helpers, and contract tests. |
| `frontend-core` | planned | Generate typed UI view models, scenario cards, graph visualizers, and browser acceptance tests. |

Target manifests live under `generator/targets/`.

## Run The Active Platform Proof

```powershell
.\scripts\generator\Test-PlatformGeneration.ps1 -Target middle-core
```

Use a custom port if another service is already listening:

```powershell
.\scripts\generator\Test-PlatformGeneration.ps1 -Target middle-core -Port 18110
```

List available targets:

```powershell
.\scripts\generator\Test-PlatformGeneration.ps1 -ListTargets
```

## Boundary

- `generator/` describes reusable generative programming targets and acceptance proof expectations.
- `tools/modelgen/` contains the current deterministic Python implementation for the middle-core model.
- `model/` contains canonical authoring specs.
- `templates/<target>/generated/` contains disposable generated outputs.
- Hand-authored runtime behavior stays in each target's runtime/application folders.

This shape lets AgentArmy remain the template and test harness while generated artifacts can later be extracted into standalone `middle-core`, `backend-core`, or `frontend-core` repositories.
