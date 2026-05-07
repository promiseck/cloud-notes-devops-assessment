# Detailed Step By Step Project Guide

This guide explains the work in the order it should be done. Each step includes what you do, why it matters, and how it contributes to the success of the whole project.

## 1. Understand The Goal

The project asks for a simple FastAPI app deployed in a production-like way on AWS.

The real goal is to show that the application is:

- Available through a public web address.
- Protected from unnecessary public access.
- Connected to a real database.
- Able to store files.
- Automatically tested and deployed.
- Monitored after deployment.
- Able to scale when traffic increases.

This matters because a DevOps engineer is judged not just by whether the app runs, but by whether it runs reliably and safely.

## 2. Build A Small Web App

This project uses the `Cloud Notes` FastAPI app.

It has:

- `/`: browser page for adding notes and uploading files.
- `/health`: simple health check for the load balancer.
- `/ready`: readiness check that confirms database access.
- `/api/notes`: saves and reads notes from RDS PostgreSQL.
- `/api/upload`: uploads files to S3.

Why this helps: the app is simple enough to understand, but it proves the required AWS services are genuinely connected.

## 3. Add Tests

The project includes a health endpoint test in `tests/test_health.py`.

Run locally:

```bash
pip install -r requirements-dev.txt
pytest
```

Why this helps: CI/CD should not deploy broken code. Even a small test gives the pipeline a quality gate.

## 4. Dockerize The App

The `Dockerfile` packages the FastAPI app into a repeatable container image.

Build locally:

```bash
docker build -t cloud-notes .
docker run -p 8000:8000 cloud-notes
```

Why this helps: Docker makes the app run the same way on a laptop, in CI, and on AWS.

## 5. Create The AWS Network With Terraform

Terraform creates a VPC with:

- 2 public subnets.
- 2 private subnets.
- Internet Gateway.
- NAT Gateway.
- Route tables.

Why this helps: public subnets receive internet traffic through the load balancer. Private subnets keep the app servers and database away from direct public access.

## 6. Add Security Groups

Terraform creates three security groups:

- Load balancer: accepts web traffic from users.
- App servers: accepts traffic only from the load balancer.
- Database: accepts traffic only from the app servers.

Why this helps: security groups reduce risk by allowing only necessary traffic.

## 7. Add RDS PostgreSQL

Terraform creates a private PostgreSQL database using RDS.

Why this helps: the app needs a persistent place to store notes. RDS is managed by AWS, so backups, patching options, encryption, and monitoring are easier than self-hosting a database.

## 8. Add S3 Storage

Terraform creates a private S3 bucket with public access blocked.

Why this helps: uploaded files should not live on an app server because app servers can be replaced during scaling or deployment. S3 is durable storage designed for files.

## 9. Add Secrets Manager

Terraform stores runtime configuration in AWS Secrets Manager.

Stored values include:

- Database connection URL.
- S3 bucket name.
- AWS region.
- App name.

Why this helps: secrets and environment settings should not be hard-coded in application code.

## 10. Add EC2 App Servers

Terraform creates a Launch Template. When an EC2 server starts, user data:

1. Installs Docker.
2. Logs in to ECR.
3. Reads app settings from Secrets Manager.
4. Pulls the Docker image.
5. Runs the FastAPI app container.
6. Starts the CloudWatch Agent.

Why this helps: servers can be replaced automatically and still configure themselves correctly.

## 11. Add The Load Balancer

Terraform creates an Application Load Balancer.

The load balancer:

- Receives public web traffic.
- Sends traffic to healthy app servers.
- Uses `/health` to check whether each server is alive.

Why this helps: users get one stable URL even if the app runs on multiple changing servers.

## 12. Add Auto Scaling

Terraform creates an Auto Scaling Group.

The group:

- Keeps the desired number of app servers running.
- Replaces unhealthy servers.
- Scales based on average CPU.

Why this helps: the application remains available if one server fails, and it can grow when demand increases.

## 13. Add Monitoring And Logs

Terraform creates CloudWatch log groups and alarms.

Monitoring includes:

- CPU usage.
- Memory usage from the CloudWatch Agent.
- Startup logs.
- Load balancer 5xx server errors.

Why this helps: deployment is not complete until you can see whether the system is healthy after it goes live.

## 14. Add Domain And HTTPS

This is part of the target production flow. A user should visit a proper HTTPS domain first, and Route 53 should send that traffic to the load balancer.

If you own a domain:

1. Create a Route 53 hosted zone or use an existing one.
2. Request an ACM certificate for the app domain.
3. Validate the certificate using DNS.
4. Set `domain_name`, `hosted_zone_id`, and `certificate_arn` in Terraform.

Why this helps: users should access the app through a friendly domain using encrypted HTTPS traffic.

If you do not yet own a domain, deploy with the load balancer URL first, then add Route 53 and HTTPS after the domain is available.

## 15. Configure GitHub Actions Secrets

In GitHub, add this repository secret:

- `AWS_ROLE_TO_ASSUME`: IAM role ARN that GitHub Actions can assume using OIDC.

Why this helps: GitHub can deploy without storing long-lived AWS access keys.

## 16. Run The Deployment

From your laptop for a first manual run:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

For the automated deployment:

1. Push code to the `main` branch.
2. GitHub Actions runs tests.
3. GitHub Actions builds the Docker image.
4. GitHub Actions pushes the image to ECR.
5. GitHub Actions applies Terraform.
6. AWS refreshes app instances gradually.

Why this helps: every code change follows the same reliable path to production.

## 17. Confirm The App Works

After Terraform finishes, get the load balancer URL:

```bash
terraform output load_balancer_url
```

Then test:

- Open the URL in a browser.
- Add a note.
- Upload a small file.
- Open `/health`.
- Open `/ready`.
- If a domain is configured, open the Route 53 domain and confirm it reaches the same app through HTTPS.
- Check CloudWatch logs.
- Check the ALB target group health.

Why this helps: this proves the web app, database, storage, network, load balancer, and monitoring are working together.

## 18. Simulate Load

Use a load tool such as `hey`:

```bash
hey -z 5m -c 50 https://your-domain.example.com/health
```

Watch:

- ALB target health.
- Auto Scaling activity.
- EC2 CPU.
- CloudWatch alarms.

Why this helps: the assessment specifically asks that the app remains available under simulated load.

## 19. Clean Up After Review

To avoid ongoing AWS charges:

```bash
cd terraform
terraform destroy
```

Why this helps: cloud resources cost money every hour. Cleaning up is part of responsible DevOps work.

## Suggested Submission Checklist

- Git repository contains application code.
- Git repository contains CI/CD config.
- Terraform code is included.
- Architecture diagram is included.
- Setup steps are documented.
- Design decisions are documented.
- Live URL is provided if AWS deployment is completed.
- Screenshots of GitHub Actions, CloudWatch, and the live app are added if requested by the reviewer.
