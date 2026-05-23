#!/usr/bin/env bash
set -euo pipefail

# Lightweight, keyless GitHub Actions -> Cloud Run bootstrap via Workload Identity
# Federation. This is the "no-Terraform" quickstart; for the managed/idempotent
# path (recommended) use ../terraform. Re-running is safe (already-existing
# resources are skipped).
#
# Required env:
#   PROJECT_ID    GCP project id
#   GITHUB_REPO   owner/repo allowed to deploy (e.g. nickpclarke/my-api-spoke)
# Optional env (defaults shown):
#   REGION=us-central1
#   REPOSITORY=containers
#   SA_NAME=cloud-run-deployer        # CI/deploy identity
#   RUNTIME_SA_NAME=cloud-run-runtime # identity the service runs as
#   POOL=github-actions
#   PROVIDER=github

: "${PROJECT_ID:?set PROJECT_ID}"
: "${GITHUB_REPO:?set GITHUB_REPO (owner/repo)}"
REGION="${REGION:-us-central1}"
REPOSITORY="${REPOSITORY:-containers}"
SA_NAME="${SA_NAME:-cloud-run-deployer}"
RUNTIME_SA_NAME="${RUNTIME_SA_NAME:-cloud-run-runtime}"
POOL="${POOL:-github-actions}"
PROVIDER="${PROVIDER:-github}"

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
RUNTIME_SA_EMAIL="${RUNTIME_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

echo ">> Enabling required APIs"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  cloudbuild.googleapis.com \
  --project "$PROJECT_ID"

echo ">> Artifact Registry repo '$REPOSITORY'"
gcloud artifacts repositories create "$REPOSITORY" \
  --repository-format=docker --location="$REGION" \
  --description="Container images for Cloud Run spokes" \
  --project "$PROJECT_ID" 2>/dev/null || echo "   already exists"

echo ">> Deploy service account '$SA_NAME'"
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="Cloud Run deployer (GitHub Actions)" \
  --project "$PROJECT_ID" 2>/dev/null || echo "   already exists"

echo ">> Runtime service account '$RUNTIME_SA_NAME'"
gcloud iam service-accounts create "$RUNTIME_SA_NAME" \
  --display-name="Cloud Run runtime identity" \
  --project "$PROJECT_ID" 2>/dev/null || echo "   already exists"

echo ">> Granting least-privilege roles to the deployer"
for ROLE in roles/run.admin roles/artifactregistry.writer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" --role="$ROLE" --condition=None --quiet >/dev/null
done

echo ">> Granting Secret Manager read to the runtime identity"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${RUNTIME_SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" --condition=None --quiet >/dev/null

echo ">> Workload Identity pool '$POOL'"
gcloud iam workload-identity-pools create "$POOL" \
  --location=global --display-name="GitHub Actions" \
  --project "$PROJECT_ID" 2>/dev/null || echo "   already exists"

echo ">> OIDC provider '$PROVIDER' (scoped to ${GITHUB_REPO})"
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
  --location=global --workload-identity-pool="$POOL" \
  --display-name="GitHub OIDC" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${GITHUB_REPO}'" \
  --project "$PROJECT_ID" 2>/dev/null || echo "   already exists"

POOL_ID="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}"
PROVIDER_RESOURCE="${POOL_ID}/providers/${PROVIDER}"

echo ">> Allowing '${GITHUB_REPO}' to impersonate ${SA_EMAIL}"
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${GITHUB_REPO}" \
  --project "$PROJECT_ID" --quiet >/dev/null

cat <<EOF

================ DONE ================
Add these GitHub repo secrets (Settings -> Secrets and variables -> Actions):

  WORKLOAD_IDENTITY_PROVIDER = ${PROVIDER_RESOURCE}
  DEPLOY_SERVICE_ACCOUNT     = ${SA_EMAIL}

Runtime identity for the service (pass as 'service_account'):
  ${RUNTIME_SA_EMAIL}

Artifact Registry:
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}

Create secrets with:
  echo -n "s3cr3t" | gcloud secrets create db-password --data-file=- --project ${PROJECT_ID}
======================================
EOF
