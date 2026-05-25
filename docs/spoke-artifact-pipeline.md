# Spoke Artifact Pipeline

How project-management artifacts that spoke agents produce **as pull requests** — spikes,
research notes, and ADRs — flow automatically into the hub **Project board** and the hub
**docs/Pages**, without a human shuttling them across repos.

This complements the generic [Spoke → Hub Callback](spoke-hub-callback.md) (an activity log
of every merge/close/comment). The artifact pipeline is **path-triggered and fires early**,
so a draft spike shows up on the board the moment it opens.

## What triggers it

A spoke PR that touches any of these paths is an "artifact" PR:

| Path | Board `Type` |
|---|---|
| `spikes/**` | Spike |
| `docs/research/**` | Spike (research) |
| `docs/decisions/**` | Decision |

Detection is by **changed path** — no labels or title prefixes required. (If a PR touches
both, precedence is decision → spike → research.)

## The flow

```
spoke PR opened/ready (incl. draft)
  └─ notify-hub-artifacts.yml  (synced into every spoke)
       detects artifact paths → repository_dispatch `spoke-artifact` → hub
            └─ spoke-artifact.yml  (hub receiver)
                 • adds the spoke PR to Project #1 as a card
                 • sets Type (Spike/Decision) + Status = In progress

spoke PR merged
  └─ same dispatch with state=merged
       └─ spoke-artifact.yml
            • sets Status = Done
            • clones the spoke at the merge commit, copies the artifact files
              into docs/spokes/<repo>/… , regenerates the rollup index,
              commits to main  → Pages republishes
```

The board is **owner-level** (`users/nickpclarke/projects/1`), so it can hold PRs from any
of your repos directly — the card *is* the spoke PR, not a mirror issue. The harvested copy
exists because spokes are **private**: a Pages reader can't follow a link into a private repo,
so the content is copied in. See the result at [Spoke Artifacts](spokes/index.md).

## Setup (per spoke)

The spoke side is **inert until the spoke has a `PROJECT_TOKEN` secret** (classic PAT with
`repo` + `project` scope on the hub) — the same token the activity-log callback uses. Without
it the step skips and never fails spoke CI. `notify-hub-artifacts.yml` is delivered by the
hub→spoke helper sync; the hub receiver (`spoke-artifact.yml`) lives only in the hub.

## Files

| File | Where | Role |
|---|---|---|
| `.github/workflows/notify-hub-artifacts.yml` | hub → synced to spokes | detect + dispatch |
| `.github/workflows/spoke-artifact.yml` | hub only | board track + docs harvest |
| `scripts/gen_spoke_index.py` | hub | regenerate `docs/spokes/index.md` |
| `docs/spokes/<repo>/…` | hub | harvested artifact content (published) |

## Notes & limits

- **Harvest commits to `main`** with `PROJECT_TOKEN`. If branch protection rejects a direct
  push, switch the final step to open a PR instead.
- Provenance lives in `docs/spokes/<repo>/.harvest-<n>.json` (a dotfile — MkDocs ignores it,
  so it never ships to Pages but the index generator can read it).
- Non-markdown artifacts (`.py`, `.ttl`, `.json`) are copied as static assets — linkable and
  downloadable from the index, but only `.md` renders as a page.
