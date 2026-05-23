environment = "dev"
project_id  = "my-app-dev"
region      = "us-central1"

service_name        = "my-service"
github_repo         = "nickpclarke/my-api-spoke"
artifact_repository = "containers"

# Dev is typically IAM-gated and unauthenticated for quick testing — adjust to taste.
allow_unauthenticated = true

env = {
  LOG_LEVEL = "debug"
}

# Feature flags for this landscape. Rendered into the service as FLAG_<NAME> env
# vars (e.g. FLAG_NEW_CHECKOUT=true). Flip freely in dev; promote per environment.
feature_flags = {
  new_checkout   = true
  beta_dashboard = true
  rate_limiting  = false
}

secrets = {
  DB_PASSWORD = "db-password"
  API_KEY     = "api-key"
}

labels = {
  team        = "platform"
  cost-center = "engineering"
  spoke       = "my-api-spoke"
}
