#!/usr/bin/env bash
# new-spoke.sh — single-command scaffolder for a new AgentArmy spoke.
#
# Realizes ARC-ADR-024 (platform-architect's golden-path Path A — top
# leverage call) + closes hub #223. Replaces the 7-step manual spoke
# creation (read 4 docs, hand-author 4 manifests, copy deploy scaffold,
# wire 3 GitHub secrets, validate with doctor) with one command + 2 inputs.
#
# Usage:
#   ./scripts/new-spoke.sh \
#     --name worker-core \
#     --system agentarmy \
#     --layer worker \
#     [--cloud azure] \
#     [--out ./worker-core]
#
# Output: a complete spoke skeleton at <out> with all 4 manifests
# (.agent/layer.json, .agent/promotion.json, agentarmy.services.json,
# image.json), a minimal Dockerfile + doctor for the runtime_kind,
# and a README with the next-step checklist (git init, gh repo create,
# GitHub secrets to set). Validates the image.json against the Image
# Standard schema before exit.
#
# Conforms to:
#   - Image Standard (docs/image-standard.md) — image.json + doctor
#   - ARC-ADR-023 — every spoke ships ONE Application-tier container
#   - ARC-ADR-024 — emits with tier=application declared by default
#   - templates/spoke-layer-manifest.example.json (shape v1)
#   - templates/service-manifest.example.json (shape v1)
#   - templates/lifecycle-promotion/promotion-manifest.example.json (shape v1)

set -euo pipefail
export MSYS_NO_PATHCONV=1  # Git Bash quirk — don't mangle /run/secrets paths

# ---- arg parsing -----------------------------------------------------------
NAME=""
SYSTEM=""
LAYER=""
CLOUD="azure"
OUT=""
HELP=0

usage() {
  cat <<EOF
new-spoke.sh — scaffold a new AgentArmy spoke

Required:
  --name <kebab>     Spoke name (kebab-case, e.g. worker-core)
  --system <name>    System / product the spoke belongs to (e.g. agentarmy)
  --layer <kind>     One of: api | web-ui | worker | infra | bff

Optional:
  --cloud <provider> azure (default) | gcp | vercel
  --out <path>       Output dir (default: ./<name>)
  --help             This help.

Conforms to ARC-ADR-023 (one Application-tier container per spoke) +
the Image Standard (one image.json per container).
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)   NAME="$2"; shift 2 ;;
    --system) SYSTEM="$2"; shift 2 ;;
    --layer)  LAYER="$2"; shift 2 ;;
    --cloud)  CLOUD="$2"; shift 2 ;;
    --out)    OUT="$2"; shift 2 ;;
    --help|-h) HELP=1; shift ;;
    *) echo "unknown flag: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ "$HELP" -eq 1 ]] || [[ -z "$NAME" ]] || [[ -z "$SYSTEM" ]] || [[ -z "$LAYER" ]]; then
  usage; exit "${HELP:-2}"
fi
case "$LAYER" in
  api|web-ui|worker|infra|bff) : ;;
  *) echo "--layer must be one of: api | web-ui | worker | infra | bff" >&2; exit 2 ;;
esac
case "$CLOUD" in
  azure|gcp|vercel) : ;;
  *) echo "--cloud must be one of: azure | gcp | vercel" >&2; exit 2 ;;
esac
if [[ ! "$NAME" =~ ^[a-z][a-z0-9-]{1,62}$ ]]; then
  echo "--name must be kebab-case starting with a letter (a-z0-9- only)" >&2; exit 2
fi

OUT="${OUT:-./$NAME}"
if [[ -e "$OUT" ]]; then
  echo "$OUT already exists — refusing to overwrite. Pick a different --out or remove it." >&2; exit 1
fi

# ---- per-layer derived defaults --------------------------------------------
case "$LAYER" in
  api|bff)   RUNTIME_KIND="container"; BASE_IMAGE="python:3.12-slim"; PORT=8000; HEALTH="/health/ready" ;;
  web-ui)    RUNTIME_KIND="container"; BASE_IMAGE="node:20-slim";    PORT=3000; HEALTH="/" ;;
  worker)    RUNTIME_KIND="worker";    BASE_IMAGE="python:3.12-slim"; PORT=8000; HEALTH="/healthz" ;;
  infra)     RUNTIME_KIND="iac";       BASE_IMAGE="none";              PORT=0;    HEALTH="" ;;
esac

# Cloud → promotion target wiring (from templates/lifecycle-promotion/)
case "$CLOUD" in
  azure)  TARGET="azure-container-apps";  DEPLOY_TARGET="aca" ;;
  gcp)    TARGET="gcp-cloud-run";         DEPLOY_TARGET="cloud-run" ;;
  vercel) TARGET="vercel";                DEPLOY_TARGET="none" ;;
esac

# ---- scaffold --------------------------------------------------------------
echo "=== scaffolding $NAME ($SYSTEM/$LAYER on $CLOUD) -> $OUT ==="
mkdir -p "$OUT/.agent" "$OUT/scripts"

cat > "$OUT/.agent/layer.json" <<JSON
{
  "\$schema": "agentarmy.layer.v1",
  "schema_version": "agentarmy.layer.v1",
  "system": "$SYSTEM",
  "layer": "$LAYER",
  "service": "$NAME",
  "repo_role": "spoke",
  "runtime_kind": "$RUNTIME_KIND",
  "contracts": [],
  "owns": [],
  "does_not_own": ["personal agent settings", "infra state"]
}
JSON

cat > "$OUT/.agent/promotion.json" <<JSON
{
  "schema_version": "agentarmy.promotion.v1",
  "lifecycle_profile": "platform-workload",
  "service": "$NAME",
  "default_target": "$TARGET",
  "dev_source_ref": "${TARGET}-dev",
  "promotion_order": ["local", "dev", "staging", "prod"],
  "simulation_targets": ["mock"],
  "targets": {
    "$TARGET": {
      "cloud": "$CLOUD",
      "build": "acr-task",
      "runtime": "$DEPLOY_TARGET",
      "template": "templates/${TARGET}-dev/"
    }
  }
}
JSON

cat > "$OUT/agentarmy.services.json" <<JSON
{
  "schema_version": "agentarmy.services.v1",
  "services": [
    {
      "name": "$NAME",
      "kind": "backend",
      "path": ".",
      "build": "docker build -t ${NAME}:local .",
      "test": "echo TODO: add tests",
      "health_url": "http://127.0.0.1:${PORT}${HEALTH}",
      "required": false
    }
  ]
}
JSON

cat > "$OUT/image.json" <<JSON
{
  "\$schema": "./templates/image-schema.json",
  "name": "$NAME",
  "kind": "single",
  "base": "$BASE_IMAGE",
  "description": "$SYSTEM/$LAYER spoke — Application tier (ARC-ADR-023). Scaffolded by scripts/new-spoke.sh.",
  "owner": "$NAME spoke (application tier)",
  "tier": "application",
  "services": [
    {
      "name": "$NAME",
      "build": ".",
      "role": "$LAYER",
      "ports": ["${PORT}:${PORT}"],
      "healthcheck": { "http": "${HEALTH}", "expect": 200 }
    }
  ],
  "secrets": [],
  "shims": { "note": "Add pip/apt deps the spoke needs on top of $BASE_IMAGE." },
  "baked": [],
  "doctor": {
    "cmd": "scripts/${NAME}-doctor.sh",
    "proves": ["readiness"],
    "description": "GET ${HEALTH} 200 on the running container."
  },
  "deploy": {
    "target": "$DEPLOY_TARGET",
    "notes": "Deploy lane scaffold: copy templates/${TARGET}-dev/ from the hub once secrets are wired."
  },
  "volumes": [],
  "contract": []
}
JSON

if [[ "$RUNTIME_KIND" != "iac" ]]; then
  cat > "$OUT/Dockerfile" <<DF
# $NAME — $SYSTEM/$LAYER spoke. Scaffolded by scripts/new-spoke.sh.
# Per ARC-ADR-023 (container tiering), this is the spoke's Application-tier
# container; one container per spoke; platform databases connect via env.

FROM $BASE_IMAGE
WORKDIR /app

# TODO: copy your sources and install deps. Example for Python:
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt
# COPY app ./app

# Non-root runtime (CWE-269 — Image Standard requirement).
RUN groupadd -r app && useradd -r -g app -m -d /home/app app
USER app
WORKDIR /home/app

EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \\
  CMD curl -fsS "http://127.0.0.1:${PORT}${HEALTH}" || exit 1

# TODO: replace with your real entrypoint.
CMD ["echo", "scaffolded — replace CMD"]
DF
fi

cat > "$OUT/scripts/${NAME}-doctor.sh" <<DOC
#!/usr/bin/env bash
# $NAME doctor — external verifier per the Image Standard.
# Assumes the container is up on \$PORT (default $PORT).
set -u
export MSYS_NO_PATHCONV=1
PORT="\${PORT:-$PORT}"
code=\$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "http://localhost:\${PORT}${HEALTH}" || echo "000")
echo "  GET http://localhost:\${PORT}${HEALTH} -> \$code"
[[ "\$code" =~ ^2[0-9][0-9]$ ]]
DOC
chmod +x "$OUT/scripts/${NAME}-doctor.sh" 2>/dev/null || true

cat > "$OUT/README.md" <<MD
# $NAME

$SYSTEM/$LAYER spoke. Scaffolded by [\`scripts/new-spoke.sh\`](../AgentArmy/scripts/new-spoke.sh) from the hub.

## Mission

<!-- TODO: one or two sentences — what this layer does and who consumes it.
     This is the repo's purpose statement; keep it sharp. -->

## Repository map

The few directories a newcomer (human or agent) needs to get oriented:

| Path | What's here |
|---|---|
| \`./\` | \`image.json\` (container manifest), \`Dockerfile\`, \`.agent/\` (layer + promotion manifests) |
| \`contracts/\` | OpenAPI/AsyncAPI this layer produces or vendors (contract-first) |
| \`scripts/\` | \`${NAME}-doctor.sh\` + repo tooling |
| \`AGENTS.md\` / \`CLAUDE.md\` | shared fleet law (synced from hub) / this repo's agent guidance |
<!-- TODO: add this layer's real source dirs (e.g. \`src/\`, \`app/\`, \`tests/\`). -->

## Conventions

- **Tier:** \`application\` ([ARC-ADR-023](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-023-container-tiering-strategy.md)) — one container per spoke; platform databases live in the hub and this service connects via env.
- **Contracts:** all integration via OpenAPI/AsyncAPI in \`contracts/\`. Vendor consumed contracts; never raw-fetch.
- **Image Standard:** \`image.json\` + \`scripts/${NAME}-doctor.sh\` validate via \`node tools/agentarmy-doctor.mjs image .\` from a sibling hub checkout.

## Next steps after scaffold

1. **Git init + first commit**
   \`\`\`bash
   cd $OUT
   git init && git add . && git commit -m "chore: scaffold $NAME spoke"
   gh repo create nickpclarke/$NAME --private --source . --remote origin --push
   \`\`\`
2. **Wire GitHub Secrets** (Settings → Secrets → Actions):
   - \`PROJECT_TOKEN\` — classic PAT with \`project\` scope (Projects v2 writes; same as hub)
   - \`CLAUDE_CODE_OAUTH_TOKEN\` — for the @claude PR-event loop
   - \`AZURE_CLIENT_ID\` / \`AZURE_TENANT_ID\` / \`AZURE_SUBSCRIPTION_ID\` — OIDC for ACA deploys
   - (cloud-specific extras per the deploy scaffold you copy in)
3. **Copy the deploy scaffold** when ready:
   \`\`\`bash
   cp -r ../AgentArmy/templates/${TARGET}-dev/ ./deploy/
   \`\`\`
4. **Validate the manifest**
   \`\`\`bash
   node ../AgentArmy/tools/agentarmy-doctor.mjs image .
   \`\`\`
5. **Register + dress this spoke** — add the repo to \`scripts/spoke_sync.config.json\` in the hub, then run \`python scripts/sync_helpers_to_spokes.py --spoke $NAME\`. This hydrates the repo with the Claude / Codex / Antigravity agent packs and the shared law. See the full lifecycle: [docs/spoke-lifecycle.md](https://github.com/nickpclarke/AgentArmy/blob/main/docs/spoke-lifecycle.md).

## What's NOT scaffolded (intentionally)

- Application source code — replace the TODO in \`Dockerfile\` + add your code.
- Contracts — author OpenAPI/AsyncAPI in \`contracts/\` per the contract-first rule.
- Tests — wire your test runner; update \`agentarmy.services.json\` \`test\` field.
- Deploy lane — copy from \`templates/${TARGET}-dev/\` when you're ready to deploy.

See [docs/spoke-lifecycle.md](https://github.com/nickpclarke/AgentArmy/blob/main/docs/spoke-lifecycle.md) in the hub for the full scaffold → register → dress → watch flow, and [docs/agent-onboarding.md](https://github.com/nickpclarke/AgentArmy/blob/main/docs/agent-onboarding.md) for orientation as an agent running inside this spoke.
MD

# ---- next-step checklist ---------------------------------------------------
cat <<EOF

══════════════════════════════════════════════════════════════════════════
  $NAME scaffolded.

  Files emitted in $OUT:
    .agent/layer.json
    .agent/promotion.json
    agentarmy.services.json
    image.json
    $(if [[ "$RUNTIME_KIND" != "iac" ]]; then echo "Dockerfile"; fi)
    scripts/${NAME}-doctor.sh
    README.md

  Next:
    cd $OUT
    git init && git add . && git commit -m "chore: scaffold $NAME spoke"
    gh repo create nickpclarke/$NAME --private --source . --remote origin --push

  Required GitHub Secrets on the new repo:
    - PROJECT_TOKEN              (classic PAT, project scope)
    - CLAUDE_CODE_OAUTH_TOKEN    (for @claude PR loop)
    - AZURE_CLIENT_ID / AZURE_TENANT_ID / AZURE_SUBSCRIPTION_ID (OIDC; $CLOUD)

  Once pushed (spoke lifecycle stages 2-4 — see docs/spoke-lifecycle.md):
    1. REGISTER: add the repo to scripts/spoke_sync.config.json in the hub
    2. DRESS:    python scripts/sync_helpers_to_spokes.py --spoke $NAME
    3. WATCH:    node tools/fleet-heartbeat.mjs  (confirm no coder-pack-drift)
    4. cp -r templates/${TARGET}-dev/ to the new spoke's deploy/ dir
    5. node tools/agentarmy-doctor.mjs image . (from the spoke) to verify

  Full map: docs/spoke-lifecycle.md   ·   This spoke: $OUT/README.md
══════════════════════════════════════════════════════════════════════════
EOF
