# REASSEMBLE — Architecture Overview

> **"The model can fail. The worker can fail. The agent's memory doesn't have to."**

## System Architecture

```
                    REASSEMBLE
              "Remember. Recover. Learn."
                        │
                        ▼
                   AWS Lambda
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
    Amazon Nova Lite        Titan Embeddings V2
      (reasoning)            (1024-dim vectors)
            │                       │
            └───────────┬───────────┘
                        ▼
                   CockroachDB
            ┌───────────┼───────────┐
            ▼           ▼           ▼
         Memory      Workflow     Audit
         vectors      state        log
```

## Data Flow — Chat Query

```
User Question
     ↓
Titan Embeddings V2
     ↓
1024-dimensional vector
     ↓
CockroachDB Vector Index (cosine distance)
     ↓
Top-K relevant memories
     ↓
Context assembly (confidence + validity + supersession)
     ↓
Amazon Nova Lite (reasoning)
     ↓
Answer + memory trace
```

## Data Flow — Crash Recovery

```
Agent starts investigation
     ↓
CockroachDB checkpoint (step 1)
     ↓
Memory retrieval checkpoint (step 2)
     ↓
   ⚠ WORKER CRASH ⚠
     ↓
New worker starts
     ↓
Reads CockroachDB (reconstructs state)
     ↓
Continues from checkpoint 2
     ↓
Validates hypothesis (step 3)
     ↓
Commits resolution memory (step 4)
     ↓
Supersedes stale knowledge
     ↓
COMPLETED ✅
```

## Component Responsibilities

| Component | Responsibility |
|---|---|
| **AWS Lambda** | Serverless runtime, HTTP handler, API routing, HTML serving |
| **Amazon Nova Lite** | LLM reasoning over reassembled context |
| **Titan Embeddings V2** | Generates 1024-dim semantic vectors for memory storage/retrieval |
| **CockroachDB** | Durable storage for semantic memories, workflow state, audit events |
| **CockroachDB Vector Index** | Distributed cosine-distance similarity search |
| **CockroachDB MCP** | AI dev/ops tooling for schema inspection and query verification |
| **Browser UI** | Single-page demo interface embedded in Lambda response |

## Three Kinds of Memory

```
┌─────────────────────────────────────────────────────┐
│                  AGENT MEMORY                        │
├─────────────────┬──────────────────┬────────────────┤
│  KNOWLEDGE      │  EXECUTION       │  AUDIT         │
│  (memories)     │  (workflows +    │  (audit_log)   │
│                 │   workflow_steps) │                │
│  What do we     │  What was the    │  What did the  │
│  know?          │  agent doing?    │  agent do?     │
│                 │                  │                │
│  • embedding    │  • workflow_id   │  • action      │
│  • content      │  • step_number   │  • details     │
│  • confidence   │  • status        │  • timestamp   │
│  • source       │  • result        │                │
│  • status       │  • checkpoint    │                │
│  • validity     │                  │                │
└─────────────────┴──────────────────┴────────────────┘
```

## REASSEMBLE vs Normal RAG

```
NORMAL RAG                    REASSEMBLE
─────────                     ──────────
Question                      Question
   ↓                             ↓
Top 5 chunks                  Semantic retrieval
   ↓                          + Structured state
LLM                           + Temporal validity
                              + Confidence scoring
                              + Supersession check
                                 ↓
                              Context reconstruction
                                 ↓
                              LLM reasoning
                                 ↓
                              Action + checkpoint
                                 ↓
                              New validated memory
```

**"RAG retrieves. Reassemble reconstructs."**

## Technology Stack

| Layer | Technology | Version/Model |
|---|---|---|
| Runtime | AWS Lambda | Python 3.11+ |
| Reasoning | Amazon Bedrock | amazon.nova-lite-v1:0 |
| Embeddings | Amazon Bedrock | amazon.titan-embed-text-v2:0 |
| Database | CockroachDB Cloud | Basic/Serverless |
| DB Driver | pg8000 | >=1.31, <2 |
| Vector Index | CockroachDB | Distributed Vector Index |
| MCP | CockroachDB Cloud | Managed MCP Server |
| Frontend | Embedded HTML/JS | Single-page app in Lambda |

## Security Model (Hackathon MVP)

- Lambda Function URL with `Auth: NONE` (demo only)
- CockroachDB Cloud with SSL (`sslmode=verify-full`)
- Environment variables for secrets (never in code)
- `.gitignore` excludes `.env` and `mcp.json`
- No production secrets in frontend or source control

---

*Last updated: 2026-08-18 21:00 IST*
