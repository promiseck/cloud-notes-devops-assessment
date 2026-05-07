variable "project_name" {
  description = "Short name used in AWS resource names."
  type        = string
  default     = "cloud-notes"
}

variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "eu-west-2"
}

variable "environment" {
  description = "Environment name, for example dev, staging, or prod."
  type        = string
  default     = "dev"
}

variable "container_image" {
  description = "Optional Docker image to run on EC2. Leave blank to use the ECR repo created by this Terraform project."
  type        = string
  default     = ""
}

variable "db_username" {
  description = "Database master username."
  type        = string
  default     = "appuser"
}

variable "db_instance_class" {
  description = "Small RDS instance class for a cost-moderate assessment deployment."
  type        = string
  default     = "db.t4g.micro"
}

variable "instance_type" {
  description = "Small EC2 instance type for the app servers."
  type        = string
  default     = "t3.micro"
}

variable "desired_capacity" {
  description = "Number of app servers to keep running."
  type        = number
  default     = 2
}

variable "domain_name" {
  description = "Optional full domain name, for example app.example.com."
  type        = string
  default     = ""
}

variable "hosted_zone_id" {
  description = "Optional Route 53 hosted zone ID for the domain."
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "Optional ACM certificate ARN for HTTPS. Create it in the same region as the ALB."
  type        = string
  default     = ""
}
