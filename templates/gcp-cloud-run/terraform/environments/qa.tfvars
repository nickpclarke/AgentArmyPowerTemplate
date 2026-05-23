environment = "qa"
project_id  = "my-app-qa"
region      = "us-central1"

service_name        = "my-service"
github_repo         = "nickpclarke/my-api-spoke"
artifact_repository = "containers"

allow_unauthenticated = false

env = {
  LOG_LEVEL = "info"
}

# Flags promote left-to-right (dev -> qa -> uat -> prod) as they stabilise.
feature_flags = {
  new_checkout   = true
  beta_dashboard = true
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
