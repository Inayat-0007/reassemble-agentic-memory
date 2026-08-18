# REASSEMBLE — Durable Agent Memory

**Remember. Recover. Learn.**

Reassemble is a hackathon MVP showing an agent whose **knowledge memory** and **execution state** are persisted in CockroachDB. Amazon Bedrock provides reasoning and embeddings; AWS Lambda provides the agent runtime.

## Why this architecture?

LLM reasoning is non-deterministic, so important state must not live only in a Lambda runtime. Reassemble stores:

- semantic memory and embeddings in `memories`
- workflow checkpoints in `workflows` and `workflow_steps`
- audit events in `audit_log`

A failed worker can be replaced by a new worker that reconstructs the workflow from CockroachDB.

## Hackathon technology

### CockroachDB
1. **Distributed Vector Indexing** — semantic retrieval over long-term agent memory.
2. **Managed MCP Server** — development/agent access to the live CockroachDB cluster for schema inspection and query verification.

### AWS
- **Amazon Bedrock** — Amazon Nova Lite for reasoning and Titan Text Embeddings V2 for embeddings.
- **AWS Lambda** — serverless agent runtime and public Function URL.

## 1. Create a CockroachDB Cloud cluster

Create a CockroachDB Cloud Basic/Serverless cluster. Copy the SQL connection string from the Connect dialog and keep the password private.

The app expects a PostgreSQL-style URL such as:

`postgresql://USER:PASSWORD@HOST:26257/defaultdb?sslmode=verify-full`

## 2. Create the schema

Open CockroachDB Cloud > SQL Console and paste `schema.sql`.

## 3. Enable Bedrock model access

In the AWS Bedrock console, make sure your chosen AWS region supports:
- `amazon.nova-lite-v1:0`
- `amazon.titan-embed-text-v2:0`

Then test Bedrock with the AWS console or AWS CLI.

## 4. Local test

Install Python 3.11+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Set environment variables:

```bash
# Windows PowerShell
$env:CRDB_URL="postgresql://USER:PASSWORD@HOST:26257/defaultdb?sslmode=verify-full"
$env:AWS_REGION="us-east-1"
$env:CHAT_MODEL_ID="amazon.nova-lite-v1:0"
$env:EMBED_MODEL_ID="amazon.titan-embed-text-v2:0"
```

For local testing, invoke `lambda_handler` through a small harness or deploy directly to Lambda. The browser app is returned from `/`.

## 5. Deploy to Lambda

Create a Lambda function using Python 3.11 or newer.

Build a deployment zip:

```bash
mkdir package
pip install -r requirements.txt -t package
copy lambda_function.py package\
cd package
powershell Compress-Archive * ../reassemble-lambda.zip
cd ..
```

On macOS/Linux:

```bash
mkdir -p package
pip install -r requirements.txt -t package
cp lambda_function.py package/
cd package
zip -r ../reassemble-lambda.zip .
cd ..
```

Upload `reassemble-lambda.zip` to Lambda.

Set handler:

`lambda_function.lambda_handler`

Set environment variables:

- `CRDB_URL`
- `AWS_REGION`
- `CHAT_MODEL_ID`
- `EMBED_MODEL_ID`

### Lambda IAM permissions

The Lambda execution role needs permission to call Bedrock runtime APIs, at minimum:

- `bedrock:InvokeModel`
- `bedrock:Converse`

## 6. Create a public Function URL

Lambda > Configuration > Function URL > Create.

For a quick hackathon demo:
- Auth type: `NONE`
- CORS: allow your demo origin or `*`

AWS will give you a URL like:

`https://xxxx.lambda-url.us-east-1.on.aws/`

Open it in a browser.

## 7. Configure CockroachDB Managed MCP for your coding agent

In Cursor, create `.cursor/mcp.json` from `.cursor/mcp.json.example`.

Get:
- Cluster ID from the CockroachDB Cloud cluster URL.
- A CockroachDB service-account API key.

The managed MCP server uses HTTPS and supports service-account API-key authentication. It exposes tools such as `list_tables`, `get_table_schema`, `select_query`, and write tools when write consent is granted.

Use MCP from your coding agent to:
- inspect the live schema
- verify workflow records
- run `SELECT` queries
- show the judge that the database is directly available to an AI coding/operations agent

## Demo flow

1. Start Incident
2. Simulate Worker Crash
3. Resume from Checkpoint
4. Ask Agent: `Why is checkout latency high and what should we do?`
5. Refresh Memory

### Key story

`Agent action -> durable checkpoint -> worker failure -> new worker -> state reconstruction -> learning`

## Security note

This hackathon MVP uses a public Lambda Function URL. Do not put production secrets in frontend code, source control, or client-side JavaScript. For a production deployment, use authentication, least-privilege IAM, and a secret manager.
