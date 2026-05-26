#!/usr/bin/env bash
# bootstrap.sh — One-time Azure setup for the ArcadeDB ACA dev deployment.
#
# Run this ONCE from a workstation that has:
#   - az CLI (authenticated to the target subscription)
#   - Contributor + Key Vault Secrets Officer on the subscription / resource group
#
# Usage:
#   ./bootstrap.sh \
#     --subscription  <subscription-id>   \
#     --resource-group rg-arcadedb-dev   \
#     --location       eastus             \
#     --acr-name       myacr              \
#     --aca-env-name   cae-backend-dev    \
#     --keyvault-name  akv01-agentarmy    \
#     --github-org     nickpclarke        \
#     --github-repo    backend-core
#
# After this script succeeds, add the three AZURE_* values it prints to
# Settings > Secrets > Actions in the spoke repo.
# See README.md for the full setup walkthrough.

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults (override via flags)
# ---------------------------------------------------------------------------
SUBSCRIPTION=""
RESOURCE_GROUP="rg-arcadedb-dev"
LOCATION="eastus"
ACR_NAME=""
ACA_ENV_NAME="cae-backend-dev"
KV_NAME="akv01-agentarmy"
GITHUB_ORG=""
GITHUB_REPO=""

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --subscription)   SUBSCRIPTION="$2";   shift 2 ;;
    --resource-group) RESOURCE_GROUP="$2"; shift 2 ;;
    --location)       LOCATION="$2";       shift 2 ;;
    --acr-name)       ACR_NAME="$2";       shift 2 ;;
    --aca-env-name)   ACA_ENV_NAME="$2";   shift 2 ;;
    --keyvault-name)  KV_NAME="$2";        shift 2 ;;
    --github-org)     GITHUB_ORG="$2";     shift 2 ;;
    --github-repo)    GITHUB_REPO="$2";    shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
MISSING=()
[[ -z "${SUBSCRIPTION}" ]]  && MISSING+=("--subscription")
[[ -z "${ACR_NAME}" ]]      && MISSING+=("--acr-name")
[[ -z "${GITHUB_ORG}" ]]    && MISSING+=("--github-org")
[[ -z "${GITHUB_REPO}" ]]   && MISSING+=("--github-repo")

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "ERROR: missing required arguments: ${MISSING[*]}"
  echo "Run with --help or read the header comment for usage."
  exit 1
fi

echo "==> Setting subscription context to: ${SUBSCRIPTION}"
az account set --subscription "${SUBSCRIPTION}"

# ---------------------------------------------------------------------------
# 1. Resource group
# ---------------------------------------------------------------------------
echo "==> Ensuring resource group: ${RESOURCE_GROUP}"
az group create \
  --name "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --output none

# ---------------------------------------------------------------------------
# 2. Azure Container Registry
# ---------------------------------------------------------------------------
echo "==> Ensuring ACR: ${ACR_NAME}"
az acr create \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${ACR_NAME}" \
  --sku Basic \
  --admin-enabled false \
  --output none 2>/dev/null || echo "    (ACR already exists)"

ACR_LOGIN_SERVER=$(az acr show --name "${ACR_NAME}" --query loginServer -o tsv)
echo "    ACR login server: ${ACR_LOGIN_SERVER}"

# ---------------------------------------------------------------------------
# 3. Log Analytics + Container Apps Environment
# ---------------------------------------------------------------------------
echo "==> Ensuring Log Analytics workspace"
LAW_NAME="law-arcadedb-dev"
az monitor log-analytics workspace create \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${LAW_NAME}" \
  --location "${LOCATION}" \
  --output none 2>/dev/null || echo "    (workspace already exists)"

LAW_ID=$(az monitor log-analytics workspace show \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${LAW_NAME}" \
  --query customerId -o tsv)
LAW_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${LAW_NAME}" \
  --query primarySharedKey -o tsv)

echo "==> Ensuring Container Apps Environment: ${ACA_ENV_NAME}"
az containerapp env create \
  --name "${ACA_ENV_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --logs-workspace-id "${LAW_ID}" \
  --logs-workspace-key "${LAW_KEY}" \
  --output none 2>/dev/null || echo "    (ACA environment already exists)"

# ---------------------------------------------------------------------------
# 4. Key Vault secrets
#    Generate random passwords if the secrets do not already exist.
#    Constraint: avoid : [ ] { } in the service password (ArcadeDB delimiter).
# ---------------------------------------------------------------------------
echo "==> Checking Key Vault secrets in: ${KV_NAME}"

generate_password() {
  # 32 chars, alphanumeric + limited punctuation — excludes : [ ] { }
  LC_ALL=C tr -dc 'A-Za-z0-9!@#%^&*()-_=+' </dev/urandom | head -c 32
}

set_secret_if_missing() {
  local name="$1"
  local value="$2"
  if az keyvault secret show --vault-name "${KV_NAME}" --name "${name}" &>/dev/null; then
    echo "    ${name}: already exists — skipping"
  else
    az keyvault secret set \
      --vault-name "${KV_NAME}" \
      --name "${name}" \
      --value "${value}" \
      --output none
    echo "    ${name}: created"
  fi
}

ROOT_PW=$(generate_password)
SVC_PW=$(generate_password)

set_secret_if_missing "arcadedb-root-password"    "${ROOT_PW}"
set_secret_if_missing "arcadedb-service-password" "${SVC_PW}"

# ---------------------------------------------------------------------------
# 5. Entra ID app registration + OIDC federated credential
# ---------------------------------------------------------------------------
APP_NAME="sp-arcadedb-aca-deploy-${GITHUB_REPO}"
echo "==> Ensuring app registration: ${APP_NAME}"

APP_ID=$(az ad app list --display-name "${APP_NAME}" --query "[0].appId" -o tsv 2>/dev/null || echo "")
if [[ -z "${APP_ID}" ]]; then
  APP_ID=$(az ad app create --display-name "${APP_NAME}" --query appId -o tsv)
  echo "    Created app: ${APP_ID}"
  # Create the service principal
  az ad sp create --id "${APP_ID}" --output none
else
  echo "    App already exists: ${APP_ID}"
fi

TENANT_ID=$(az account show --query tenantId -o tsv)
SUB_ID=$(az account show --query id -o tsv)

# Role assignment: Contributor on the resource group
echo "==> Assigning Contributor on resource group to service principal"
SP_OID=$(az ad sp show --id "${APP_ID}" --query id -o tsv)
az role assignment create \
  --assignee-object-id "${SP_OID}" \
  --assignee-principal-type ServicePrincipal \
  --role Contributor \
  --scope "/subscriptions/${SUB_ID}/resourceGroups/${RESOURCE_GROUP}" \
  --output none 2>/dev/null || echo "    (role assignment already exists)"

# Role assignment: Key Vault Secrets Officer on the vault (needed to create secrets)
KV_ID=$(az keyvault show --name "${KV_NAME}" --query id -o tsv)
az role assignment create \
  --assignee-object-id "${SP_OID}" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope "${KV_ID}" \
  --output none 2>/dev/null || echo "    (KV role assignment already exists)"

# OIDC federated credentials — one for main branch pushes, one for workflow_dispatch
add_federated_credential() {
  local cred_name="$1"
  local subject="$2"
  local existing
  existing=$(az ad app federated-credential list --id "${APP_ID}" \
    --query "[?name=='${cred_name}'].name" -o tsv 2>/dev/null || echo "")
  if [[ -n "${existing}" ]]; then
    echo "    federated credential '${cred_name}': already exists — skipping"
    return
  fi
  az ad app federated-credential create \
    --id "${APP_ID}" \
    --parameters "{
      \"name\": \"${cred_name}\",
      \"issuer\": \"https://token.actions.githubusercontent.com\",
      \"subject\": \"${subject}\",
      \"audiences\": [\"api://AzureADTokenExchange\"]
    }" \
    --output none
  echo "    federated credential '${cred_name}': created"
}

echo "==> Creating OIDC federated credentials"
add_federated_credential \
  "github-main" \
  "repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/main"

add_federated_credential \
  "github-workflow-dispatch" \
  "repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/main"

# ---------------------------------------------------------------------------
# 6. Print the secrets to add to the spoke repo
# ---------------------------------------------------------------------------
echo ""
echo "========================================================================"
echo "  Bootstrap complete. Add the following to:"
echo "  Settings > Secrets > Actions  in  ${GITHUB_ORG}/${GITHUB_REPO}"
echo "========================================================================"
echo ""
echo "  AZURE_CLIENT_ID       = ${APP_ID}"
echo "  AZURE_TENANT_ID       = ${TENANT_ID}"
echo "  AZURE_SUBSCRIPTION_ID = ${SUB_ID}"
echo ""
echo "  Also set these as repo Variables (Settings > Variables > Actions):"
echo "  AZURE_ACR_LOGIN_SERVER = ${ACR_LOGIN_SERVER}"
echo "  AZURE_RESOURCE_GROUP   = ${RESOURCE_GROUP}"
echo ""
echo "  The ArcadeDB passwords are stored in Key Vault '${KV_NAME}'."
echo "  Secret names:"
echo "    arcadedb-root-password"
echo "    arcadedb-service-password"
echo ""
echo "  To connect backend-core's UDA, set:"
echo "    ARCADEDB_URL      = https://<fqdn from deploy output>"
echo "    ARCADEDB_DATABASE = knowledge"
echo "    ARCADEDB_USER     = platform_reader"
echo "    secret_ref        = akv:arcadedb-service-password"
echo "========================================================================"
