output "workload_identity_provider" {
  description = "Set as the GitHub repo secret WORKLOAD_IDENTITY_PROVIDER."
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "deploy_service_account" {
  description = "Set as the GitHub repo secret DEPLOY_SERVICE_ACCOUNT."
  value       = google_service_account.deployer.email
}

output "runtime_service_account" {
  description = "Pass as the `service_account` input to the deploy workflow."
  value       = google_service_account.runtime.email
}

output "artifact_registry" {
  description = "Artifact Registry path for built images."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repository}"
}

output "service_url" {
  description = "Cloud Run service URL."
  value       = google_cloud_run_v2_service.this.uri
}

output "set_secrets_flag" {
  description = "Value for the deploy workflow `set_secrets` input (empty when no secrets configured)."
  value       = join(",", [for env_name, secret_id in var.secrets : "${env_name}=${secret_id}:latest"])
}

output "feature_flags_rendered" {
  description = "Feature flags as they appear in the running service (FLAG_<NAME> env vars)."
  value       = local.flag_env
}

