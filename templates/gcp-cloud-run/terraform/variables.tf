variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "environment" {
  type        = string
  description = "Landscape this stack targets: dev | qa | uat | prod."

  validation {
    condition     = contains(["dev", "qa", "uat", "prod"], var.environment)
    error_message = "environment must be one of: dev, qa, uat, prod."
  }
}

variable "region" {
  type        = string
  description = "Region for Cloud Run, Artifact Registry, and the WIF resources."
  default     = "us-central1"
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name (also used as the image name)."
}

variable "github_repo" {
  type        = string
  description = "owner/repo allowed to deploy via Workload Identity Federation (e.g. nickpclarke/my-api-spoke)."
}

variable "artifact_repository" {
  type        = string
  description = "Artifact Registry Docker repository name."
  default     = "containers"
}

variable "image" {
  type        = string
  description = "Initial container image. Use a placeholder; CI rolls real images (image changes are ignored by Terraform)."
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "allow_unauthenticated" {
  type        = bool
  description = "Expose the service publicly. When false the service is IAM-gated."
  default     = false
}

variable "env" {
  type        = map(string)
  description = "Plaintext environment variables for the service."
  default     = {}
}

variable "feature_flags" {
  type        = map(bool)
  description = "Per-landscape feature flags. Rendered into the service as FLAG_<NAME> env vars (uppercased), e.g. {new_checkout = true} => FLAG_NEW_CHECKOUT=true."
  default     = {}
}

variable "secrets" {
  type        = map(string)
  description = "Map of ENV_VAR_NAME => Secret Manager secret id. Secrets are created and mounted as env vars (version 'latest')."
  default     = {}
}

variable "secret_values" {
  type        = map(string)
  description = "Optional initial values for secrets in `secrets` (keyed by ENV_VAR_NAME). PREFER adding versions out of band so values stay out of Terraform state."
  default     = {}
  sensitive   = true
}

variable "enable_apis" {
  type        = bool
  description = "Let Terraform enable the required Google APIs on the project."
  default     = true
}

variable "labels" {
  type        = map(string)
  description = "Resource labels for cost attribution (team, env, cost-center, spoke)."
  default     = {}
}
