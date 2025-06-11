## 🧭 (1) Testing Current Setup
---
**LOGIN CREDENTIALS**
Admin account 
Email/Username : yuanxingt02@gmail.com
Password : Yuanxingt02Admin!

Agent account
Email/Username : yuanxingt02+1@gmail.com
Password : Yuanxingt02Agent!

**URLs of your application**
itsag2t3.com

---
## 🧭 (2) Setup Instructions for Deploying to Another Region (e.g., Hong Kong - `ap-east-1`)

This guide outlines the steps required to replicate the current AWS infrastructure into a different region. The current deployment is in `ap-southeast-1` (Singapore) across three Availability Zones. These instructions will help you set up the same infrastructure in another region, such as `ap-east-1` (Hong Kong).

Cloudformation Template and Routing Configuration can be found in Final Report

---

### 🌐 1. VPC and Networking Setup

Create a new **VPC** in the target region with the following:

- **3 Public Subnets** – one in each AZ (e.g., `ap-east-1a`, `ap-east-1b`, `ap-east-1c`)
  - For: External Application Load Balancer (ALB)
- **3 Private Subnets** – one in each AZ
  - For: ECS (Fargate), EC2 Auto Scaling Group, and RDS

- Configure Security Groups:
  - **External ALB SG** – allows inbound HTTP (80) and HTTPS (443) from the internet
  - **Frontend EC2 SG** – only allows traffic from the External ALB SG
  - **Internal ALB SG** – only allows traffic from the EC2 SG
  - **ECS Services SG** – only allows traffic from the Internal ALB SG
  - **RDS SG** – only allows traffic from ECS SG

> 🔐 Outbound traffic is allowed by default

---

### ⚙️ 2. Load Balancers

- **External ALB** (Public Subnets):
  - Listener on port **80** → Redirect to port **443**
  - Listener on port **443** → Forward to EC2 frontend ASG
  - Attach an **ACM certificate** for `itsag2t3.com` (must be created in the new region)

- **Internal ALB** (Private Subnets):
  - Listener on port **80**
  - Forward paths like `/api/admin`, `/api/client`, etc., to the appropriate ECS service and port

---

### 🧱 3. ECS (Fargate) Services

Create a new ECS Cluster and deploy the following 9 services:

- `admin`, `account`, `bounceemail`, `client`, `logging`, `sendemail`, `sftp`, `transaction`, `user`
- Use ECR to push images to the new region
- Create task definitions with the necessary environment variables
- Register each service to a target group behind the Internal ALB
- Environment variables are used throughout ECS, they can be found in the respective task definitions

---

### 🖥️ 4. EC2 Frontend

- Launch an **EC2 Auto Scaling Group** across all three AZs in private subnets
- In the launch template/user data script(code provided below):
  - Pull the frontend static assets (`dist/`) from S3
  - Start NGINX to serve the Vite frontend

---

### 🛢️ 5. RDS MySQL

- Launch a Multi-AZ MySQL RDS instance in private subnets
- Enable automatic backups and failover
- To replicate data from the current region:
  - Take a snapshot in `ap-southeast-1`
  - Share and restore it in `ap-east-1`

---

### 🔐 6. Authentication (Cognito)

- Create a new Cognito User Pool and App Client in the new region
- Update frontend/backend configs with the new pool ID and client ID

---

### 🌍 7. Domain and SSL

- Use **Route 53** to add an **A Record** or **CNAME** pointing to the new region's External ALB
- Request a new **ACM certificate** in the target region for `itsag2t3.com`
- Attach the certificate to the ALB (listener on port 443)

---

### 🔁 8. CI/CD (CodePipeline)

- Recreate or duplicate the existing CodePipeline setup in the new region
  - Push ECR images to the new region
  - Register new task definitions in the ECS cluster
  - Update ECS services with the new definitions
- Ensure IAM roles are scoped to the correct region and resources

---

### 📬 9. Email and Monitoring

- **SES (Simple Email Service)**:
  - Re-verify domain/email in the new region (SES is region-specific)

- **SQS & SNS**:
  - Recreate queues and topics in the new region
  - Re-subscribe services and notification targets

- **CloudWatch**:
  - Configure log groups for ECS, EC2, and RDS
  - Set up alarms for CPU/memory usage
  - Send alerts to admin via SNS when thresholds are breached

---

###  10. IAM Roles
---
- Ensure IAM roles are given to the required ecs containers, such as for access to SQS(used in email), Cognito(used in user), as well as to CodePipeline to access and update ECS services.

---

### 📜 EC2 User Data Script (Frontend EC2 ASG Launch Template)

Use the following script as the EC2 **user data** in the launch template for the frontend Auto Scaling Group. It installs NGINX, pulls the static frontend build from S3, configures routing for a Vite-based SPA, and sets up NGINX to serve the app.

```bash
#!/bin/bash
set -xe

# Install nginx and aws-cli
yum update -y
yum install -y nginx aws-cli unzip

# Start nginx and enable it to start on boot
systemctl enable nginx
systemctl start nginx

# Clean default nginx files
rm -rf /usr/share/nginx/html/*

# Download the Vite build from your S3 bucket, change bucket directory as needed 
aws s3 cp s3://itsag2t3frontend/dist/ /usr/share/nginx/html/ --recursive

# Set correct permissions for nginx to read the files
chown -R nginx:nginx /usr/share/nginx/html

# Configure nginx to handle SPA (Single Page App) routing
cat > /etc/nginx/conf.d/vite-app.conf << EOF
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

# Remove the default nginx configuration (if it exists)
rm -f /etc/nginx/conf.d/default.conf

# Test and reload nginx configuration
nginx -t && systemctl reload nginx

```
### 📜 CodePipeline Build project (to automate ECR push to ECS)

Use the following script in the build project for CodePipeline. Edit variables such as REPO_NAME,ACCOUNT_ID,AWS_REGION, etc. accordingly.

```bash
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.8
    commands:
      - echo Installing dependencies...
      - pip install --quiet awscli jq

  build:
    commands:
      - echo "Getting latest image tag from ECR..."
      - IMAGE_TAG=latest
      - AWS_REGION=ap-southeast-1
      - ACCOUNT_ID=699089610166
      - REPO_NAME=admin
      - IMAGE_URI=699089610166.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG

      - echo "Describing current task definition..."
      - TASK_FAMILY=Admin
      - CONTAINER_NAME=Admin
      - CLUSTER_NAME=ItsaApp
      - SERVICE_NAME=AdminLoad
      

      - TASK_DEF=$(aws ecs describe-task-definition --task-definition $TASK_FAMILY)

      - echo "Creating new task definition with updated image..."
      - |
        NEW_DEF=$(echo "$TASK_DEF" | jq --arg IMAGE "$IMAGE_URI" --arg NAME "$CONTAINER_NAME" '
          .taskDefinition |
          {
            family: .family,
            executionRoleArn: .executionRoleArn,
            networkMode: .networkMode,
            requiresCompatibilities: .requiresCompatibilities,
            cpu: .cpu,
            memory: .memory,
            containerDefinitions: [
              .containerDefinitions[] | if .name == $NAME then .image = $IMAGE | . else . end
            ]
          }')

      - echo "$NEW_DEF" > taskdef.json

      - echo "Registering new task definition revision..."
      - NEW_REVISION_ARN=$(aws ecs register-task-definition --cli-input-json file://taskdef.json | jq -r '.taskDefinition.taskDefinitionArn')

      # Debug output before ECS service update
      - echo "Updating ECS service with new task definition revision..."


      # Check if any variable is empty
      - |
        if [ -z "$CLUSTER_NAME" ] || [ -z "$SERVICE_NAME" ] || [ -z "$NEW_REVISION_ARN" ]; then
          echo "Error: One or more required variables are empty!"
          exit 1
        fi

      - aws ecs update-service --cluster "$CLUSTER_NAME" --service "$SERVICE_NAME" --task-definition "$NEW_REVISION_ARN" --force-new-deployment
```
