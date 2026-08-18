# REASSEMBLE — Remember. Recover. Learn.

**Tagline:** A durable agentic workflow engine backed by CockroachDB vector search and state machine synchronization to survive worker crashes, maintain long-term memory, and implement autonomous memory supersession.

---

## 💡 The Inspiration
AI agents are increasingly used to automate complex multi-step processes like incident remediation, data processing, and user engagement. However, they face two systemic failures:
1. **Volatile Execution State:** If a background worker crashes in the middle of a 4-step workflow, the agent loses its call-stack state, resulting in duplicated actions or orphaned operations.
2. **Stale Context Retrieval (RAG Contradictions):** Traditional RAG systems query vector databases based on similarity, which frequently retrieves outdated recommendations (e.g. *Runbook #12: Increase pool size*) instead of the newly validated lessons (e.g. *Incident #208: Pool changes do not fix the connection leak*).

**REASSEMBLE** was built to solve both challenges by utilizing CockroachDB as a single source of truth for both **durable state machines** and **dynamic vector memory**.

---

## ⚙️ What it Does
REASSEMBLE is a serverless MVP containing:
- **Durable State Engine:** Runs multi-step incident investigation workflows, committing transactional progress checkpoints to CockroachDB at every step.
- **Simulated Crash/Recovery Flow:** Demonstrates that if a worker crashes mid-workflow, a newly spawned replacement worker instantly reconstructs the execution context from CockroachDB and safely resumes from the exact checkpoint.
- **Dynamic Semantic Memory:** Harnesses 1024-dimensional vector embeddings stored directly in CockroachDB (`VECTOR` type with cosine distance index `<=>`) to query long-term memory.
- **Autonomous Memory Supersession:** When a resumed workflow resolves an incident, it commits the verified resolution to memory while setting a deprecation relation on conflicting past instructions. Future agent reasoning queries automatically favor the validated lesson.

---

## 🛠️ How We Built It
- **Database:** CockroachDB Cloud (Serverless) for relational consistency, distributed ACID transaction checkpointing, and vector index calculations.
- **Backend:** AWS Lambda (Python runtime) serving a public REST API and function URL.
- **Model Integration:** Amazon Bedrock (Nova Lite for reasoning, Titan Embeddings V2 for vector mapping) with a robust, zero-dependency local deterministic fallback to ensure execution continuity under any AWS account limit.
- **Developer Tools:** Cursor IDE configured with the **CockroachDB Managed MCP** server (`https://cockroachlabs.cloud/mcp`) for direct schema introspection.

---

## 🛡️ Value Proposition
> *"RAG retrieves. Reassemble reconstructs."*

For enterprise SRE and operations teams, REASSEMBLE guarantees:
1. **No Lost State:** Worker crash/restart overhead drops to milliseconds since checkpoints are transactionally safe in CockroachDB.
2. **Context Integrity:** Eliminates "AI hallucination" from conflicting historical runbooks by resolving contradictions right at the database query layer.

---

## 🔗 Project Links
- **GitHub Repository:** [https://github.com/Inayat-0007/reassemble-agentic-memory](https://github.com/Inayat-0007/reassemble-agentic-memory)
- **Live Demo Endpoint:** [https://wdixxgldo6nkydfcncocpvdqu40ukjkt.lambda-url.us-east-1.on.aws/](https://wdixxgldo6nkydfcncocpvdqu40ukjkt.lambda-url.us-east-1.on.aws/)
