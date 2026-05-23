terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0, < 7.0"
    }
  }

  # Recommended: store state in a GCS bucket (create it once, out of band):
  #   gsutil mb -l us-central1 gs://YOUR-TFSTATE-BUCKET
  # backend "gcs" {
  #   bucket = "YOUR-TFSTATE-BUCKET"
  #   prefix = "cloud-run/SERVICE"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
