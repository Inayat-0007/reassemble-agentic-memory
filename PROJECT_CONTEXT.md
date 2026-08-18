# REASSEMBLE — Project Context & File Map

> Auto-generated: 2026-08-18 21:05 IST
> Project: REASSEMBLE — Durable Agent Memory
> Status: Hackathon MVP (Active Development)
> Deadline: 2026-08-19 02:30 IST

## Project Purpose

REASSEMBLE demonstrates an AI agent whose knowledge memory and execution state are durably persisted in CockroachDB. Amazon Bedrock provides reasoning and embeddings; AWS Lambda provides the serverless runtime.

**Core thesis**: *"RAG retrieves. Reassemble reconstructs."*

---

## Directory Structure

```
reassemble-starter/
│
├── lambda_function.py          # Main application (Lambda handler + embedded UI)
├── schema.sql                  # CockroachDB database schema (4 tables + vector index)
├── requirements.txt            # Python dependencies (pg8000)
├── README.md                   # Project overview and setup guide
├── LICENSE                     # MIT License
├── .env.example                # Environment variable template
├── .gitignore                  # Git exclusion rules
│
├── .cursor/                    # Cursor IDE configuration
│   └── mcp.json.example        # CockroachDB MCP server config template
│
├── .github/                    # GitHub community files
│   └── CONTRIBUTING.md         # Contribution guidelines
│
├── docs/                       # Documentation root
│   ├── architecture.md         # System architecture with ASCII diagrams
│   ├── prd.md                  # Product Requirements Document
│   ├── mrd.md                  # Market Requirements Document
│   ├── demo-script.md          # 3-minute demo script
│   │
│   ├── design/                 # Technical design documents
│   │   ├── system-design.md    # System architecture & data flows
│   │   ├── database-design.md  # Schema, vector indexing, memory lifecycle
│   │   ├── api-design.md       # API endpoints specification
│   │   └── memory-algorithm.md # REASSEMBLE memory algorithm (11 steps)
│   │
│   ├── workflows/              # Process documentation
│   │   ├── development-workflow.md   # Local dev setup & coding workflow
│   │   ├── deployment-workflow.md    # Lambda build, deploy, Function URL
│   │   └── demo-workflow.md         # Detailed demo execution plan
│   │
│   └── brainstorm/             # Ideas and creative exploration
│       └── ideas.md            # Future features, judge angles, quotes
│
├── rules/                      # Project rules and standards
│   ├── coding-standards.md     # Python style, DB patterns, security
│   ├── commit-conventions.md   # Conventional commits, branch naming
│   ├── project-rules.md       # Scope boundaries, priorities, DO NOT list
│   └── ai-agent-rules.md      # Agent behavior: memory, supersession, audit
│
├── tracking/                   # Project tracking and history
│   ├── changelog.md            # Version changelog (Keep a Changelog format)
│   ├── decision-log.md         # Architectural decisions with rationale
│   ├── progress-tracker.md     # Checkpoint A-F task tracker
│   └── session-notes.md        # Development session logs
│
├── scripts/                    # Build and deployment automation
│   ├── build.ps1               # Build Lambda ZIP package
│   ├── deploy.ps1              # Deploy to AWS Lambda
│   └── test-local.ps1          # Local testing harness
│
└── PROJECT_CONTEXT.md          # This file — project map and context
```

---

## Technology Stack

| Layer | Technology | Identifier |
|---|---|---|
| Runtime | AWS Lambda | Python 3.11+ |
| Reasoning LLM | Amazon Bedrock | amazon.nova-lite-v1:0 |
| Embeddings | Amazon Bedrock | amazon.titan-embed-text-v2:0 |
| Database | CockroachDB Cloud | Basic/Serverless |
| Vector Index | CockroachDB | Distributed VECTOR(1024) |
| DB Driver | pg8000 | >=1.31, <2 |
| MCP Server | CockroachDB Cloud | Managed MCP (HTTPS) |
| Frontend | Embedded HTML/JS | Single-page in Lambda |

## Database Tables

| Table | Purpose | Key Columns |
|---|---|---|
| `memories` | Semantic knowledge store | embedding, content, confidence, status, source |
| `workflows` | Workflow execution state | workflow_id, status, last_completed_step |
| `workflow_steps` | Step-level checkpoints | step_number, name, status, result |
| `audit_log` | Event audit trail | action, details, created_at |

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Serve browser UI |
| POST | `/api/memories` | List semantic memories |
| POST | `/api/chat` | Chat with memory-augmented agent |
| POST | `/api/demo/start` | Start incident workflow |
| POST | `/api/demo/crash` | Simulate worker crash |
| POST | `/api/demo/resume` | Resume from checkpoint |

## Key Files — Quick Reference

| Need | File |
|---|---|
| Understand the app | `lambda_function.py` |
| Set up database | `schema.sql` |
| Configure secrets | `.env.example` |
| Build for Lambda | `scripts/build.ps1` |
| Deploy to AWS | `scripts/deploy.ps1` |
| Test locally | `scripts/test-local.ps1` |
| Run the demo | `docs/workflows/demo-workflow.md` |
| Project priorities | `rules/project-rules.md` |
| Track progress | `tracking/progress-tracker.md` |

---

## CockroachDB Features Used (Hackathon Requirement: ≥2)

1. **Distributed Vector Indexing** — `CREATE VECTOR INDEX` on `memories.embedding` for semantic similarity search
2. **Managed MCP Server** — AI dev/ops access to live CockroachDB cluster via `.cursor/mcp.json`

## AWS Services Used

1. **Amazon Bedrock** — Nova Lite (reasoning) + Titan Embeddings V2 (1024-dim vectors)
2. **AWS Lambda** — Serverless agent runtime with Function URL

---

*Last updated: 2026-08-18 21:05 IST*
