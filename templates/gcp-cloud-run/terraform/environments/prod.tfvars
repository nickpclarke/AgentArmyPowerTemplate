environment = "prod"
project_id  = "my-app-prod"
region      = "us-central1"

service_name        = "my-service"
github_repo         = "nickpclarke/my-api-spoke"
artifact_repository = "containers"

allow_unauthenticated = false

env = {
  LOG_LEVEL = "info"
}

# Only fully-baked flags are on in prod. Keep risky flags off until promoted.
feature_flags = {
  new_checkout   = false
  beta_dashboard = false
  rate_limiting  = true
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
