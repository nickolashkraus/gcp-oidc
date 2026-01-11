output "service_a_url" {
  description = "URL for service_a."
  value       = google_cloud_run_v2_service.service_a.uri
}

output "service_b_url" {
  description = "URL for service_b."
  value       = google_cloud_run_v2_service.service_b.uri
}
