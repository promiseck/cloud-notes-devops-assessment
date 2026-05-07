# Architecture And Design Decisions

## Why EC2 Auto Scaling Instead Of ECS/EKS?

The core requirement explicitly says EC2 or Elastic Beanstalk. EC2 with an Auto Scaling Group is direct, reviewable, and cheaper to understand than Kubernetes. ECS would be a strong bonus option, but it adds more moving parts than this assessment requires.

## Network Design

The VPC has:

- Public subnets for the load balancer and NAT Gateway.
- Private subnets for EC2 app servers and RDS.
- An Internet Gateway so public resources can receive web traffic.
- A NAT Gateway so private app servers can download patches and pull Docker images without being directly exposed to the internet.

This matters because the public internet should reach only the load balancer. The app servers and database stay private.

## Security Groups

- ALB security group allows HTTP/HTTPS from the internet.
- App security group allows port `8000` only from the ALB.
- Database security group allows PostgreSQL port `5432` only from the app servers.

This is the AWS equivalent of locking every door except the one the user actually needs.

## Secrets

The database URL, S3 bucket name, region, and app name are stored in AWS Secrets Manager. The EC2 instances read the secret at startup using their IAM role. Passwords are not stored in the app code.

## CI/CD

GitHub Actions performs four major jobs:

1. Run tests.
2. Create or confirm the ECR repository.
3. Build and push a Docker image.
4. Run Terraform to update AWS.

When the image changes, Terraform updates the launch template. The Auto Scaling Group then performs a rolling instance refresh so the app is replaced gradually.

## Monitoring

CloudWatch receives:

- EC2 CPU metrics.
- Memory metrics from the CloudWatch Agent.
- Startup logs from the EC2 instances.
- ALB error metrics.

The Terraform creates alarms for high CPU and ALB 5xx errors. In a full production setup, attach these alarms to an SNS topic for email, Slack, PagerDuty, or another alert channel.

## Domain And HTTPS

In the intended production flow, users should not normally type the raw load balancer URL. They should type a friendly domain name such as `notes.example.com`.

The request flow is:

1. User opens `https://notes.example.com`.
2. Route 53 receives the DNS lookup for that domain.
3. Route 53 points the domain to the Application Load Balancer.
4. The load balancer terminates HTTPS using the ACM certificate.
5. The load balancer sends traffic to healthy EC2 app servers.

To enable this, a real domain or subdomain must be available:

1. Create or use an existing Route 53 hosted zone.
2. Request an ACM certificate for the app domain.
3. Set `domain_name`, `hosted_zone_id`, and `certificate_arn` in Terraform.

Terraform then creates an alias record pointing the domain to the load balancer and enables HTTPS on port `443`.

The raw load balancer URL is still useful as a fallback test URL before the domain is connected.

## Cost Notes

Main cost drivers:

- NAT Gateway hourly cost.
- RDS hourly cost and storage.
- EC2 instance hours.
- Application Load Balancer hourly cost.

Moderate-cost choices:

- Keep `desired_capacity = 2` for a production-like demo.
- Use `desired_capacity = 1` for the cheapest short-lived demo, but explain that one server has less resilience.
- Destroy the environment when the assessment is complete.
- Keep CloudWatch log retention short.
