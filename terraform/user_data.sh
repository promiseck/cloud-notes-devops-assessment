#!/bin/bash
set -euxo pipefail

dnf update -y
dnf install -y docker amazon-cloudwatch-agent
systemctl enable --now docker

aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin "$(echo ${container} | cut -d/ -f1)"
aws secretsmanager get-secret-value --region ${aws_region} --secret-id ${secret_id} --query SecretString --output text > /tmp/app-secret.json

DATABASE_URL=$(python3 -c "import json; print(json.load(open('/tmp/app-secret.json'))['DATABASE_URL'])")
S3_BUCKET=$(python3 -c "import json; print(json.load(open('/tmp/app-secret.json'))['S3_BUCKET'])")
APP_NAME=$(python3 -c "import json; print(json.load(open('/tmp/app-secret.json'))['APP_NAME'])")

docker rm -f ${project_name} || true
docker pull ${container}
docker run -d \
  --restart unless-stopped \
  --name ${project_name} \
  -p ${app_port}:8000 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e S3_BUCKET="$S3_BUCKET" \
  -e AWS_REGION="${aws_region}" \
  -e APP_NAME="$APP_NAME" \
  ${container}

cat >/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<'JSON'
{
  "metrics": {
    "append_dimensions": {
      "InstanceId": "$${aws:InstanceId}",
      "AutoScalingGroupName": "$${aws:AutoScalingGroupName}"
    },
    "metrics_collected": {
      "mem": { "measurement": ["mem_used_percent"], "metrics_collection_interval": 60 },
      "disk": { "measurement": ["used_percent"], "resources": ["*"], "metrics_collection_interval": 60 }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/cloud-init-output.log",
            "log_group_name": "${log_group}",
            "log_stream_name": "{instance_id}/cloud-init"
          }
        ]
      }
    }
  }
}
JSON

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s
