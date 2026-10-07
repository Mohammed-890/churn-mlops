# AWS deployment and recovery runbook

**Status:** no AWS resources have been created. This runbook is for the next stage, after you choose an account, region and acceptable budget. Terraform validation does not prove a cloud deployment will succeed. Do not use real customer information with the demonstration's public HTTP endpoint.

## Before deployment

Use a sandbox AWS account with an appropriate non-root identity. Install AWS CLI v2, Docker and Terraform 1.9.8 or a compatible version. Authenticate using your normal AWS SSO/profile flow; do not commit keys. Run `aws sts get-caller-identity` and confirm the account is the intended one.

Review costs for ECS Fargate (0.5 vCPU and 1 GB memory per task), an Application Load Balancer, public IPv4 addresses, ECR storage, CloudWatch logs/alarms, SNS and data transfer in your chosen region. During rollout two tasks can run temporarily. There is no NAT gateway in this configuration. Charges continue while resources run even if no one visits the app. Use the AWS pricing calculator and set an account budget alert before creating resources. No fixed monthly estimate is asserted here.

Create an empty GitHub repository and upload the contents of this project, including workflow files and the Terraform provider lock file. Do not upload `.venv`, `.terraform`, state files, credentials or private tfvars.

## Bootstrap ECR without a circular dependency

The service needs an image in ECR before it starts. First create only the repository using a targeted bootstrap, build/push the image, then apply the full configuration. Targeted applies are an initial bootstrap exception, not the normal update flow.

1. From the project root, copy `infra/terraform.tfvars.example` to `infra/terraform.tfvars`.
2. Fill in your repository as `owner/repo`, region and project name. The example image URI is temporary for repository bootstrap only; replace it before the full apply. If the AWS account already has a GitHub OIDC provider, set `create_github_oidc = false` to reuse it. The configuration will never delete that reused provider.
3. From the project root:

```bash
terraform -chdir=infra init
terraform -chdir=infra plan \
  -target=aws_ecr_repository.api \
  -target=aws_ecr_lifecycle_policy.api \
  -out=bootstrap.tfplan
```

Inspect the plan. It should create the ECR repository and lifecycle policy only. After reviewing the resources and cost, apply that exact plan:

```bash
terraform -chdir=infra apply bootstrap.tfplan
```

4. Build and push. The following example assumes eu-west-2 and repository name churnops; replace both consistently if changed. Choose a fresh immutable tag when repeating bootstrap.

```bash
CHURN_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
CHURN_REGION=eu-west-2
CHURN_REPOSITORY=churnops
CHURN_REGISTRY="$CHURN_ACCOUNT.dkr.ecr.$CHURN_REGION.amazonaws.com"
CHURN_TAG=bootstrap-v1
aws ecr get-login-password --region "$CHURN_REGION" | \
  docker login --username AWS --password-stdin "$CHURN_REGISTRY"
python scripts/verify_data.py
python -m src.train
python -m pytest -q
docker build --platform linux/amd64 -t "$CHURN_REGISTRY/$CHURN_REPOSITORY:$CHURN_TAG" .
docker run --rm -p 8000:8000 "$CHURN_REGISTRY/$CHURN_REPOSITORY:$CHURN_TAG"
```

Visit /ready and make a prediction while that local container is running. Stop it with Ctrl+C, then:

```bash
docker push "$CHURN_REGISTRY/$CHURN_REPOSITORY:$CHURN_TAG"
aws ecr describe-images --region "$CHURN_REGION" \
  --repository-name "$CHURN_REPOSITORY" \
  --image-ids imageTag="$CHURN_TAG" \
  --query 'imageDetails[0].imageDigest' --output text
```

5. Set `image_uri` in tfvars to `REGISTRY/REPOSITORY@sha256:...` using the returned digest. Now generate, inspect and apply the complete plan:

```bash
terraform -chdir=infra plan -out=deployment.tfplan
terraform -chdir=infra apply deployment.tfplan
terraform -chdir=infra output
```

6. Open the output URL, make a prediction and inspect /ready and /model. Verify ALB target health, ECS service events and CloudWatch logs. Confirm any SNS email subscription. Record the model version and task revision in your deployment notes.

## GitHub environment and variables

Create a GitHub environment named `production`. Restrict its deployment branches to main and add a required reviewer if available for your repository plan. The workflow also checks the main branch, but environment restrictions are the identity boundary for OIDC.

Set these environment/repository variables:

| Variable | Value |
|---|---|
| AWS_REGION | Region from tfvars |
| AWS_ROLE_ARN | Terraform github_role_arn output |
| ECR_REPOSITORY | Project repository name, normally churnops |
| ECS_CLUSTER | Terraform cluster output |
| ECS_SERVICE | Terraform service output |

Merge code into main, let the CI checks pass, and manually run **Deploy to ECS**. It builds a fresh image, smoke-tests it locally, pushes a unique immutable tag and deploys by digest. It repeats Python tests but does not apply infrastructure.

The generated IAM role allows push to this ECR repository, task registration, updating this ECS service and passing this task execution role. Some AWS APIs require wildcard resources, notably ECR token acquisition and task registration. Review the policy before use. The application has no task role because it does not call AWS APIs.

## Terraform state and task revisions

For an initial solo demo, local state can work if you retain it securely. A shared repository should use an S3 backend with encryption, versioning, public access blocked and appropriate state locking. With Terraform 1.9, configure a DynamoDB lock table for the S3 backend. Create backend resources separately; do not make a state bucket depend on the same state it stores. Never upload state to Git.

The service ignores task_definition changes from Terraform, because app delivery owns revisions. If you change task settings in Terraform, apply the task-definition change, then deploy that resulting revision explicitly using `aws ecs update-service`. A normal GitHub deployment copies settings from the currently running task, so it will not automatically pick up an unused Terraform revision.

## Rollback

Before an app deployment, record the active revision:

```bash
aws ecs describe-services --cluster churnops --services churnops \
  --query 'services[0].taskDefinition' --output text
```

If an unhealthy new rollout fails, ECS's circuit breaker may return to the previous completed deployment. The workflow checks whether the active task is the newly requested one, so a rollback should fail the workflow instead of reporting success.

To manually restore a known-good revision:

```bash
aws ecs update-service --cluster churnops --service churnops \
  --task-definition YOUR_PREVIOUS_TASK_DEFINITION_ARN
aws ecs wait services-stable --cluster churnops --services churnops
```

Then check the active revision, /ready, /model and a prediction. Waiting for stable alone is insufficient. Keep rollback images in ECR: the demo policy retains the latest 20 images, so old task revisions are not an unlimited archive. The first deployment has no previous completed version to restore.

For an actual controlled failure exercise, use a throwaway branch/configuration and an image that deliberately fails readiness, deploy during a planned demo window, observe service events and prove the prior model still answers. Record evidence. This has not been done as part of local development.

## Teardown

Use the original state and AWS account. First inspect:

```bash
terraform -chdir=infra plan -destroy -out=destroy.tfplan
```

ECR deletion fails while images remain because force deletion is intentionally disabled. Decide which images you need to retain, then explicitly delete only images in this project's ECR repository before applying the destroy plan. A failed destroy can remove some resources and leave others; inspect the account and run a fresh destroy plan as needed.

Delete the project's CloudWatch logs if you do not need them, check for remaining ALBs/tasks/network interfaces/public IPs, and confirm your billing dashboard. Separately created state/budget resources are not in this project's Terraform state.

## Limits before a real production deployment

The default has one task, HTTP only, no login, no rate limiting and no autoscaling. Two ALB subnets do not make one task highly available. Logs contain infrastructure/request metadata, and the UI/API are intended for fictional records. Add HTTPS with ACM, authentication, request limiting, data handling controls, dependency/image review, deployment approvals and a measured availability plan before expanding the scope.
