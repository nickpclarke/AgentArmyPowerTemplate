#!/usr/bin/env bash
# deploy.sh — Build, push, and deploy the ACA GitHub Runner infrastructure.
#
# This script is idempotent: running it a second time with the same args is safe.
# It does NOT create or modify cloud resources automatically — it validates inputs,
# then runs `az deployment group create --what-if` before asking for confirmation.
#
# Prerequisites (run from the directory containing this script):
#   - az CLI authenticated:  az login && az account set --subscription AASub1
#   - az containerapp extension: az extension add --name containerapp
#   - docker (or podman) available and running
#   - Key Vault `akv01-agentarmy` accessible from the current account
#   - The runner resource group already exists (or pass --create-rg)
#
# Usage:
#   ./deploy.sh \
#     --subscription     <subscription-id>           \
#     --resource-group   rg-github-runner-ci         \
#     --location         eastus                      \
#     --acr-name         agentarmy                   \
#     --keyvault-name    akv01-agentarmy              \
#     --runner-version   2.317.0                      \
#     [--image-tag       <git-sha or 'latest'>]       \
#     [--create-rg]
#
# Environment variables override CLI flags:
#   SUBSCRIPTION, RESOURCE_GROUP, LOCATION, ACR_NAME, KV_NAME,
#   RUNNER_VERSION, IMAGE_TAG, CREATE_RG

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SUBSCRIPTION="${SUBSCRIPTION:-}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-github-runner-ci}"
LOCATION="${LOCATION:-eastus}"
ACR_NAME="${ACR_NAME:-agentarmy}"
KV_NAME="${KV_NAME:-akv01-agentarmy}"
RUNNER_VERSION="${RUNNER_VERSION:-2.317.0}"
IMAGE_NAME="aca-github-runner"
IMAGE_TAG="${IMAGE_TAG:-latest}"
KV_SECRET_NAME="GHRUNNERPAT"
CREATE_RG="${CREATE_RG:-false}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --subscription)   SUBSCRIPTION="$2";   shift 2 ;;
    --resource-group) RESOURCE_GROUP="$2"; shift 2 ;;
    --location)       LOCATION="$2";       shift 2 ;;
    --acr-name)       ACR_NAME="$2";       shift 2 ;;
    --keyvault-name)  KV_NAME="$2";        shift 2 ;;
    --runner-version) RUNNER_VERSION="$2"; shift 2 ;;
    --image-tag)      IMAGE_TAG="$2";      shift 2 ;;
    --create-rg)      CREATE_RG="true";    shift   ;;
    --help|-h)
      sed -n '/^# Usage:/,/^$/p' "${BASH_SOURCE[0]}"
      exit 0
      ;;
    *) echo "[deploy] unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Validation: required args
# ---------------------------------------------------------------------------
MISSING=()
[[ -z "${SUBSCRIPTION}" ]] && MISSING+=("--subscription")
[[ -z "${ACR_NAME}" ]]     && MISSING+=("--acr-name")

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "[deploy] ERROR: missing required arguments: ${MISSING[*]}" >&2
  echo "         Run ./deploy.sh --help for usage." >&2
  exit 1
fi

ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
FULL_IMAGE="${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"

echo ""
echo "========================================================================"
echo "  ACA GitHub Runner — deploy"
echo "========================================================================"
echo "  Subscription  : ${SUBSCRIPTION}"
echo "  Resource group: ${RESOURCE_GROUP}  (create: ${CREATE_RG})"
echo "  Location      : ${LOCATION}"
echo "  ACR           : ${ACR_LOGIN_SERVER}"
echo "  Image         : ${FULL_IMAGE}"
echo "  Runner binary : v${RUNNER_VERSION}"
echo "  Key Vault     : ${KV_NAME}  (secret: ${KV_SECRET_NAME})"
echo "========================================================================"
echo ""

# ---------------------------------------------------------------------------
# Step 1 — Set subscription context
# ---------------------------------------------------------------------------
echo "==> [1/6] Setting subscription context"
az account set --subscription "${SUBSCRIPTION}"

# ---------------------------------------------------------------------------
# Step 2 — Ensure resource group exists (optional)
# ---------------------------------------------------------------------------
if [[ "${CREATE_RG}" == "true" ]]; then
  echo "==> [2/6] Ensuring resource group: ${RESOURCE_GROUP}"
  az group create \
    --name "${RESOURCE_GROUP}" \
    --location "${LOCATION}" \
    --output none
  echo "    Resource group ready."
else
  echo "==> [2/6] Verifying resource group exists: ${RESOURCE_GROUP}"
  if ! az group show --name "${RESOURCE_GROUP}" --output none 2>/dev/null; then
    echo "    ERROR: resource group '${RESOURCE_GROUP}' not found." >&2
    echo "    Re-run with --create-rg to create it, or create it manually:" >&2
    echo "      az group create --name ${RESOURCE_GROUP} --location ${LOCATION}" >&2
    exit 1
  fi
  echo "    Resource group found."
fi

# ---------------------------------------------------------------------------
# Step 3 — Ensure the GitHub PAT secret exists in Key Vault
#   If it already exists, skip. If not, prompt for the value interactively
#   so the PAT is never in shell history or command-line args.
# ---------------------------------------------------------------------------
echo "==> [3/6] Checking Key Vault secret: ${KV_SECRET_NAME} in ${KV_NAME}"

if az keyvault secret show \
    --vault-name "${KV_NAME}" \
    --name "${KV_SECRET_NAME}" \
    --output none 2>/dev/null; then
  echo "    Secret already exists — skipping."
else
  echo "    Secret not found. You will be prompted for the GitHub PAT."
  echo "    Required: classic PAT with 'repo' scope (for private repos)."
  echo "    The existing PAT can be reused if it has 'repo' scope."
  echo ""
  # Read without echo to avoid leaking the PAT into terminal history.
  read -r -s -p "    Enter GitHub PAT (input hidden): " GH_PAT
  echo ""

  if [[ -z "${GH_PAT}" ]]; then
    echo "    ERROR: PAT cannot be empty." >&2
    exit 1
  fi

  az keyvault secret set \
    --vault-name "${KV_NAME}" \
    --name "${KV_SECRET_NAME}" \
    --value "${GH_PAT}" \
    --output none

  # Immediately discard the variable — it is now safely in Key Vault.
  unset GH_PAT
  echo "    Secret created."
fi

# ---------------------------------------------------------------------------
# Step 4 — Build and push the runner image to ACR
# ---------------------------------------------------------------------------
echo "==> [4/6] Logging in to ACR: ${ACR_LOGIN_SERVER}"
az acr login --name "${ACR_NAME}"

echo "==> Building image: ${FULL_IMAGE}"
echo "    Build ARG RUNNER_VERSION=${RUNNER_VERSION}"

docker build \
  --build-arg "RUNNER_VERSION=${RUNNER_VERSION}" \
  --tag "${FULL_IMAGE}" \
  --file "${SCRIPT_DIR}/Dockerfile" \
  "${SCRIPT_DIR}"

echo "==> Pushing image: ${FULL_IMAGE}"
docker push "${FULL_IMAGE}"

echo "    Image pushed successfully."

# ---------------------------------------------------------------------------
# Step 5 — What-if preview (shows what Bicep will create/modify)
# ---------------------------------------------------------------------------
echo ""
echo "==> [5/6] Running Bicep what-if preview (no changes applied yet)"
az deployment group what-if \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file  "${SCRIPT_DIR}/main.bicep" \
  --parameters     "${SCRIPT_DIR}/main.bicepparam" \
  --parameters     "imageTag=${IMAGE_TAG}" \
  --parameters     "keyVaultName=${KV_NAME}" \
  --parameters     "kvSecretNamePat=${KV_SECRET_NAME}" \
  --parameters     "acrLoginServer=${ACR_LOGIN_SERVER}"

# ---------------------------------------------------------------------------
# Step 6 — Confirm and deploy
# ---------------------------------------------------------------------------
echo ""
read -r -p "==> [6/6] Apply the above changes? (yes/no): " CONFIRM
if [[ "${CONFIRM}" != "yes" ]]; then
  echo "    Deployment cancelled — no changes applied."
  exit 0
fi

echo "==> Deploying infrastructure via Bicep"
az deployment group create \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file  "${SCRIPT_DIR}/main.bicep" \
  --parameters     "${SCRIPT_DIR}/main.bicepparam" \
  --parameters     "imageTag=${IMAGE_TAG}" \
  --parameters     "keyVaultName=${KV_NAME}" \
  --parameters     "kvSecretNamePat=${KV_SECRET_NAME}" \
  --parameters     "acrLoginServer=${ACR_LOGIN_SERVER}" \
  --output         json \
  | tee /tmp/aca-runner-deploy-output.json

echo ""
echo "========================================================================"
echo "  Deployment complete."
echo ""
echo "  Outputs:"
az deployment group show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "main" \
  --query "properties.outputs" \
  --output table 2>/dev/null || true

echo ""
echo "  Next steps:"
echo "    1. Update your workflows to use:  runs-on: [self-hosted, aca-linux]"
echo "    2. Trigger a workflow run — KEDA will start a runner Job automatically."
echo "    3. Monitor executions:"
echo "       az containerapp job execution list \\"
echo "         --resource-group ${RESOURCE_GROUP} \\"
echo "         --name job-runner-agentarmy-AgentArmy-ci"
echo "========================================================================"
