# Example applications demonstrating service-to-service authentication using
# Google-signed OpenID Connect ID tokens.
#
#   - Service A can make authenticated requests to Service B.
#   - Service B can receive authenticated requests from Service A.

# Enable Cloud Run Admin API.
resource "google_project_service" "run" {
  project = var.project_id
  service = "run.googleapis.com"
}

resource "google_service_account" "service_a" {
  account_id = "gcp-oidc-service-a"
}

resource "google_service_account" "service_b" {
  account_id = "gcp-oidc-service-b"
}

# Service A (Calling Service).
# Service A can make authenticated requests to Service B.
resource "google_cloud_run_v2_service" "service_a" {
  name     = "service-a"
  location = var.region

  # Allow direct access from the Internet.
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.service_a.email

    containers {
      image = var.image

      # Override the entrypoint of the container.
      command = ["uvicorn", "src.services.service_a.main:app", "--host", "0.0.0.0", "--port", "8080"]

      env {
        name  = "SERVICE_B_URL"
        value = google_cloud_run_v2_service.service_b.uri
      }
    }
  }

  depends_on = [google_project_service.run]
}


# Service B (Receiving Service).
# Service B can receive authenticated requests from Service A.
resource "google_cloud_run_v2_service" "service_b" {
  name     = "service-b"
  location = var.region

  # Only allow internal traffic.
  ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = google_service_account.service_b.email

    containers {
      image = var.image

      # Override the entrypoint of the container.
      command = ["uvicorn", "src.services.service_b.main:app", "--host", "0.0.0.0", "--port", "8080"]

      env {
        name  = "SERVICE_B_URL"
        value = google_cloud_run_v2_service.service_b.uri
      }
    }
  }

  depends_on = [google_project_service.run]
}

resource "google_cloud_run_v2_service_iam_member" "service_b_invoker" {
  name     = google_cloud_run_v2_service.service_b.name
  location = google_cloud_run_v2_service.service_b.location
  member   = "serviceAccount:${google_service_account.service_a.email}"
  role     = "roles/run.invoker"

  # NOTE: `allUsers` makes the service publicly accessible.
  # members = ["allUsers"]
}
