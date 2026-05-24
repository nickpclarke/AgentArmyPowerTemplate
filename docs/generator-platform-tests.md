# Generator Platform Tests

AgentArmy owns the platform-level generative programming harness. The generated outputs may target `middle-core`, `backend-core`, or `frontend-core`, but the template repo should keep the reusable model-to-code pipeline and acceptance tests visible in one place.

## Why This Exists

The goal is not to prove that one endpoint returns JSON. The goal is to prove this loop:

```text
model spec -> deterministic generator -> generated target artifacts -> target runtime/demo -> API + browser acceptance proof
```

That makes the generator a platform capability. Each target can eventually live in its own repo, but AgentArmy can still provide:

- canonical target manifests;
- deterministic generation commands;
- expected generated outputs;
- local proof scripts;
- Playwright browser tests;
- acceptance criteria for human and machine reviewers.

## Folder Layout

| Path | Purpose |
|---|---|
| `generator/README.md` | Human overview of the generator harness. |
| `generator/platform-test.manifest.json` | Registry of generator targets. |
| `generator/targets/middle-core.json` | Active target manifest for the middle-core prototype. |
| `generator/targets/backend-core.json` | Planned backend-core generation target. |
| `generator/targets/frontend-core.json` | Planned frontend-core generation target. |
| `scripts/generator/Test-PlatformGeneration.ps1` | Target-aware platform proof runner. |
| `tools/modelgen/` | Current deterministic Python generator implementation for middle-core. |

## Run It

List targets:

```powershell
.\scripts\generator\Test-PlatformGeneration.ps1 -ListTargets
```

Run the active middle-core platform proof:

```powershell
.\scripts\generator\Test-PlatformGeneration.ps1 -Target middle-core
```

Use a different port if needed:

```powershell
.\scripts\generator\Test-PlatformGeneration.ps1 -Target middle-core -Port 18110
```

Skip docs during a faster local loop:

```powershell
.\scripts\generator\Test-PlatformGeneration.ps1 -Target middle-core -Port 18110 -SkipDocs
```

## Active Target: Middle-Core

The middle-core target currently proves:

- model validation;
- deterministic C# contract generation;
- generated state-machine contracts;
- .NET build/test;
- catalog validation;
- localhost service startup;
- `/health`, `/model`, `/model/demo`, success scenario, and failure scenario checks;
- Playwright browser test against the scenario lab.

The human demo page is:

```text
/model/demo
```

## Planned Targets

Backend-core can use the same pattern for generated provider contracts, ArcadeDB schema helpers, projection adapters, OpenAPI drift checks, and backend contract fixtures.

Frontend-core can use the same pattern for generated typed view models, object cards, graph visualizers, scenario labs, and browser acceptance tests.

The important boundary is that the generator harness stays in AgentArmy, while generated outputs are disposable target artifacts.
