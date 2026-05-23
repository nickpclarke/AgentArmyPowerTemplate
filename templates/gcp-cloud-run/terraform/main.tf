locals {
  required_apis = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "cloudbuild.googleapis.com",
  ]

  # Every resource carries the landscape label for cost attribution and filtering.
  labels = merge(var.labels, { env = var.environment })

  # Feature flags become FLAG_<NAME> env vars (vendor-neutral / OpenFeature-friendly).
  flag_env = { for name, on in var.feature_flags : "FLAG_${upper(name)}" => tostring(on) }

  # Plaintext env = explicit env + rendered feature flags.
  plain_env = merge(var.env, local.flag_env)
}

data "google_project" "this" {
  project_id = var.project_id
}

# ---------------------------------------------------------------------------
# APIs
# ---------------------------------------------------------------------------
resource "google_project_service" "apis" {
  for_each = var.enable_apis ? toset(local.required_apis) : toset([])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# ---------------------------------------------------------------------------
# Artifact Registry
# ---------------------------------------------------------------------------
resource "google_artifact_registry_repository" "containers" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_repository
  format        = "DOCKER"
  description   = "Container images for ${var.service_name}"
  labels        = local.labels

  depends_on = [google_project_service.apis]
}

# ---------------------------------------------------------------------------
# Identities: deployer (CI) + runtime (the service)
# ---------------------------------------------------------------------------
resource "google_service_account" "deployer" {
  project      = var.project_id
  account_id   = "${var.service_name}-deployer"
  display_name = "Cloud Run deployer for ${var.service_name} (GitHub Actions)"
}

resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = "${var.service_name}-runtime"
  display_name = "Cloud Run runtime identity for ${var.service_name}"
}

resource "google_project_iam_member" "deployer_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/artifactregistry.writer",
    "roles/iam.serviceAccountUser",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# ---------------------------------------------------------------------------
# Workload Identity Federation: keyless GitHub Actions -> GCP, scoped to one repo
# ---------------------------------------------------------------------------
resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github-actions"
  display_name              = "GitHub Actions"

  depends_on = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }
  # Scope the provider to a single repo so no other repo can mint tokens.
  attribute_condition = "assertion.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "github_impersonation" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

# ---------------------------------------------------------------------------
# Secret Manager
# ---------------------------------------------------------------------------
resource "google_secret_manager_secret" "this" {
  for_each = var.secrets

  project   = var.project_id
  secret_id = each.value
  labels    = local.labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Optional initial values. Prefer adding versions out of band to keep secrets out of state.
resource "google_secret_manager_secret_version" "this" {
  for_each = var.secret_values

  secret      = google_secret_manager_secret.this[each.key].id
  secret_data = each.value
}

# Runtime identity may read the secrets it mounts.
resource "google_secret_manager_secret_iam_member" "runtime_accessor" {
  for_each = var.secrets

  project   = var.project_id
  secret_id = google_secret_manager_secret.this[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

# ---------------------------------------------------------------------------
# Cloud Run service (CI owns image rollout; see ignore_changes below)
# ---------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "this" {
  project  = var.project_id
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  labels   = local.labels

  template {
    service_account = google_service_account.runtime.email

    containers {
      image = var.image

      dynamic "env" {
        for_each = local.plain_env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.this[env.key].secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  lifecycle {
    # CI deploys real image tags; Terraform should not fight those rollouts.
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }

  depends_on = [
    google_project_iam_member.deployer_roles,
    google_secret_manager_secret_iam_member.runtime_accessor,
  ]
}

# Public access (only when allow_unauthenticated = true).
resource "google_cloud_run_v2_service_iam_member" "public" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.this.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
