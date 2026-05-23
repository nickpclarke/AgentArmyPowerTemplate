environment = "uat"
project_id  = "my-app-uat"
region      = "us-central1"

service_name        = "my-service"
github_repo         = "nickpclarke/my-api-spoke"
artifact_repository = "containers"

allow_unauthenticated = false

env = {
  LOG_LEVEL = "info"
}

# UAT mirrors prod flags as closely as possible for representative sign-off.
feature_flags = {
  new_checkout   = true
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
