# Spoke → hub callback

Spoke repos report key events **back to the AgentArmy hub** so cross-repo activity is visible
in one place — the reverse of the hub→spoke [epic handoff](spoke-work-intake.md). It automates
the "close the loop with the hub" step from the spoke work-intake model.

## How it works

```
spoke: PR merged / issue closed / PR-issue comment (non-bot)
  └─ .github/workflows/notify-hub.yml   (synced to every spoke)
       └─ repository_dispatch  event_type=spoke-update  -->  nickpclarke/AgentArmy
            └─ .github/workflows/spoke-callback.yml      (hub receiver)
                 └─ appends to the hub "Spoke Activity Log" issue + the run summary
```

- **Spoke side** (`notify-hub.yml`, synced via `spoke_sync.config.json`): fires a `spoke-update`
  `repository_dispatch` to the hub on a **merged PR**, a **closed issue**, or a **comment** on a
  PR/issue, with `{repo, kind, number, title, url, author, snippet}`. Guards keep it sane:
  it **skips bot comments** (so Gemini's quota notices don't flood the hub) and **skips the hub
  repo itself** (which would otherwise loop on the Spoke Activity Log). Needs **`PROJECT_TOKEN`**
  in the spoke's secrets; if absent the step **skips** (never fails the spoke's CI).
- **Hub side** (`spoke-callback.yml`): listens for `repository_dispatch: [spoke-update]` and
  records the event on a `Spoke Activity Log` issue (created on first event) + the run summary,
  using the built-in `GITHUB_TOKEN`.

Untrusted `client_payload` is read through `env:` vars and used only as quoted shell variables
— never interpolated into the `run:` script (GitHub Actions injection-safety).

## "Both" mechanisms

`repository_dispatch` is the default (decoupled, one shared token, easy to add event types).
A spoke can **also** write to the hub directly when it already knows the target — e.g. comment
on the linked hub epic via `gh issue comment` with `PROJECT_TOKEN`. Use direct writes for the
specific "this epic is done" case; use `repository_dispatch` for general activity.

## Follow-ups

- **v2 routing:** carry a `hub_ref` (the originating hub epic) in the payload so the receiver
  comments on that epic instead of the central log.
- **Board nudge:** extend the receiver to move the linked hub Project item to *Done*.
