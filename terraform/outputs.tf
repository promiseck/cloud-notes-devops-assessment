output "load_balancer_url" {
  description = "Public URL for the web app before a custom domain is attached."
  value       = "http://${aws_lb.app.dns_name}"
}

output "route53_url" {
  description = "Custom domain URL, if domain_name was provided."
  value       = var.domain_name == "" ? "" : "https://${var.domain_name}"
}

output "s3_bucket" {
  description = "Private bucket used by the app for uploads."
  value       = aws_s3_bucket.uploads.bucket
}

output "ecr_repository_url" {
  description = "ECR repository where CI/CD pushes the Docker image."
  value       = aws_ecr_repository.app.repository_url
}

output "secret_name" {
  description = "Secrets Manager entry that stores app runtime settings."
  value       = aws_secretsmanager_secret.app.name
}
