# Project Deliverables Checklist

This document maps the assessment requirements to the files and AWS resources in this project.

## Required Deliverables

### 1. Git Repository With Application Code

Status: Included.

Where to find it:

- `app/main.py`: FastAPI web application.
- `tests/test_health.py`: basic automated test.
- `requirements.txt`: application dependencies.
- `requirements-dev.txt`: test dependencies.

What this proves:

The repository contains a real web app that can run locally, in Docker, and on AWS.

### 2. Git Repository With CI/CD Pipeline Config

Status: Included.

Where to find it:

- `.github/workflows/deploy.yml`

What this proves:

GitHub Actions can test the app, build the Docker image, push it to AWS ECR, and deploy infrastructure/app changes using Terraform.

### 3. Documentation

Status: Included.

Where to find it:

- `README.md`: project overview.
- `docs/STEP_BY_STEP.md`: detailed setup and deployment steps.
- `docs/ARCHITECTURE.md`: design decisions and cost notes.
- `docs/DELIVERABLES_CHECKLIST.md`: this requirement mapping.

### 4. Architecture Diagram

Status: Included.

Where to find it:

- `README.md`

The diagram is written in Mermaid format so GitHub can render it visually.

### 5. Setup Steps

Status: Included.

Where to find it:

- `docs/STEP_BY_STEP.md`

### 6. Design Decisions

Status: Included.

Where to find it:

- `docs/ARCHITECTURE.md`

### 7. Live URL

Status: Available after AWS deployment.

How to get it:

```bash
cd terraform
terraform output load_balancer_url
```

If Route 53 and HTTPS are configured, also check:

```bash
terraform output route53_url
```

Target production expectation:

- The preferred live URL is the Route 53 HTTPS domain.
- The raw load balancer URL is mainly a fallback when no owned domain is available yet.

## Bonus Items

### Infrastructure As Code: Terraform Or CloudFormation

Status: Included.

Choice used:

- Terraform

Where to find it:

- `terraform/main.tf`
- `terraform/variables.tf`
- `terraform/outputs.tf`
- `terraform/user_data.sh`

### Dockerize The App

Status: Included.

Where to find it:

- `Dockerfile`
- `.dockerignore`

### Blue/Green Deployment Strategy

Status: Partially included as a rolling deployment, not a full blue/green setup.

What this project currently does:

- Builds a new Docker image for every deployment.
- Updates the EC2 Launch Template.
- Uses the Auto Scaling Group instance refresh to replace app servers gradually.
- Keeps the load balancer serving traffic while instances are replaced.

Why this is not full blue/green:

A true blue/green setup usually has two separate production environments, for example `blue` and `green`, with traffic switching between them after validation.

Cost-moderate recommendation:

For this assessment, rolling deployment is acceptable and cheaper. If the reviewer specifically asks for blue/green, add a second target group and switch ALB traffic between old and new versions.

### Use Amazon ECS Or Amazon EKS

Status: Not included in the current cost-moderate version.

Reason:

The core requirement says EC2 or Elastic Beanstalk. This project uses EC2 because it directly satisfies the requirement and keeps the architecture easier to explain.

Cost-moderate recommendation:

If you want to strengthen the bonus score, choose ECS Fargate instead of EKS. EKS is more complex and usually harder to justify for a small assessment app.

### Add Caching Layer: Redis / ElastiCache

Status: Not included in the current cost-moderate version.

Reason:

ElastiCache adds extra AWS cost and operational complexity. The app is intentionally simple and does not require caching to work.

Cost-moderate recommendation:

If the reviewer asks for this bonus, add a small ElastiCache Redis instance in the private subnets and use it for cached note reads or health metadata.

## Best Submission Summary

Use this summary when presenting the project:

This project delivers the required production-like AWS deployment for a FastAPI app using Terraform, Docker, GitHub Actions, EC2 Auto Scaling, Application Load Balancer, RDS PostgreSQL, S3, Secrets Manager, CloudWatch, and optional Route 53/HTTPS. It includes the required Git repository contents, CI/CD configuration, architecture diagram, setup steps, design decisions, and a live URL after deployment. Bonus items included are Infrastructure as Code and Dockerization. Rolling deployment is implemented as a cost-moderate alternative to full blue/green.
