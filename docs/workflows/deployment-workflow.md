# REASSEMBLE — AWS Lambda Deployment & Operations Workflow

This document provides the operational runbook for building, packaging, deploying, configuring, and verifying the **REASSEMBLE** agent on AWS Lambda, backed by CockroachDB Cloud and Amazon Bedrock.

---

## Table of Contents

1. [Architecture & Deployment Model](#architecture--deployment-model)
2. [Prerequisites & IAM Configuration](#prerequisites--iam-configuration)
3. [Building the Lambda ZIP Package](#building-the-lambda-zip-package)
   - [PowerShell (Windows)](#1-powershell-build-workflow-windows)
   - [Bash / Zsh (macOS / Linux)](#2-bash--zsh-build-workflow-macos--linux)
4. [Creating & Updating the AWS Lambda Function](#creating--updating-the-aws-lambda-function)
   - [Option A: AWS Management Console](#option-a-aws-management-console)
   - [Option B: AWS CLI](#option-b-aws-cli)
5. [Configuring Function Settings & Environment Variables](#configuring-function-settings--environment-variables)
6. [Enabling & Configuring Lambda Function URL](#enabling--configuring-lambda-function-url)
7. [Post-Deployment Smoke Test Checklist](#post-deployment-smoke-test-checklist)
8. [Rollback & Disaster Recovery Procedures](#rollback--disaster-recovery-procedures)

---

## Architecture & Deployment Model

REASSEMBLE is deployed as an AWS Lambda serverless function that serves both the Single Page Application (SPA) frontend and the REST API backend through a public Lambda Function URL.

```
                      ┌───────────────────────────────────────────────┐
                      │                 Public Client                 │
                      │      (Web Browser / API Testing Harness)      │
                      └───────────────────────┬───────────────────────┘
                                              │ HTTPS
                                              ▼
                      ┌───────────────────────────────────────────────┐
                      │           Lambda Function URL (Auth: NONE)    │
                      └───────────────────────┬───────────────────────┘
                                              │
                                              ▼
                      ┌───────────────────────────────────────────────┐
                      │          AWS Lambda Runtime (Python 3.11)     │
                      │  - Handler: lambda_function.lambda_handler    │
                      │  - Memory: 512 MB | Timeout: 60s              │
                      │  - Pure-Python Driver: pg8000                 │
                      └──────────────┬─────────────────┬──────────────┘
                                     │                 │
              Direct TLS (Port 26257)│                 │ AWS SDK (boto3)
                                     ▼                 ▼
 ┌─────────────────────────────────────────┐     ┌────────────────────────────┐
 │         CockroachDB Cloud Basic         │     │       Amazon Bedrock       │
 │ - Durable Checkpoints (workflows)       │     │ - amazon.nova-lite-v1:0    │
 │ - Vector Indexing (memories <=> VECTOR) │     │ - amazon.titan-embed-text  │
 │ - Audit Logging (audit_log)             │     └────────────────────────────┘
 └─────────────────────────────────────────┘
```

---

## Prerequisites & IAM Configuration

### 1. Prerequisites
- AWS CLI installed and authenticated (`aws configure`).
- Active CockroachDB Cloud cluster running with database URL (`postgresql://...`).
- Models enabled in Amazon Bedrock Console (`us-east-1` recommended):
  - `amazon.nova-lite-v1:0`
  - `amazon.titan-embed-text-v2:0`

### 2. Lambda Execution Role & IAM Policy
Create an IAM execution role (e.g., `reassemble-lambda-role`) with standard CloudWatch logging permissions and Bedrock invocation rights:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:Converse"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Building the Lambda ZIP Package

Because REASSEMBLE uses `pg8000` (a pure-Python PostgreSQL driver), the deployment package can be compiled on any OS (Windows, macOS, Linux) with zero binary compatibility issues.

### 1. PowerShell Build Workflow (Windows)

Execute the following commands from the repository root (`c:\Users\moham\Downloads\reassemble-starter`):

```powershell
# 1. Clean previous build artifacts
if (Test-Path "package") { Remove-Item -Recurse -Force "package" }
if (Test-Path "reassemble-lambda.zip") { Remove-Item -Force "reassemble-lambda.zip" }

# 2. Create packaging directory
New-Item -ItemType Directory -Name "package"

# 3. Install pure-Python dependencies into package folder
pip install -r requirements.txt -t package --no-cache-dir

# 4. Copy source code into package folder
Copy-Item "lambda_function.py" -Destination "package\"

# 5. Compress into deployment zip
Set-Location -Path "package"
Compress-Archive -Path * -DestinationPath "..\reassemble-lambda.zip" -Force
Set-Location -Path ".."

# 6. Verify zip was created
Get-Item "reassemble-lambda.zip" | Select-Object Name, Length, LastWriteTime
```

### 2. Bash / Zsh Build Workflow (macOS / Linux)

```bash
# 1. Clean previous build artifacts
rm -rf package reassemble-lambda.zip

# 2. Create packaging directory
mkdir -p package

# 3. Install dependencies into package folder
pip install -r requirements.txt -t package --no-cache-dir

# 4. Copy source code
cp lambda_function.py package/

# 5. Create zip archive
cd package
zip -r ../reassemble-lambda.zip .
cd ..

# 6. Verify archive size
ls -lh reassemble-lambda.zip
```

---

## Creating & Updating the AWS Lambda Function

### Option A: AWS Management Console

1. Navigate to **AWS Lambda** > **Functions** > **Create function**.
2. Select **Author from scratch**:
   - **Function name**: `reassemble-agent`
   - **Runtime**: `Python 3.11` (or `Python 3.12`)
   - **Architecture**: `x86_64` (or `arm64`)
   - **Permissions**: Use existing role `reassemble-lambda-role`.
3. Click **Create function**.
4. In the **Code** tab:
   - Click **Upload from** > **.zip file**.
   - Select `reassemble-lambda.zip` and click **Save**.
5. In **Runtime settings** (below the code editor):
   - Verify **Handler** is set to: `lambda_function.lambda_handler`.

### Option B: AWS CLI

**Create Function (First time):**
```powershell
aws lambda create-function `
  --function-name reassemble-agent `
  --runtime python3.11 `
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/reassemble-lambda-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://reassemble-lambda.zip `
  --timeout 60 `
  --memory-size 512 `
  --region us-east-1
```

**Update Function Code (Subsequent builds):**
```powershell
aws lambda update-function-code `
  --function-name reassemble-agent `
  --zip-file fileb://reassemble-lambda.zip `
  --region us-east-1
```

---

## Configuring Function Settings & Environment Variables

### 1. General Configuration
- **Memory**: Set to `512 MB` (provides optimal CPU allocation for TLS cryptography and embedding serialization).
- **Timeout**: Set to `60 seconds` (accommodates cold starts, Bedrock Converse reasoning, and Titan text embeddings).

### 2. Environment Variables Configuration

Navigate to **Configuration** > **Environment variables** > **Edit**, and set:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `CRDB_URL` | `postgresql://USER:PASS@HOST:26257/defaultdb?sslmode=verify-full` | CockroachDB Cloud connection string |
| `AWS_REGION` | `us-east-1` | AWS Region for Bedrock |
| `CHAT_MODEL_ID` | `amazon.nova-lite-v1:0` | Amazon Bedrock reasoning model |
| `EMBED_MODEL_ID` | `amazon.titan-embed-text-v2:0` | Amazon Bedrock embedding model |

**AWS CLI Configuration:**
```powershell
aws lambda update-function-configuration `
  --function-name reassemble-agent `
  --environment "Variables={CRDB_URL='postgresql://USER:PASSWORD@HOST:26257/defaultdb?sslmode=verify-full',AWS_REGION='us-east-1',CHAT_MODEL_ID='amazon.nova-lite-v1:0',EMBED_MODEL_ID='amazon.titan-embed-text-v2:0'}" `
  --region us-east-1
```

---

## Enabling & Configuring Lambda Function URL

Lambda Function URLs provide a dedicated HTTP/HTTPS endpoint directly to the function without requiring API Gateway setup.

### 1. Create Function URL via AWS Console

1. Navigate to **Configuration** > **Function URL** > **Create function URL**.
2. **Auth type**: Choose `NONE` (public access for hackathon judging and live evaluation).
3. Expand **Additional settings (CORS)**:
   - **Allow origin**: `*`
   - **Allow headers**: `*` (or `content-type`)
   - **Allow methods**: Check `GET`, `POST`, `OPTIONS`.
4. Click **Save**.
5. Copy the generated **Function URL**:
   `https://<unique-id>.lambda-url.us-east-1.on.aws/`

### 2. Create Function URL via AWS CLI

```powershell
# Create Function URL with Auth NONE
aws lambda create-function-url-config `
  --function-name reassemble-agent `
  --auth-type NONE `
  --cors "AllowOrigins=*,AllowMethods=GET,POST,OPTIONS,AllowHeaders=content-type" `
  --region us-east-1

# Add public permission policy
aws lambda add-permission `
  --function-name reassemble-agent `
  --statement-id FunctionURLAllowPublicAccess `
  --action lambda:InvokeFunctionUrl `
  --principal "*" `
  --function-url-auth-type NONE `
  --region us-east-1
```

---

## Post-Deployment Smoke Test Checklist

Execute this verification sequence against your public Lambda Function URL:

### 1. UI Root Endpoint Smoke Test
Open `https://<unique-id>.lambda-url.us-east-1.on.aws/` in your browser:
- [ ] Page renders with dark background and purple header **REASSEMBLE**.
- [ ] Action buttons (`1. Start Incident`, `2. Simulate Worker Crash`, `3. Resume from Checkpoint`, `Refresh Memory`) are visible.

### 2. Memory Vector Retrieval Test
```bash
curl -s -X POST https://<unique-id>.lambda-url.us-east-1.on.aws/api/memories \
  -H "Content-Type: application/json"
```
- [ ] Response status is `200 OK`.
- [ ] Response contains array of `memories` retrieved from CockroachDB.

### 3. Incident Lifecycle Smoke Test

**Step A: Start Incident**
```bash
curl -s -X POST https://<unique-id>.lambda-url.us-east-1.on.aws/api/demo/start \
  -H "Content-Type: application/json"
```
- [ ] Returns `workflow_id`, status `INVESTIGATING`, step `1/4`.

**Step B: Simulate Worker Crash**
```bash
curl -s -X POST https://<unique-id>.lambda-url.us-east-1.on.aws/api/demo/crash \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "<WORKFLOW_ID_FROM_STEP_A>"}'
```
- [ ] Returns status `INTERRUPTED`, step `2/4`.

**Step C: Resume from Checkpoint**
```bash
curl -s -X POST https://<unique-id>.lambda-url.us-east-1.on.aws/api/demo/resume \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "<WORKFLOW_ID_FROM_STEP_A>"}'
```
- [ ] Returns status `COMPLETED`, step `4/4`.
- [ ] CockroachDB records validated memory `incident-208` and marks `incident-143` as superseded.

### 4. Bedrock Conversational Reasoning Test
```bash
curl -s -X POST https://<unique-id>.lambda-url.us-east-1.on.aws/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why is checkout latency high and what should we do?"}'
```
- [ ] Returns AI response citing `incident-208` (connection leak fix/rollback) rather than obsolete `incident-143` (connection pool sizing).

### 5. CloudWatch Logs Verification
Inspect CloudWatch log group `/aws/lambda/reassemble-agent`:
- [ ] No database timeout or SSL handshake errors.
- [ ] No Bedrock IAM `AccessDeniedException` errors.

---

## Rollback & Disaster Recovery Procedures

### 1. Lambda Code Rollback
If a deployment exhibits regressions:

1. **Re-publish Known Good ZIP**:
   ```powershell
   aws lambda update-function-code `
     --function-name reassemble-agent `
     --zip-file fileb://reassemble-lambda-backup.zip `
     --region us-east-1
   ```
2. **Lambda Versioning (If Configured)**:
   Point the production alias back to the previous version:
   ```powershell
   aws lambda update-alias `
     --function-name reassemble-agent `
     --name live `
     --function-version <PREVIOUS_STABLE_VERSION> `
     --region us-east-1
   ```

### 2. CockroachDB Data Reset Procedure
To wipe test incident workflows or reset the memory store for a fresh demo run, execute in CockroachDB SQL Console:

```sql
-- Reset workflows and audit log
DELETE FROM workflow_steps;
DELETE FROM workflows;
DELETE FROM audit_log;

-- Reset memories back to seed state
DELETE FROM memories;
```
When the Lambda function is invoked next, `seed_memories(c)` will automatically re-populate the standard baseline demo memories.
