# REASSEMBLE — Database Design Document

**Project:** REASSEMBLE — Durable Agent Memory  
**Component:** Database Architecture & Data Modeling  
**Target Engine:** CockroachDB Cloud (v23.2+ / v24.1+)  
**Vector Extension:** Distributed Vector Indexing (`VECTOR(1024)`)  

---

## 1. Schema Overview

REASSEMBLE utilizes a unified, relational-vector hybrid database schema hosted on **CockroachDB Cloud**. The schema bridges non-deterministic LLM reasoning with distributed ACID durability by managing four distinct data models:

1. **`memories`**: Distributed vector store containing semantic agent knowledge, empirical observations, architectural decisions, and runbooks with vector embeddings and confidence metrics.
2. **`workflows`**: Top-level workflow execution records tracking active agent tasks, high-level status, and incident context.
3. **`workflow_steps`**: Granular, step-by-step checkpoint states allowing crash recovery at discrete sub-task boundaries.
4. **`audit_log`**: Append-only tamper-evident event log recording agent transitions, crash events, and memory supersessions.

```
+----------------------------------------------------------------------------------------------------+
|                                    COCKROACHDB SCHEMA ENTITY DIAGRAM                               |
+----------------------------------------------------------------------------------------------------+

       +------------------------------------+             +------------------------------------+
       |              memories              |             |             workflows              |
       +------------------------------------+             +------------------------------------+
       | PK  id           UUID              |             | PK  workflow_id         UUID       |
       |     memory_type  STRING            |             |     status              STRING     |
       |     content      STRING            |             |     incident            STRING     |
       |     embedding    VECTOR(1024)      |             |     last_completed_step INT        |
       |     confidence   FLOAT8            |             |     total_steps         INT        |
       |     source       STRING            |             |     updated_at          TIMESTAMPTZ|
       |     status       STRING            |             +-----------------+------------------+
       |     created_at   TIMESTAMPTZ       |                               | 1
       |     valid_until  TIMESTAMPTZ       |                               |
       | FK  supersedes   UUID (self-ref)   |                               |
       +------------------+-----------------+                               |
                          | (Lineage / Supersession)                        | 1..N
                          +-------+                                         |
                                  |                                         v
                                  v                               +------------------------------------+
       +------------------------------------+                     |           workflow_steps           |
       |             audit_log              |                     +------------------------------------+
       +------------------------------------+                     | PK,FK workflow_id   UUID           |
       | PK  id           UUID              |                     | PK    step_number   INT            |
       | FK  workflow_id  UUID              |<--------------------+       name          STRING         |
       |     action       STRING            |                     |       status        STRING         |
       |     details      STRING            |                     |       result        STRING         |
       |     created_at   TIMESTAMPTZ       |                     |       updated_at    TIMESTAMPTZ    |
       +------------------------------------+                     +------------------------------------+
```

---

## 2. Table Details & Column Specifications

### 2.1 Table: `memories`
Stores semantic memories with high-dimensional embeddings, validity intervals, and lineage pointers.

```sql
CREATE TABLE IF NOT EXISTS memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  memory_type STRING NOT NULL,
  content STRING NOT NULL,
  embedding VECTOR(1024) NOT NULL,
  confidence FLOAT8 NOT NULL DEFAULT 0.5,
  source STRING,
  status STRING NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  valid_until TIMESTAMPTZ NULL,
  supersedes UUID NULL
);
```

| Column Name | Data Type | Nullable | Default | Description & Operational Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key; unique global identifier for the memory chunk. |
| `memory_type` | `STRING` | No | None | Category of memory (`incident`, `runbook`, `architecture`, `lesson`, `validated_lesson`, `current_fact`). |
| `content` | `STRING` | No | None | Human-readable textual knowledge, incident report, or operational rule. |
| `embedding` | `VECTOR(1024)` | No | None | 1024-dimensional normalized dense embedding generated by Amazon Titan Text Embeddings V2. |
| `confidence` | `FLOAT8` | No | `0.5` | Bayesian confidence weight ($0.0 \le c \le 1.0$) indicating empirical reliability of this knowledge. |
| `source` | `STRING` | Yes | `NULL` | Upstream origin identifier or ticket ID (e.g., `incident-143`, `runbook-12`, `incident-208`). |
| `status` | `STRING` | No | `'active'` | Lifecycle state: `'active'`, `'superseded'`, `'invalidated'`, `'draft'`. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | UTC timestamp when the memory was initially ingested or validated. |
| `valid_until` | `TIMESTAMPTZ` | Yes | `NULL` | Timestamp indicating expiration or point in time when superseded. Active if `NULL` or future. |
| `supersedes` | `UUID` | Yes | `NULL` | Optional self-referencing foreign key pointing to an older `memories.id` that this record replaces. |

---

### 2.2 Table: `workflows`
Tracks long-running agent tasks and operational incidents.

```sql
CREATE TABLE IF NOT EXISTS workflows (
  workflow_id UUID PRIMARY KEY,
  status STRING NOT NULL,
  incident STRING NOT NULL,
  last_completed_step INT NOT NULL DEFAULT 0,
  total_steps INT NOT NULL DEFAULT 4,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

| Column Name | Data Type | Nullable | Default | Description & Operational Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `workflow_id` | `UUID` | No | None | Primary key; unique identifier for the execution workflow instance. |
| `status` | `STRING` | No | None | High-level execution status (`'INVESTIGATING'`, `'INTERRUPTED'`, `'COMPLETED'`, `'FAILED'`). |
| `incident` | `STRING` | No | None | Summary description of the operational event or task prompt triggering the workflow. |
| `last_completed_step`| `INT` | No | `0` | Watermark index of the last durably committed step. Used immediately upon worker recovery. |
| `total_steps` | `INT` | No | `4` | Total planned progression steps for completion tracking. |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Timestamp of the most recent status transition or checkpoint commit. |

---

### 2.3 Table: `workflow_steps`
Stores fine-grained step executions and execution results for a parent workflow.

```sql
CREATE TABLE IF NOT EXISTS workflow_steps (
  workflow_id UUID NOT NULL,
  step_number INT NOT NULL,
  name STRING NOT NULL,
  status STRING NOT NULL,
  result STRING,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (workflow_id, step_number)
);
```

| Column Name | Data Type | Nullable | Default | Description & Operational Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `workflow_id` | `UUID` | No | None | Composite primary key component referencing `workflows.workflow_id`. |
| `step_number` | `INT` | No | None | Composite primary key component; 1-indexed sequential step identifier (e.g., 1, 2, 3, 4). |
| `name` | `STRING` | No | None | Descriptive step title (e.g., *"Load incident context"*, *"Validate current hypothesis"*). |
| `status` | `STRING` | No | None | Discrete step state: `'PENDING'`, `'IN_PROGRESS'`, `'COMPLETED'`, `'FAILED'`. |
| `result` | `STRING` | Yes | `NULL` | Structured result, observation payload, or reasoning checkpoint emitted by the agent. |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | UTC timestamp when step status was updated. |

---

### 2.4 Table: `audit_log`
Immutable, append-only operational log providing forensic observability into agent actions and worker failures.

```sql
CREATE TABLE IF NOT EXISTS audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID,
  action STRING NOT NULL,
  details STRING,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

| Column Name | Data Type | Nullable | Default | Description & Operational Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key for the audit entry. |
| `workflow_id` | `UUID` | Yes | `NULL` | Optional reference to the associated workflow instance. |
| `action` | `STRING` | No | None | Standardized action verb (`WORKFLOW_CREATED`, `SIMULATED_CRASH`, `WORKFLOW_COMPLETED`). |
| `details` | `STRING` | Yes | `NULL` | Detailed context, recovery diagnostic notes, or checkpoint reason. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Exact UTC commit time generated by CockroachDB. |

---

## 3. Vector Indexing Strategy

### 3.1 1024-Dimensional Semantic Space
REASSEMBLE standardizes on a vector dimensionality of **1024** to match Amazon Bedrock's `amazon.titan-embed-text-v2:0` embedding model. 

- **Normalization:** Vectors are unit-normalized ($L_2\text{-norm} = 1.0$) upon ingestion via Bedrock's `"normalize": True` parameter.
- **Distance Metric:** Cosine Distance is computed using CockroachDB's native vector distance operator:
  $$\text{Cosine Distance}(u, v) = 1 - \frac{u \cdot v}{\|u\|_2 \|v\|_2} \implies u \Leftrightarrow v$$
  For unit-normalized vectors, this evaluates directly to $1 - (u \cdot v)$.

### 3.2 Index Definition & Acceleration

```sql
CREATE VECTOR INDEX IF NOT EXISTS memories_embedding_idx ON memories (embedding);
```

- **Algorithm:** CockroachDB builds distributed vector indexes (Hierarchical Navigable Small World / Vector Inverted File partition trees) directly across distributed ranges.
- **Hybrid Relational-Vector Pushdown:** Queries combine vector ordering with standard SQL predicates:
  ```sql
  SELECT id, memory_type, content, confidence, source, status
  FROM memories
  WHERE status = 'active'
  ORDER BY embedding <=> %s::VECTOR
  LIMIT 5;
  ```
  CockroachDB's cost-based optimizer evaluates the relational filter (`status = 'active'`) in conjunction with the vector index to prune search space before performing distance calculations.

---

## 4. Memory Lifecycle & Dynamic Supersession

Autonomous systems must cope with **non-stationary facts**. As systems evolve, earlier assumptions (e.g., *"increase connection pool on timeout"*) become counter-productive or dangerous.

```
       +----------------------------------------------------------------------+
       |                          1. INGESTION                                |
       | Initial hypothesis ingested with moderate confidence (0.72)          |
       | Source: incident-143 | Status: 'active' | valid_until: NULL          |
       +----------------------------------+-----------------------------------+
                                          |
                                          | Deployment v2.8 occurs;
                                          | Agent verifies connection leak.
                                          v
       +----------------------------------------------------------------------+
       |                   2. ATOMIC TRANSACTIONAL LEARNING                   |
       |                                                                      |
       |  a. INSERT validated memory (incident-208):                          |
       |     - memory_type: 'validated_lesson'                                |
       |     - confidence:  0.94                                              |
       |     - status:      'active'                                          |
       |     - supersedes:  <UUID of incident-143>                            |
       |                                                                      |
       |  b. UPDATE stale memory (incident-143):                              |
       |     - status:      'superseded'                                      |
       |     - valid_until: now()                                             |
       +----------------------------------+-----------------------------------+
                                          |
                                          v
       +----------------------------------------------------------------------+
       |                        3. REASSEMBLE QUERY                           |
       | Vector search filters out WHERE status = 'active'.                   |
       | Incident-208 is presented to LLM; Incident-143 is excluded or        |
       | presented only as a refuted historical antipattern.                 |
       +----------------------------------------------------------------------+
```

### Transition Matrix
- **`active` $\to$ `superseded`**: Triggered when a workflow concludes with verified root-cause evidence invalidating a prior record.
- **`active` $\to$ `invalidated`**: Triggered if a memory source is retracted or proven corrupted.
- **Decay & Expiration**: Queries can optionally filter by `valid_until IS NULL OR valid_until > now()` to enforce temporal shelf-lives for transient facts.

---

## 5. Indexing & Optimization Strategy

| Index Identifier | Target Table | Indexed Columns | Index Type | Optimization Target |
| :--- | :--- | :--- | :--- | :--- |
| `memories_pkey` | `memories` | `(id ASC)` | Primary Key B-Tree | Global identity lookups and self-referencing joins. |
| `memories_embedding_idx` | `memories` | `(embedding)` | Vector Index | Sub-second ANN similarity search. |
| `workflows_pkey` | `workflows` | `(workflow_id ASC)` | Primary Key B-Tree | Single-row state reconstruction upon crash recovery. |
| `workflow_steps_pkey` | `workflow_steps` | `(workflow_id ASC, step_number ASC)` | Composite PK B-Tree | Ordered step retrieval and discrete checkpoint updates. |
| `audit_log_pkey` | `audit_log` | `(id ASC)` | Primary Key B-Tree | Fast write ingestion and unique audit event identity. |

---

## 6. CockroachDB-Specific Features Leveraged

1. **Native `VECTOR` Data Type & Operators:** Direct native support for `VECTOR(1024)` without external third-party vector databases, eliminating dual-write synchronization hazards.
2. **Multi-Raft Distributed Consensus:** Checkpoints committed to `workflows` and `workflow_steps` are synchronously replicated across a quorum of nodes. Worker crashes will never result in partially written or lost step states.
3. **Serializable ACID Isolation:** Guarantees that concurrent agent workers or parallel workflows do not encounter dirty reads, phantom records, or write skew when updating shared memory graphs.
4. **Built-in `gen_random_uuid()`:** Generates cryptographically secure, collision-free UUID v4 identifiers inside the database engine.
5. **CockroachDB Managed Model Context Protocol (MCP):** Connects external AI assistants directly to the cluster over HTTPS, exposing live introspection tools (`list_tables`, `get_table_schema`, `select_query`) without developing bespoke diagnostic APIs.
