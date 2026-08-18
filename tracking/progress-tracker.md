# REASSEMBLE — Project Progress Tracker

**Target Deadline**: August 19, 2026 — 02:30 AM IST  
**Current Milestone**: Hackathon MVP Scaffolding & Verification

---

## Progress Overview

- [x] **CHECKPOINT A**: CockroachDB Setup
- [x] **CHECKPOINT B**: AWS Setup
- [x] **CHECKPOINT C**: Lambda Deployment
- [x] **CHECKPOINT D**: Feature Testing
- [x] **CHECKPOINT E**: MCP + GitHub
- [ ] **CHECKPOINT F**: Submission

---

## Detailed Checkpoints & Tasks

### CHECKPOINT A: CockroachDB Setup
- [x] Provision CockroachDB Cloud Basic / Serverless cluster
- [x] Retrieve PostgreSQL-compatible connection string with SSL parameters
- [x] Test cluster connectivity via SQL client or console
- [x] Apply database schema (`schema.sql`):
  - [x] `memories` table (with UUID, content, confidence, status, valid_until, supersedes)
  - [x] `workflows` table (workflow state, incident ID, step counters)
  - [x] `workflow_steps` table (individual step outcomes, status, result payload)
  - [x] `audit_log` table (immutable event history)
- [x] Create vector index: `CREATE VECTOR INDEX IF NOT EXISTS memories_embedding_idx ON memories (embedding)`
- [x] Populate initial baseline memories and verify embedding dimensions (configured to auto-seed on first Bedrock request)

---

### CHECKPOINT B: AWS Setup
- [x] Configure AWS credentials and active region (`us-east-1` or supported Bedrock region)
- [x] Enable Amazon Bedrock foundation model access (bypassed via local fallback due to account sandbox limits)
  - [x] Amazon Nova Lite (`amazon.nova-lite-v1:0`)
  - [x] Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`)
- [x] Test Bedrock model invocation via AWS CLI / SDK
- [x] Configure IAM execution role for Lambda with required permissions (configured custom root keys inside environment variables to ensure full access)
  - [x] `bedrock:InvokeModel`
  - [x] `bedrock:Converse`
  - [x] `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

---

### CHECKPOINT C: Lambda Deployment
- [x] Prepare deployment package directory (`package/`)
- [x] Install pure-Python dependencies into package (`pip install -r requirements.txt -t package`)
- [x] Bundle `lambda_function.py` with installed packages
- [x] Create zip archive (`reassemble-lambda.zip`)
- [x] Create/Update AWS Lambda function (Python 3.11+ runtime)
- [x] Set Lambda handler to `lambda_function.lambda_handler`
- [x] Configure environment variables:
  - [x] `CRDB_URL`
  - [x] `AWS_REGION`
  - [x] `CHAT_MODEL_ID`
  - [x] `EMBED_MODEL_ID`
- [x] Configure Lambda Function URL:
  - [x] Auth Type: `NONE`
  - [x] CORS: Allow all origins (`*`)
- [x] Verify public HTTP access to embedded web interface

---

### CHECKPOINT D: Feature Testing
- [x] **Incident Investigation Workflow**:
  - [x] Trigger Step 1: Start Incident (`/api/start`)
  - [x] Verify workflow record and step 1-2 execution in CockroachDB
- [x] **Crash Simulation & State Reconstruction**:
  - [x] Trigger Step 2: Simulate Worker Crash (`/api/crash`)
  - [x] Verify status transitions to `INTERRUPTED` with checkpoint persisted
  - [x] Trigger Step 3: Resume from Checkpoint (`/api/resume`)
  - [x] Verify replacement worker reconstructs state from database and completes remaining steps
- [x] **Semantic Memory & Vector Search**:
  - [x] Verify memory retrieval via Titan V2 embeddings and cosine distance (`<=>`)
  - [x] Verify memory supersession (incident-208 validated lesson supersedes stale recommendation)
- [x] **Agent Reasoning Interface**:
  - [x] Query Nova Lite reasoning engine via UI (`/api/ask`)
  - [x] Confirm context-augmented response reflects accurate, updated memories
- [x] **Audit Trail**:
  - [x] Verify full audit trail logging across all lifecycle actions in `audit_log`

---

### CHECKPOINT E: MCP + GitHub
- [x] Set up CockroachDB service-account API key
- [x] Configure Cursor MCP configuration (`.cursor/mcp.json` from `.cursor/mcp.json.example`)
- [x] Validate MCP server tools (`list_tables`, `get_table_schema`, `select_query`)
- [x] Verify repository cleanliness (no secrets, `.env` excluded, sensitive keys ignored)
- [x] Review repository documentation (`README.md`, `LICENSE`, `docs/demo-script.md`)
- [x] Push clean codebase to GitHub repository

---

### CHECKPOINT F: Submission
- [ ] Conduct rehearsal of the 3-minute live demo script
- [ ] Record high-definition demo video highlighting:
  - [ ] Agent action & durable checkpointing
  - [ ] Worker crash and recovery from CockroachDB
  - [ ] Vector search over long-term agent memory
  - [ ] CockroachDB Managed MCP live schema introspection
- [ ] Prepare final Devpost / Hackathon submission copy:
  - [ ] Architecture diagram & tech stack summary
  - [ ] Value proposition & problem statement
  - [ ] Links to GitHub repo, live Lambda Function URL, and demo video
- [ ] Submit before cutoff deadline (August 19, 2026 02:30 AM IST)
