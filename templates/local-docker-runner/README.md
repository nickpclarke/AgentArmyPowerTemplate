# Local Docker self-hosted runners

Free, unmetered CI for the AgentArmy fleet on **your own machine**. Self-hosted runner
minutes don't count against your monthly GitHub-hosted quota, so this unblocks CI even
when the included minutes are exhausted — at the cost of only running while your PC is on.

This is the **fast path** (≈15 min, no cloud auth). The always-on equivalent is
[`templates/aca-github-runner/`](../aca-github-runner/README.md) (Azure Container Apps +
KEDA, scale-to-zero) — **same idea, same labels**, so workflows don't change when you add it.

## How it works

```
PR opened by an agent → GitHub cloud queues the CI jobs
   → your local runner (outbound long-poll to GitHub) grabs a job → runs it → reports back
```

The runner connects **out** to GitHub; nothing is exposed inbound. GitHub owns the queue,
secrets, and logs; your container is just leased compute. One persistent runner per repo
(your account is a user, not an org, so runners register per-repo).

## Quick start

1. Docker Desktop running.
2. A classic GitHub **PAT with `repo` scope** (private repos). Reuse your existing
   PROJECT_TOKEN-style PAT or mint one at <https://github.com/settings/tokens>.
3. From this folder:
   ```bash
   export GH_PAT=ghp_your_token            # or: cp .env.example .env  &&  edit .env
   docker compose up -d                    # default: 1 ephemeral runner/repo (4 total)
   docker compose logs -f
   ```
4. Confirm they're online: `gh api repos/nickpclarke/<repo>/actions/runners`.

Stop with `docker compose down` (ephemeral runners drop out cleanly).

## Capacity (ephemeral pool)

Each runner is **ephemeral** — one job, then it exits and respawns fresh. Pool size per
repo = `replicas` = max concurrent jobs that repo runs locally.

```bash
LOCAL_RUNNERS_PER_REPO=8 docker compose up -d   # 8/repo = 32 total
docker compose up -d --scale runner-middle=12   # crank one repo
```

**Sizing — RAM is the cap, not cores.** A CI job wants ~2 GB; concurrency ≈ RAM ÷ 2 GB.
On a **32 GB** box, keep total runners ≤ ~12 (≈24 GB) so the OS + Docker Desktop + your other
work have headroom — heavy docker-build/browser jobs spike higher, so the default 1/repo (4)
is a conservative starting point (bump to `LOCAL_RUNNERS_PER_REPO=2` → 8 total for more
parallelism). Cores (you have plenty) let them all run at once; they don't raise
the ceiling. **The NPU is not used by CI at all.**

## Using the runners

The runners auto-carry `self-hosted`, `Linux`, `X64`. A workflow uses them by setting:

```yaml
jobs:
  build:
    runs-on: [self-hosted, linux]   # was: ubuntu-latest
```

> ⚠️ Once a workflow targets `[self-hosted, linux]`, it will **only** run when a runner is
> online. Keep heavy/cloud-deploy workflows on `ubuntu-latest` until you're confident, and
> migrate the lightweight gating checks (lint, tests, drift) first.

## Security

- **PAT:** never commit it. Prefer `export GH_PAT=…` (shell-only) over a `.env` file; if you
  use `.env`, it's gitignored. Scope it to `repo` only.
- **Code execution:** a self-hosted runner executes whatever a PR contains on your machine.
  Safe-ish here because these are **private** repos with your own agents — but never point a
  self-hosted runner at a public repo.
- **Docker socket (the reason for the local runner):** these runners mount
  `/var/run/docker.sock` so jobs labelled `docker-local` can run `docker build` against your
  Docker Desktop daemon — the one thing ACA runners **can't** do (no DIND). This grants those
  jobs **host-daemon (root-equivalent) access**, so it's only acceptable for **private** repos
  with your own agents. Never mount the socket on a runner attached to a public repo.
- The container runs with `no-new-privileges` and an isolated tmpfs workdir.

## Labels & routing

Runners carry `self-hosted, Linux, X64` (auto) plus `agentarmy, local, docker-local`.
- Non-docker jobs use `runs-on: [self-hosted, linux]` → run on **either** these or the ACA runners (whichever is up).
- Docker-build jobs use `runs-on: [self-hosted, docker-local]` → run **only here** (ACA lacks the label and a daemon). These run only while your PC + this runner are up.

## Files

| File | Role |
|---|---|
| `docker-compose.yml` | Four `myoung34/github-runner` services (one per repo) |
| `.env.example` | Template for the `GH_PAT` secret (copy to gitignored `.env`) |
