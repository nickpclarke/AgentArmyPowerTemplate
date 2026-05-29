# board-sync (function tier)

Applies a **proven, vended field adapter** to live work items from a board system and
emits **canonical WorkItems** (ARC-ADR-036). The thin *runtime consumer* half of the
abstraction meta-service: the adapter was discovered, escalated, and **validated** at
build time by the meta-service and baked into `adapters/` — so this runtime needs no
embedder and no abstraction-service call. A GitHub issue and a Linear issue come out
the same shape, feeding the Holonic Unified Board ([#334](https://github.com/nickpclarke/AgentArmy/issues/334)).

## Run

```bash
python doctor.py          # offline correctness gate — samples -> canonical, required fields present
BOARD_SOURCE=github python sync.py   # LIVE: fetch Projects v2 items -> canonical WorkItems
```

`sync.py` resolves the GitHub token from `GH_TOKEN`, else **`akv:GithubPAT`** (Key
Vault, via `DefaultAzureCredential`) — keys never live in source. **Verified live**
against the AgentArmy Projects v2 board: a real item (board status "Done") normalized
to a runtime-safe canonical WorkItem.

## What's baked
| File | |
|---|---|
| `apply.py` | `apply_adapter(adapter, payload)` → canonical WorkItem; `missing_required()` gate |
| `connectors.py` | live GitHub Projects v2 GraphQL fetch (token from env or akv); Linear sample-ready |
| `adapters/*.workitem.json` | the **vended** field adapters (canonical field ← source field), from the meta-service |
| `samples/*.json` | representative payloads for the offline doctor |
| `doctor.py` | proves both surfaces normalize to one canonical shape |

## Deploy
ACA job/worker (`entrypoint sync`) on a schedule/trigger → canonical WorkItems to the
board. Linear: supply a workspace key + wire its connector (same shape as GitHub).
The adapter is **re-vended** when a board's schema drifts (re-run the meta-service).
