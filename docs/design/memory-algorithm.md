# The REASSEMBLE Memory Algorithm

**Project:** REASSEMBLE — Durable Agent Memory  
**Algorithm Specification:** 11-Step Crash-Resilient Knowledge Synthesis & State Reassembly  
**Core Technologies:** CockroachDB Distributed Vector Index + Amazon Bedrock (Nova Lite & Titan Embeddings V2)  

---

## 1. Algorithm Overview & Core Principles

Autonomous agents operating in production environments require more than static text retrieval; they require **durable episodic memory**, **probabilistic confidence filtering**, and **transactional state progression**. Traditional Retrieval-Augmented Generation (RAG) fails when operational facts change, worker processes crash, or contradictory hypotheses emerge over time.

The **REASSEMBLE Memory Algorithm** defines a closed-loop, crash-resilient cognitive cycle that unifies semantic memory search with relational checkpoint durability in CockroachDB.

```
       +-------------------------------------------------------------------------+
       |                     THE 11-STEP REASSEMBLE PIPELINE                     |
       +-------------------------------------------------------------------------+
                                            │
                                 [ 1. Extract Task Intent ]
                                            │
                             [ 2. Generate Semantic Vector ]
                                (Bedrock Titan Embeddings V2)
                                            │
                             [ 3. CockroachDB Vector Search ]
                                (Cosine Distance: <=> operator)
                                            │
                           [ 4. Retrieve Structured State ]
                                (Workflows & Step Checkpoints)
                                            │
                            [ 5. Validity & Status Filter ]
                                (Confidence, valid_until, active)
                                            │
                            [ 6. Multi-Factor Memory Rank ]
                              (Relevance + Confidence + Recency)
                                            │
                             [ 7. Reassemble Prompt Context ]
                                 (Structured Grounding Block)
                                            │
                             [ 8. Bedrock LLM Reasoning ]
                                 (Nova Lite Contradiction-Aware)
                                            │
                             [ 9. Commit Step Checkpoint ]
                               (CockroachDB ACID Transaction)
                                            │
                           [ 10. Write Validated Knowledge ]
                                (Insert New Empirical Fact)
                                            │
                           [ 11. Supersede Stale Knowledge ]
                                (Atomic Invalidation & Lineage)
                                            │
                                            ▼
                               [ Resilient Execution State ]
```

---

## 2. The 11-Step Memory Algorithm Pipeline

### Step 1: Extract Task Intent
When an incoming user request, alert event, or operational trigger enters the agent runtime, the agent parses the raw input into a normalized task intent string.
- Strips non-semantic noise, formats variable names, and pinpoints the core diagnostic subject (e.g., *"checkout latency spike after deployment v2.8"*).

### Step 2: Generate Semantic Embedding (Amazon Titan V2, 1024-dim)
The intent text is converted into a normalized, dense mathematical representation using Amazon Bedrock's `amazon.titan-embed-text-v2:0` model:
- **Dimensions:** 1024.
- **Normalization:** Vectors are $L_2$-normalized to unit length ($\|v\|_2 = 1.0$) at generation time (`{"dimensions": 1024, "normalize": True}`).
- **Input Text Truncation:** Text length is bounded to protect embedding limits while capturing full incident context.

### Step 3: Search CockroachDB Vector Index
The normalized vector is formatted into a SQL vector literal (`[v_1, v_2, ..., v_1024]`) and queried against CockroachDB:

```sql
SELECT id, memory_type, content, confidence, source, status, valid_until, supersedes
FROM memories
WHERE status = 'active'
ORDER BY embedding <=> $1::VECTOR
LIMIT 5;
```

CockroachDB evaluates the cosine distance operator (`<=>`) using its distributed vector index (`memories_embedding_idx`), retrieving candidate nearest-neighbor memories across distributed nodes with sub-second latency.

### Step 4: Retrieve Structured Workflow State
In parallel with semantic retrieval, the agent loads relational execution checkpoints:

```sql
SELECT workflow_id, status, incident, last_completed_step, total_steps 
FROM workflows 
WHERE workflow_id = $1;

SELECT step_number, name, status, result 
FROM workflow_steps 
WHERE workflow_id = $1 
ORDER BY step_number ASC;
```

This step reconstructs exact historical progress (e.g., whether Step 1 or Step 2 finished prior to an unexpected worker restart), ensuring execution never starts from zero.

### Step 5: Check Confidence, Validity, Status, and Supersession
Candidate memories undergo rigorous validation filtering before admission into the agent's working context:
- **Status Filter:** Stale memories marked `status = 'superseded'` or `status = 'invalidated'` are excluded from primary reasoning.
- **Temporal Shelf-Life:** Records where `valid_until IS NOT NULL AND valid_until < now()` are purged from active consideration.
- **Confidence Thresholding:** Memories with Bayesian confidence ratings below a defined threshold ($c < 0.60$) are demoted or flagged as unverified hypotheses.

### Step 6: Multi-Factor Memory Ranking
The candidate knowledge items are scored using a composite ranking formula balancing semantic alignment with empirical reliability:

$$\text{Score}(m) = w_1 \cdot \text{Sim}(q, m) + w_2 \cdot \text{Conf}(m) + w_3 \cdot \text{Recency}(m) + w_4 \cdot \text{Authority}(m)$$

Where:
- $\text{Sim}(q, m) = 1 - (\vec{q} \Leftrightarrow \vec{m})$ (Cosine similarity)
- $\text{Conf}(m) \in [0, 1]$ (Stored Bayesian confidence rating)
- $\text{Recency}(m) = \exp(-\lambda \cdot \Delta t)$ (Exponential temporal decay)
- $\text{Authority}(m)$ (Weight assigned based on `memory_type`, e.g., `validated_lesson` > `incident` hypothesis)

### Step 7: Reassemble Context
The filtered and ranked memories are synthesized into a structured context block injected into the LLM system prompt:

```text
[validated_lesson | confidence=0.94 | incident-208]
Incident #208: Deployment v2.8 introduced a connection leak in the payment service. The validated remediation was to roll back the deployment and fix the leak, not to blindly increase the pool size.

[runbook | confidence=0.95 | runbook-12]
Runbook #12: If checkout latency exceeds 2 seconds, inspect payment database connection pressure, active sessions, and recent deployment changes.
```

### Step 8: LLM Reasoning (Amazon Nova Lite)
Amazon Bedrock's `amazon.nova-lite-v1:0` receives the reassembled context along with explicit system instructions:
- **Contradiction Awareness:** The model is explicitly instructed to detect conflicting advice between older diagnostic theories and newly validated operational lessons.
- **Explainability:** The LLM cites specific memory sources (`incident-208`, `runbook-12`) in its generated diagnostic and remediation plan.

### Step 9: Commit Checkpoint (ACID Durability)
Before returning or executing side-effects, the agent writes its latest step completion to CockroachDB inside an atomic transaction:

```sql
BEGIN;
UPDATE workflow_steps 
SET status = 'COMPLETED', result = $2, updated_at = now() 
WHERE workflow_id = $1 AND step_number = $3;

UPDATE workflows 
SET last_completed_step = $3, updated_at = now() 
WHERE workflow_id = $1;

INSERT INTO audit_log (workflow_id, action, details) 
VALUES ($1, 'STEP_CHECKPOINT', $4);
COMMIT;
```

If the compute container crashes immediately after this transaction, the next worker picks up at step `$3 + 1`.

### Step 10: Write New Validated Knowledge
When the agent verifies a novel finding or fixes a bug, it registers a permanent knowledge item:

```sql
INSERT INTO memories (memory_type, content, embedding, confidence, source, status) 
VALUES ('validated_lesson', $1, $2::VECTOR, 0.94, 'incident-208', 'active');
```

### Step 11: Supersede Stale Knowledge
To prevent future agent runs from repeating invalidated assumptions, the agent atomically marks the obsolete record as superseded:

```sql
UPDATE memories 
SET status = 'superseded', valid_until = now() 
WHERE source = 'incident-143' AND status = 'active';
```

This guarantees that future vector queries automatically prioritize the validated finding while preserving full forensic lineage in the database.

---

## 3. Detailed Comparison: Traditional RAG vs. REASSEMBLE

| Architectural Dimension | Traditional Naive RAG | REASSEMBLE Memory Architecture |
| :--- | :--- | :--- |
| **State Persistence** | **Ephemeral / Stateless:** Agent state exists in Python heap or short-lived memory. A crashed worker loses all progress. | **Distributed ACID Checkpointing:** Execution state and step progression are persisted in CockroachDB before every step. |
| **Handling of Stale / Conflicting Knowledge** | **Static Accumulation:** Stale documents remain in the vector index. LLMs hallucinate or get confused by contradictory chunks. | **Dynamic Memory Supersession:** Stale memories are marked `superseded` and atomically replaced by validated lessons (`incident-208` supersedes `incident-143`). |
| **Data Model** | **Vector-Only Silo:** Embeddings live in an isolated vector DB detached from operational workflows. | **Unified Relational-Vector Store:** Vectors (`VECTOR(1024)`), relational workflows, and audit logs live in CockroachDB. |
| **Confidence Scoring** | **Flat Distance Metric:** Distance score alone dictates relevance without regard for empirical validation. | **Bayesian Confidence Weighting:** Blends vector cosine similarity with empirical validation ratings ($0.0 \le c \le 1.0$). |
| **Crash Recovery & Resumption** | **Zero Recovery:** Worker crash requires entire task to be re-run from step 1, burning tokens and compute. | **Instant State Reconstruction:** A newly spawned worker queries `last_completed_step` and resumes exactly where the previous worker failed. |
| **Auditability & Provenance** | **Opaque Retrieval:** In-flight reasoning and state transitions leave no persistent audit trail. | **Tamper-Evident Audit Log:** Every status transition, worker crash event, and memory mutation is recorded in `audit_log`. |
| **Developer / Agent Tooling** | **Custom API endpoints required** to inspect database state or debug retrieval. | **CockroachDB Managed MCP:** Standardized Model Context Protocol enables AI IDEs (Cursor/Claude) to inspect live schemas and query state directly. |

---

## 4. Algorithmic Proof: The Checkout Latency Incident

```
[ T0: Initial Ingestion ]
Memories in CockroachDB:
- Memory A (incident-143, conf=0.72, status=active): "Engineers suspect connection pool exhaustion; recommend increasing pool."
- Memory B (runbook-12,     conf=0.95, status=active): "Inspect payment DB connection pressure."

[ T1: Incident Triggered ]
Agent initiates incident response. Step 1 (Context Loaded) committed to CockroachDB.

[ T2: Memory Retrieval & Crash ]
Step 2 executed. Worker 1 records Step 2 completion, then CRASHES (Worker killed).
Workflows table status = 'INTERRUPTED', last_completed_step = 2.

[ T3: Worker 2 Spawns & Resumes ]
Worker 2 boots with ZERO memory of Worker 1.
Worker 2 queries CockroachDB: Sees workflow_id is at step 2.
Resumes directly at Step 3 (Validate hypothesis) and Step 4 (Commit resolution).

[ T4: Empirical Discovery & Supersession ]
Worker 2 determines deployment v2.8 has a connection leak.
Increasing pool size will NOT fix a leak (Incident #191).
Worker 2 executes Step 10 & 11:
  - Writes Memory C (incident-208, conf=0.94, status=active): "Deployment v2.8 connection leak. Roll back deployment."
  - Updates Memory A (incident-143): status = 'superseded', valid_until = now().

[ T5: Subsequent Agent Query ]
User asks: "Why is checkout latency high?"
REASSEMBLE algorithm queries CockroachDB vector index WHERE status = 'active'.
Memory C is retrieved; Memory A is excluded.
Nova Lite outputs correct root-cause remediation with 100% precision.
```
