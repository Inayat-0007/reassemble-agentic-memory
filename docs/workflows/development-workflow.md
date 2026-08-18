# REASSEMBLE — Local Development & Engineering Workflow

This document outlines the end-to-end development workflow for **REASSEMBLE — Durable Agent Memory**. It provides comprehensive instructions for local environment setup, environment variable configuration, local testing harnesses, code style standards, Git branching models, and pre-commit verification.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Local Setup Steps](#local-setup-steps)
4. [Environment Variables Reference](#environment-variables-reference)
5. [Local Testing Approach](#local-testing-approach)
   - [CLI Testing Harness](#1-cli-testing-harness)
   - [Local HTTP Mock Server](#2-local-http-mock-server)
   - [CockroachDB Schema & Managed MCP Verification](#3-cockroachdb-schema--managed-mcp-verification)
6. [Code Style & Engineering Guidelines](#code-style--engineering-guidelines)
7. [Git Workflow & Branching Strategy](#git-workflow--branching-strategy)
8. [Pre-Commit & Quality Checklist](#pre-commit--quality-checklist)

---

## Architecture Overview

REASSEMBLE is a resilient, serverless AI incident-response agent whose **knowledge memory** and **execution state** are persisted in **CockroachDB**.

```
┌─────────────────────────────────────────────────────────────┐
│                       Developer Machine                     │
│  ┌──────────────────────┐        ┌────────────────────────┐ │
│  │ Python 3.11+ Runtime │        │ Cursor / VS Code (MCP) │ │
│  │  - pg8000 (Pure Py)  │        │  - .cursor/mcp.json    │ │
│  │  - boto3 (Bedrock)   │        │  - Schema Introspect   │ │
│  └──────────┬───────────┘        └───────────┬────────────┘ │
└─────────────┼────────────────────────────────┼──────────────┘
              │ Direct SQL                     │ Managed MCP
              ▼                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    CockroachDB Cloud Basic                  │
│  - workflows & workflow_steps (Execution Checkpoints)       │
│  - memories (Distributed VECTOR(1024) Index)                │
│  - audit_log (Tamper-evident State History)                 │
└─────────────────────────────▲───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                       Amazon Bedrock                        │
│  - amazon.nova-lite-v1:0 (Reasoning & Synthesis)            │
│  - amazon.titan-embed-text-v2:0 (1024-dim Embeddings)       │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before setting up the repository locally, ensure the following tooling is installed and accessible in your system `PATH`:

- **Python**: Version `3.11` or newer (`python --version`)
- **Git**: Version `2.30+` (`git --version`)
- **AWS CLI**: Version `2.x` configured with Bedrock access (`aws sts get-caller-identity`)
- **CockroachDB Cloud Account**: Active Serverless/Basic cluster with database connection string
- **Shell**: PowerShell (Windows) or Bash/Zsh (macOS/Linux)

---

## Local Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/<your-org-or-username>/reassemble.git
cd reassemble
```

### 2. Create and Activate a Python Virtual Environment

Isolate project dependencies using Python's standard `venv` module:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> [!NOTE]
> If you encounter PowerShell script execution policy restrictions, run:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**macOS / Linux (Bash/Zsh):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the core runtime dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

To install optional development and linting tools:

```bash
pip install flake8 black pytest
```

### 4. Configure Environment Variables

Copy `.env.example` to create your local `.env` file:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Edit `.env` with your active CockroachDB connection string and AWS credentials.

---

## Environment Variables Reference

The following environment variables control runtime database connectivity and AWS Bedrock model invocation:

| Variable | Type | Default | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `CRDB_URL` | String | *Required* | CockroachDB Cloud PostgreSQL connection URL with TLS/SSL parameters | `postgresql://user:pass@host.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full` |
| `AWS_REGION` | String | `us-east-1` | AWS Region where Bedrock foundation models are enabled | `us-east-1` |
| `CHAT_MODEL_ID` | String | `amazon.nova-lite-v1:0` | Amazon Bedrock LLM Model ID for conversational reasoning | `amazon.nova-lite-v1:0` |
| `EMBED_MODEL_ID`| String | `amazon.titan-embed-text-v2:0`| Bedrock Embedding Model ID (1024 dimensions) | `amazon.titan-embed-text-v2:0` |

### Setting Environment Variables in Shell Sessions

**Windows (PowerShell):**
```powershell
$env:CRDB_URL="postgresql://user:password@cluster-name.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full"
$env:AWS_REGION="us-east-1"
$env:CHAT_MODEL_ID="amazon.nova-lite-v1:0"
$env:EMBED_MODEL_ID="amazon.titan-embed-text-v2:0"
```

**macOS / Linux (Bash/Zsh):**
```bash
export CRDB_URL="postgresql://user:password@cluster-name.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full"
export AWS_REGION="us-east-1"
export CHAT_MODEL_ID="amazon.nova-lite-v1:0"
export EMBED_MODEL_ID="amazon.titan-embed-text-v2:0"
```

---

## Local Testing Approach

Because REASSEMBLE is packaged as an AWS Lambda function with embedded web assets, you can test the application locally using two primary methods without deploying to AWS.

### 1. CLI Testing Harness

Create a scratch script `test_local.py` to directly invoke the `lambda_handler` function with simulated API Gateway / Lambda Function URL events:

```python
import json
import os
from lambda_function import lambda_handler

def run_test(method, path, body=None):
    print(f"\n--- Testing {method} {path} ---")
    event = {
        "rawPath": path,
        "requestContext": {
            "http": {
                "method": method
            }
        },
        "body": json.dumps(body) if body else "{}"
    }
    response = lambda_handler(event, None)
    print(f"Status: {response['statusCode']}")
    try:
        body_data = json.loads(response["body"])
        print("Response Body:\n", json.dumps(body_data, indent=2))
    except Exception:
        print(f"Response Body (Raw): {response['body'][:100]}...")

if __name__ == "__main__":
    # 1. Test Root UI GET
    run_test("GET", "/")

    # 2. Test Memories Retrieval
    run_test("POST", "/api/memories")

    # 3. Test Workflow Lifecycle: Start
    start_res = lambda_handler({
        "rawPath": "/api/demo/start",
        "requestContext": {"http": {"method": "POST"}},
        "body": "{}"
    }, None)
    workflow_id = json.loads(start_res["body"])["workflow_id"]
    print(f"\nCreated Workflow ID: {workflow_id}")

    # 4. Test Workflow Crash
    run_test("POST", "/api/demo/crash", {"workflow_id": workflow_id})

    # 5. Test Workflow Resume
    run_test("POST", "/api/demo/resume", {"workflow_id": workflow_id})

    # 6. Test Bedrock Agent Chat
    run_test("POST", "/api/chat", {
        "message": "Why is checkout latency high and what should we do?",
        "workflow_id": workflow_id
    })
```

Execute the test harness:

```powershell
python test_local.py
```

### 2. Local HTTP Mock Server

To interact with the frontend UI in a local browser, run a lightweight local HTTP server bridging standard browser requests to `lambda_handler`:

```python
# local_server.py
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from lambda_function import lambda_handler

class LocalLambdaHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._handle_req("OPTIONS")

    def do_GET(self):
        self._handle_req("GET")

    def do_POST(self):
        self._handle_req("POST")

    def _handle_req(self, method):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        event = {
            "rawPath": self.path,
            "requestContext": {"http": {"method": method}},
            "body": body
        }

        res = lambda_handler(event, None)
        self.send_response(res["statusCode"])
        for k, v in res.get("headers", {}).items():
            self.send_header(k, v)
        self.end_headers()

        response_body = res["body"]
        if isinstance(response_body, str):
            self.wfile.write(response_body.encode("utf-8"))
        else:
            self.wfile.write(json.dumps(response_body).encode("utf-8"))

if __name__ == "__main__":
    server = HTTPServer(("localhost", 8000), LocalLambdaHandler)
    print("REASSEMBLE Local Dev Server listening on http://localhost:8000")
    server.serve_forever()
```

Run:
```powershell
python local_server.py
```
Open `http://localhost:8000` in your browser.

### 3. CockroachDB Schema & Managed MCP Verification

To inspect and verify live database state during development:

1. **CockroachDB Cloud SQL Console**:
   Paste and execute queries from `schema.sql`.
2. **Cursor Managed MCP Integration**:
   Configure `.cursor/mcp.json` with your CockroachDB Cloud Cluster ID and Service Account API Key:
   ```json
   {
     "mcpServers": {
       "cockroachdb-cloud": {
         "type": "http",
         "url": "https://cockroachlabs.cloud/mcp",
         "headers": {
           "mcp-cluster-id": "YOUR_CLUSTER_ID",
           "Authorization": "Bearer YOUR_SERVICE_ACCOUNT_API_KEY"
         }
       }
     }
   }
   ```
   Use Cursor Composer or chat to prompt: `"Use CockroachDB MCP to show row counts in workflows and memories."`

---

## Code Style & Engineering Guidelines

To maintain rapid development velocity without sacrificing reliability:

1. **Pure Python Database Driver (`pg8000`)**:
   - Do **NOT** introduce C-compiled dependencies (such as `psycopg2` or `psycopg2-binary`).
   - `pg8000` guarantees 100% portable deployment across Windows, macOS, and AWS Lambda Linux runtimes.
2. **Parameterized SQL Queries**:
   - Always use `%s` parameter substitution with parameterized query tuples.
   - Never use f-strings or manual string concatenation for SQL statements.
   ```python
   # Correct
   cur.execute("SELECT * FROM workflows WHERE workflow_id = %s", (wid,))

   # Incorrect (Vulnerable to SQL injection)
   cur.execute(f"SELECT * FROM workflows WHERE workflow_id = '{wid}'")
   ```
3. **Deterministic Error Handling**:
   - Return structured HTTP JSON error objects `{ "error": str(e) }` with appropriate status codes (`400`, `404`, `500`).
4. **Single-File Architecture**:
   - Keep core Lambda logic in `lambda_function.py` to prevent packaging and import resolution mismatches during deployment.
5. **PEP 8 Standards**:
   - 4-space indentation.
   - Descriptive function and variable names (`snake_case`).
   - Constants defined at module top in `UPPER_SNAKE_CASE`.

---

## Git Workflow & Branching Strategy

We follow a streamlined GitHub-flow model optimized for fast hackathon iterations.

```
       feat/vector-retrieval
      o───────o───────o
     /                 \
main ───────────────────●───────────● (Deploy to Lambda)
                         \         /
                          o───────o
                         fix/pg8000-ssl
```

### Branch Naming Conventions

- `feat/<feature-name>`: New capabilities (e.g., `feat/vector-retrieval`, `feat/memory-supersession`)
- `fix/<bug-description>`: Bug fixes (e.g., `fix/pg8000-ssl-context`, `fix/bedrock-converse-payload`)
- `docs/<topic>`: Documentation enhancements (e.g., `docs/deployment-guide`, `docs/demo-script`)
- `chore/<task>`: Dependency updates, CI/CD tweaks, cleanup (e.g., `chore/requirements-lock`)

### Conventional Commits Format

Commit messages should adhere to the Conventional Commits specification:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: A new user-facing feature or API endpoint
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

**Examples:**
```bash
git commit -m "feat(memory): implement vector similarity query using Titan V2 embeddings"
git commit -m "fix(db): configure TLS default context in pg8000 connection factory"
git commit -m "docs(workflows): add development and demo workflows"
```

---

## Pre-Commit & Quality Checklist

Before pushing changes or deploying to AWS Lambda, verify the following:

- [ ] **No Hardcoded Secrets**: Ensure passwords, API keys, and connection strings are NOT committed. `.env` must be in `.gitignore`.
- [ ] **Syntax Validation**: Run `python -m py_compile lambda_function.py` to verify syntax.
- [ ] **Code Formatting**: Run `flake8 lambda_function.py --max-line-length=120` or verify with `black`.
- [ ] **Database Connection Test**: Verify `pg8000` can connect and execute queries against CockroachDB Cloud.
- [ ] **AWS Bedrock Test**: Verify `bedrock.invoke_model` and `bedrock.converse` succeed without permission errors.
- [ ] **Local Harness Execution**: Run `python test_local.py` and verify all 6 endpoints return HTTP 200.
