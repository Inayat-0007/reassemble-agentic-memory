# ⚡ REASSEMBLE — Durable Agentic Memory Engine
### *Remember. Recover. Learn. — Built with CockroachDB & AWS*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-AWS%20Lambda%20URL-7c3aed?style=for-the-badge&logo=amazon-aws)](https://wdixxgldo6nkydfcncocpvdqu40ukjkt.lambda-url.us-east-1.on.aws/)
[![CockroachDB](https://img.shields.io/badge/Database-CockroachDB%20Serverless-6933FF?style=for-the-badge&logo=cockroachlabs)](https://cockroachlabs.cloud/)
[![AWS Lambda](https://img.shields.io/badge/Compute-AWS%20Lambda-FF9900?style=for-the-badge&logo=awslambda)](https://aws.amazon.com/lambda/)
[![Vector Search](https://img.shields.io/badge/Vector%20Search-1024--dim%20Cosine-10b981?style=for-the-badge)](https://www.cockroachlabs.com/docs/stable/vector-search)

> **Submission for the CockroachDB x AWS Hackathon (Agentic Memory Track)**  
> **Live Production Dashboard:** [https://wdixxgldo6nkydfcncocpvdqu40ukjkt.lambda-url.us-east-1.on.aws/](https://wdixxgldo6nkydfcncocpvdqu40ukjkt.lambda-url.us-east-1.on.aws/)

---

## 🎯 The Core Thesis

Modern AI agents execute complex, multi-step production workflows. However, they suffer from two fundamental vulnerabilities:
1. **Stateless Compute Vulnerability:** When a background worker process crashes or times out mid-task, in-memory execution state is permanently lost.
2. **Semantic Contradiction Fragility:** Traditional RAG vector databases retrieve historical advice without understanding chronological supersession or evidence validation.

**REASSEMBLE** treats agent memory and execution state not as ephemeral chat history, but as an **ACID-compliant, distributed database system of record** powered by **CockroachDB**.

> *"Compute and AI workers are disposable. Agent memory and workflow state must be permanent."*

---

## 🏗️ System Architecture

```text
               ┌─────────────────────────────────────────────────────────┐
               │         Cursor AI / Developer Environment               │
               └────────────────────────────┬────────────────────────────┘
                                            │ AI Schema Introspection
                                            ▼
                               ┌───────────────────────────┐
                               │  CockroachDB Managed MCP  │
                               └────────────┬──────────────┘
                                            │
                                            ▼
┌───────────────────────┐      ┌───────────────────────────┐
│     User Browser      │      │    COCKROACHDB CLUSTER    │
│  (Next-Gen 2026 UI)   │      │       (Asia-South1)       │
└───────────┬───────────┘      ├───────────────────────────┤
            │ REST / JSON      │ • workflows (ACID State)  │
            ▼                  │ • workflow_steps          │
┌───────────────────────┐ SQL  │ • memories (VECTOR 1024)  │
│      AWS LAMBDA       ├─────►│ • audit_log               │
│   (Serverless REST)   │      └────────────▲──────────────┘
└───────────┬───────────┘                   │
            │ Embeddings & Reasoning        │ Checkpoints & Cosine Search
            ▼                               │
┌───────────────────────┐                   │
│    AMAZON BEDROCK     ├───────────────────┘
│ (Nova Lite + TitanV2) │
└───────────────────────┘
```

---

## 💎 Two Core CockroachDB Capabilities

### 1. Distributed Vector Indexing (`VECTOR(1024) <=>`)
We eliminate the need for a separate vector database (like Pinecone or Qdrant). CockroachDB unifies relational tables and vector embeddings in a single ACID engine:
```sql
CREATE TABLE IF NOT EXISTS memories (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_type VARCHAR(64) NOT NULL,
    content STRING NOT NULL,
    confidence FLOAT8 NOT NULL,
    source VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    supersedes UUID REFERENCES memories(memory_id),
    embedding VECTOR(1024),
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- Cosine Distance Vector Index
CREATE VECTOR INDEX IF NOT EXISTS memories_embedding_idx 
ON memories (embedding);
```

### 2. CockroachDB Managed MCP Server
Configured in `.cursor/mcp.json` to give AI development tools native schema introspection and SQL query execution directly through the Model Context Protocol.

---

## 🎬 The 3-Minute Judging Demo Flow

| Step | Action | What Happens in the Database | What It Proves |
|---|---|---|---|
| **1** | **Start Incident** | Commits row to `workflows` (`status = 'INVESTIGATING'`, `last_completed_step = 1`). | Durable state is created as an ACID transaction, not held in volatile Lambda memory. |
| **2** | **Controlled Failure Injection** | Updates row to `status = 'INTERRUPTED'`, `last_completed_step = 2`. | Tests resilience against unexpected process termination. |
| **3** | **Resume from Checkpoint** | New stateless worker queries CockroachDB, reconstructs state, finishes steps 3 & 4, commits `status = 'COMPLETED'`. | State recovery is 100% database-backed with zero data loss. |
| **4** | **Ask Agent** (`Why is checkout latency high?`) | Queries `memories` via cosine similarity vector search. Identifies that validated `incident-208` (v2.8 leak) supersedes `incident-143` (pool size). | **Memory Evolution:** Agent recognizes conflicting historical data and provides validated remediation. |

---

## 🛡️ Truth in Engineering & Reality Verification

To ensure transparent and judge-proof evaluation:

| Component | Status | Implementation Details |
|---|---|---|
| **CockroachDB Cluster** | 🟢 **LIVE** | Real CockroachDB Cloud Serverless cluster in `asia-south1`. |
| **Workflow State Machine** | 🟢 **LIVE** | Real PostgreSQL ACID transactions (`workflows`, `workflow_steps`). |
| **Distributed Vector Search** | 🟢 **LIVE** | Real `VECTOR(1024)` index with `<=>` Cosine Distance queries. |
| **Checkpoint Recovery** | 🟢 **LIVE** | Real state reconstruction from database checkpoints. |
| **Memory Supersession** | 🟢 **LIVE** | Real database relationship (`supersedes` foreign key pointer). |
| **AWS Lambda Runtime** | 🟢 **LIVE** | Live public Function URL deployed in `us-east-1`. |
| **Failure Injection** | 🟡 **CONTROLLED** | Deliberately injected worker interruption after Checkpoint 2. |
| **Memory Dataset** | 🟡 **SEEDED FIXTURE**| 5 pre-seeded demonstration vectors for deterministic evaluation. |
| **AI Engine (Bedrock)**| 🟡 **EVALUATION MODE**| Uses IAM Execution Role with deterministic fallback for reproducible evaluation under zero-quota sandboxes. |

---

## 🚀 Local Setup & Replication

### 1. Prerequisites
- Python 3.11+
- CockroachDB Cloud cluster (Serverless or Dedicated)

### 2. Installation
```bash
git clone https://github.com/Inayat-0007/reassemble-agentic-memory.git
cd reassemble-agentic-memory

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Initialize Database Schema
Run the SQL definitions in CockroachDB SQL Console:
```bash
cockroach sql --url "YOUR_COCKROACHDB_CONNECTION_STRING" -f schema.sql
```

### 4. Run Live E2E Verification Suite
```bash
python scripts/full_e2e_test.py
```
*Expected Output:* **10/10 Tests Passed (100% Success Rate)**.

---

## 🔒 Security & Credential Hygiene
- **Zero Secrets Tracked:** The repository contains zero hardcoded API keys, database passwords, or AWS secrets.
- **IAM Role Fallback:** The live AWS Lambda function authenticates via its internal AWS IAM Execution Role (`reassemble-agent-role-11zpseyh`).

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
