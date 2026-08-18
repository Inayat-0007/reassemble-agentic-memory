# REASSEMBLE — System Design Document

**Project:** REASSEMBLE — Durable Agent Memory  
**Motto:** *Remember. Recover. Learn.*  
**Author:** REASSEMBLE Architecture Team  
**Status:** Production / MVP Architecture  
**Target Platform:** AWS Lambda + Amazon Bedrock + CockroachDB Cloud  

---

## 1. Executive Summary & Architectural Vision

Modern autonomous AI agents suffer from a fundamental architectural flaw: **memory fragility and compute state coupling**. Traditional agent frameworks keep task execution states, conversation histories, and working hypotheses in ephemeral runtime memory (e.g., Python heap, local session storage, or short-lived server memory). When an agent worker fails, encounters a network blip, or scales down, all in-flight operational context is permanently lost. Furthermore, standard Retrieval-Augmented Generation (RAG) models retrieve static documentation chunks but lack the ability to update, supersede, or invalidate past mistaken beliefs.

**REASSEMBLE** introduces an enterprise-grade, crash-resilient memory and workflow execution framework. By combining **CockroachDB** (for distributed ACID checkpoints, transactional execution state, and native vector search) with **Amazon Bedrock** (Amazon Nova Lite for reasoning and Amazon Titan Text Embeddings V2 for high-dimension semantic representation) on **AWS Lambda**, REASSEMBLE decouples agent intelligence from worker lifecycle. 

Key innovations include:
1. **Durable Agent Checkpointing:** Workflow step progressions and operational states are committed transactionally to CockroachDB. If a worker crashes mid-step, a newly spawned worker immediately reconstructs the workflow from the database and continues execution without lost progress.
2. **Hybrid Memory & Vector Indexing:** Semantic knowledge embeddings (`VECTOR(1024)`) and relational workflow state reside in the same CockroachDB database, enabling unified queries that combine semantic similarity with relational filtering and transactional consistency.
3. **Dynamic Memory Supersession:** When an agent discovers a root-cause remediation that contradicts earlier diagnostic hypotheses, it invalidates the stale memory record (`status = 'superseded'`) and writes a validated lesson with complete provenance.
4. **Managed Model Context Protocol (MCP) Integration:** Direct agentic access to CockroachDB via CockroachDB Managed MCP allows external developer agents (e.g., Cursor, Claude Desktop) to inspect schemas, query workflow tables, and verify recovery state.

---

## 2. Architecture Overview

### 2.1 High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                 CLIENT TIER                                       |
|                                                                                   |
|    +-------------------------------------------------------------------------+    |
|    |                      Browser SPA / Developer IDE                        |    |
|    |    - Incident Dashboard (Start / Crash / Resume)                        |    |
|    |    - Agent Chat Interface (Query Semantic Memory)                       |    |
|    |    - Real-time Memory Trace & Workflow State Viewer                     |    |
|    +-------------------------------------------------------------------------+    |
+------------------------------------------+----------------------------------------+
                                           | HTTPS / Function URL
                                           v
+-----------------------------------------------------------------------------------+
|                            SERVERLESS COMPUTE TIER                                |
|                                                                                   |
|    +-------------------------------------------------------------------------+    |
|    |                        AWS Lambda (Python 3.11+)                        |    |
|    |                                                                         |    |
|    |   [ HTTP Router / Controller ]                                          |    |
|    |   ├── GET  /                 -> Serves Embedded SPA HTML                |    |
|    |   ├── POST /api/memories     -> Seed & Retrieve Active Memories         |    |
|    |   ├── POST /api/chat         -> Semantic Memory Reassembly + LLM        |    |
|    |   ├── POST /api/demo/start   -> Initialize Incident & Step 1 Checkpoint |    |
|    |   ├── POST /api/demo/crash   -> Commit Step 2 & Simulate Worker Crash   |    |
|    |   └── POST /api/demo/resume  -> Reconstruct State, Step 3/4 & Supersede |    |
|    |                                                                         |    |
|    |   [ REASSEMBLE Agent Engine ]                                           |    |
|    |   ├── Intent Extraction & Memory Vectorizer                             |    |
|    |   ├── Context Reassembly & Confidence Evaluator                         |    |
|    |   └── Transactional Checkpoint Manager & Audit Recorder                 |    |
|    +-------------------+-----------------------------------+-----------------+    |
+------------------------|-----------------------------------|----------------------+
                         |                                   |
         boto3 Bedrock   |                   pg8000 TLS      |
         API Calls       |                   SQL Wire Proto  |
                         v                                   v
+------------------------------------+   +------------------------------------------+
|          AI & INFERENCE            |   |             PERSISTENCE TIER             |
|                                    |   |                                          |
|  +------------------------------+  |   |  +------------------------------------+  |
|  |        Amazon Bedrock        |  |   |  |     CockroachDB Cloud Cluster      |  |
|  |                              |  |   |  |        (Serverless / Multi-Node)   |  |
|  |  [ Titan Text Embed V2 ]     |  |   |  |                                    |  |
|  |  - Model: amazon.titan-      |  |   |  |  [ Distributed SQL & Relational ]  |  |
|  |    embed-text-v2:0           |  |   |  |  - workflows (Workflow State)      |  |
|  |  - Output: 1024-dim Vector   |  |   |  |  - workflow_steps (Checkpoints)    |  |
|  |                              |  |   |  |  - audit_log (Immutable Audit)     |  |
|  |  [ Nova Lite v1 ]            |  |   |  |                                    |  |
|  |  - Model: amazon.nova-       |  |   |  |  [ Distributed Vector Search ]     |  |
|  |    lite-v1:0                 |  |   |  |  - memories (VECTOR(1024))         |  |
|  |  - Prompt Context Reassembly |  |   |  |  - memories_embedding_idx (HNSW)   |  |
|  |  - Fast, Low-Latency Reason  |  |   |  |  - Cosine Distance Operator (<=>)  |  |
|  +------------------------------+  |   |  +------------------------------------+  |
+------------------------------------+   +---------------------+--------------------+
                                                               ^
                                                               | MCP Protocol (HTTPS)
                                                 +-------------+-------------+
                                                 | CockroachDB Managed MCP   |
                                                 | - Schema Inspection       |
                                                 | - SELECT Verification     |
                                                 | - Cursor / Claude Agent   |
                                                 +---------------------------+
```

---

## 3. Component Responsibilities

### 3.1 AWS Lambda Runtime (Stateless Orchestrator)
- **Execution Lifecycle:** Operates as an on-demand, stateless compute unit. Receives HTTPS invocations via AWS Lambda Function URL.
- **Request Routing:** Dispatches incoming HTTP requests to dedicated controllers (`/`, `/api/memories`, `/api/chat`, `/api/demo/*`).
- **Database Driver:** Utilizes `pg8000` (pure Python PostgreSQL DB-API client) to establish secure, direct TLS connections to CockroachDB Cloud.
- **State Management Principle:** **Zero local execution state.** Any state required across invocations must be written to CockroachDB before returning an HTTP response.

### 3.2 Amazon Bedrock (Inference & Embedding Engine)
- **Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`):**
  - Converts queries and incident observations into normalized 1024-dimensional dense vectors.
  - Configuration: `{"dimensions": 1024, "normalize": True}`.
- **Amazon Nova Lite v1 (`amazon.nova-lite-v1:0`):**
  - Ultra-fast, cost-effective multimodal LLM tailored for high-frequency reasoning and agentic workflows.
  - Receives dynamically reassembled context (containing active memories, source citations, and confidence metrics).
  - Explicitly trained via system instructions to identify contradictory hypotheses and favor newly validated evidence over superseded assumptions.

### 3.3 CockroachDB Cloud (Distributed Database & Vector Store)
- **ACID Transaction Engine:** Provides serializable ACID transactions across multi-step workflow modifications, ensuring checkpoint integrity even during sudden worker crashes.
- **Distributed Vector Indexing:** Houses dense embeddings in native `VECTOR(1024)` columns and accelerates approximate nearest neighbor search using vector indices and cosine distance operator (`<=>`).
- **Unified Storage Architecture:** Combines structured workflow progress (`workflows`, `workflow_steps`), append-only security traces (`audit_log`), and unstructured knowledge items (`memories`) in a single distributed database cluster.

### 3.4 CockroachDB Managed MCP Server (Developer & Operations Tooling)
- **Protocol:** Standardized Model Context Protocol (MCP) running over secure HTTPS with service-account API-key authentication.
- **Agent Integration:** Allows AI IDEs (Cursor, VS Code) and autonomous ops agents to discover schema definitions, execute read-only queries, and verify workflow checkpoints directly without requiring custom administrative endpoints.

### 3.5 Single Page Application (SPA Frontend)
- **Packaging:** Embedded directly within the Lambda function as a zero-dependency HTML5/CSS3/JavaScript single-file application.
- **Capabilities:** Interactive 3-step incident demonstration (Start -> Crash -> Resume), live agent chat window with dynamic memory trace visualization, and workflow state inspector.

---

## 4. End-to-End Data Flows

### 4.1 Chat Query & Context Reassembly Flow

```
[ User Browser ]      [ Lambda Handler ]         [ Bedrock Titan V2 ]      [ CockroachDB ]          [ Bedrock Nova Lite ]
       |                      |                           |                      |                        |
       |--- POST /api/chat -->|                           |                      |                        |
       |    { "message" }     |                           |                      |                        |
       |                      |--- InvokeModel(embed) --->|                      |                        |
       |                      |<-- 1024-dim Vector -------|                      |                        |
       |                      |                                                  |                        |
       |                      |--- SELECT * FROM memories WHERE status='active' -|                        |
       |                      |    ORDER BY embedding <=> vector LIMIT 5 ------->|                        |
       |                      |<-- Top 5 Relevant Active Memories --------------|                        |
       |                      |                                                  |                        |
       |                      |--- Format Reassembled Memory Context ----------------------------------->|
       |                      |    (System prompt + Confidence + Sources)                                |
       |                      |<-- Reasoning Output & Actionable Next Step ------------------------------|
       |                      |
       |<-- HTTP 200 OK ------|
       |    { answer,         |
       |      memories }      |
```

1. **User Request:** The client submits a natural language question (e.g., *"Why is checkout latency high?"*).
2. **Vector Generation:** Lambda calls Amazon Bedrock (`Titan Text Embeddings V2`) to generate a 1024-dimensional normalized vector representing the semantic intent.
3. **CockroachDB Vector Search:** Lambda executes a cosine similarity query (`ORDER BY embedding <=> %s::VECTOR LIMIT 5`) filtered on `status = 'active'`.
4. **Context Reassembly:** The retrieved memories, complete with confidence scores, source tags, and memory types, are synthesized into a structured memory block.
5. **LLM Inference:** Amazon Bedrock (`Nova Lite`) processes the system prompt and reassembled memory to formulate a grounded diagnosis.
6. **Client Response:** The answer and memory trace are returned to the client for rendering.

---

### 4.2 Incident Lifecycle & Checkpointing Flow

```
[ User Browser ]      [ Lambda Handler ]         [ CockroachDB: workflows ]   [ CockroachDB: workflow_steps ]   [ CockroachDB: audit_log ]
       |                      |                               |                              |                             |
       |-- POST /demo/start ->|                               |                              |                             |
       |                      |-- BEGIN TRANSACTION --------->|                              |                             |
       |                      |-- INSERT INTO workflows ----->| (status='INVESTIGATING')     |                             |
       |                      |-- INSERT INTO workflow_steps ------------------------------->| (Steps 1..4 = 'PENDING')    |
       |                      |-- UPDATE workflow_steps ------------------------------------>| (Step 1 = 'COMPLETED')      |
       |                      |-- UPDATE workflows (last=1) ->|                              |                             |
       |                      |-- INSERT INTO audit_log ------------------------------------------------------------------>| (WORKFLOW_CREATED)
       |                      |-- COMMIT TRANSACTION -------->|                              |                             |
       |                      |                               |                              |                             |
       |<-- HTTP 200 OK ------|                               |                              |                             |
       |    { workflow_id,    |                               |                              |                             |
       |      state }         |                               |                              |                             |
```

1. **Initialization:** The user triggers an incident response workflow.
2. **Transaction Execution:** Within a single serializable transaction:
   - A unique `workflow_id` (UUID v4) is generated.
   - The master `workflows` record is inserted with status `INVESTIGATING`.
   - Four discrete step rows are created in `workflow_steps` (1: Load context, 2: Retrieve memory, 3: Validate hypothesis, 4: Commit resolution).
   - Step 1 is marked `COMPLETED` and `last_completed_step` is set to `1`.
   - An immutable event is written to `audit_log`.
3. **Durability Guarantee:** State is immediately persisted in CockroachDB before the client receives acknowledgment.

---

### 4.3 Crash Simulation & Durable Recovery Flow

```
[ Worker 1 (Crashing) ]         [ CockroachDB Cluster ]          [ Worker 2 (Recovery) ]
         |                                 |                                |
         |-- POST /demo/crash ------------>|                                |
         |   UPDATE step 2 = 'COMPLETED'   |                                |
         |   UPDATE workflows              |                                |
         |     SET status = 'INTERRUPTED'  |                                |
         |     last_completed_step = 2     |                                |
         |   INSERT audit SIMULATED_CRASH  |                                |
         |   COMMIT TRANSACTION            |                                |
         |                                 |                                |
       XXXXX [ Worker 1 Terminated ]       |                                |
                                           |                                |
                                           |<-- POST /demo/resume ----------|
                                           |    (workflow_id)               |
                                           |                                |
                                           |--- SELECT * FROM workflows ----|
                                           |    WHERE workflow_id = $1      |
                                           |                                |
                                           |<-- State: INTERRUPTED, Step 2 -|
                                           |                                |
                                           |<-- Execute Step 3 & 4 ---------|
                                           |    UPDATE step 3 = 'COMPLETED' |
                                           |    UPDATE step 4 = 'COMPLETED' |
                                           |    UPDATE workflows            |
                                           |      SET status = 'COMPLETED'  |
                                           |      last_completed_step = 4   |
                                           |    INSERT validated memory     |
                                           |    UPDATE stale memory         |
                                           |      SET status = 'superseded' |
                                           |    INSERT audit WORKFLOW_DONE  |
                                           |    COMMIT TRANSACTION          |
```

1. **Checkpointing prior to Crash:** Worker 1 executes Step 2, updates `workflow_steps` to `COMPLETED`, transitions `workflows.status` to `INTERRUPTED`, records the audit event, and terminates.
2. **Independent Worker Spawning:** A completely separate Lambda instance (Worker 2) is invoked with `POST /api/demo/resume`. Worker 2 shares **zero in-memory variables** with Worker 1.
3. **State Reconstruction:** Worker 2 queries CockroachDB using `workflow_id` to inspect `last_completed_step` and step history.
4. **Resumed Execution:** Recognizing that Steps 1 and 2 are already complete, Worker 2 executes Steps 3 and 4 without repeating prior work.
5. **Memory Supersession & Learning:** Worker 2 discovers that deployment v2.8 caused a connection leak (not pool exhaustion). It inserts a new validated memory (`incident-208`) with 0.94 confidence and marks the conflicting memory (`incident-143`) as `status = 'superseded'` and `valid_until = now()`.

---

## 5. Scalability Considerations

| Architectural Layer | Scalability Vector | Design & Mitigation Strategy |
| :--- | :--- | :--- |
| **Compute Tier (Lambda)** | Horizontal scaling to 10,000+ concurrent executions | **Stateless execution model:** Lambda functions contain zero session state or local locks. Handlers initialize lightweight clients (`pg8000`, `boto3`) outside the warm invocation loop. Cold starts are minimized by avoiding heavy ORMs. |
| **Database Tier (CockroachDB)** | Multi-region distributed SQL with automatic sharding | CockroachDB splits tables into 64MB range partitions replicated via the Raft consensus algorithm. Vector similarity searches are distributed across nodes, avoiding centralized bottlenecking. |
| **Vector Index Performance** | High-volume nearest neighbor search | Built-in HNSW / vector indexing with Cosine Distance (`<=>`) scales sub-linearly with memory catalog size. Active memory filtering (`WHERE status = 'active'`) drastically reduces vector candidate scan spaces. |
| **Connection Management** | Lambda-to-CockroachDB connection pooling | Uses lightweight, per-invocation connection handshakes with a 15-second socket timeout. In large-scale enterprise deployments, an AWS RDS Proxy or CockroachDB Serverless connection pooler buffers concurrent connections. |
| **Inference Tier (Bedrock)** | Bedrock token throughput and concurrency | Nova Lite is utilized for sub-second agent reasoning. Prompts are compactly structured with token budgets capped at `maxTokens: 600` and low temperature (`0.2`) for deterministic, highly reproducible evaluations. |

---

## 6. Security Model & Production Readiness

### 6.1 Hackathon MVP Scope
- **Network Transport:** End-to-end TLS 1.3 encryption for all external API calls and database sessions (`ssl_context=create_default_context()`, `verify-full`).
- **AWS IAM Least Privilege:** The Lambda execution role requires only targeted permissions:
  - `bedrock:InvokeModel` (Titan Text Embeddings V2)
  - `bedrock:Converse` (Nova Lite)
  - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` (CloudWatch Logging)
- **Credential Storage:** Database connection strings and model IDs are injected strictly via Lambda environment variables (`CRDB_URL`, `CHAT_MODEL_ID`, `EMBED_MODEL_ID`), never hardcoded in repository code or client-side assets.
- **CORS Configuration:** Controlled HTTP response headers allowing standard cross-origin resource sharing for web client integration.

### 6.2 Production Hardening Roadmap

```
+-----------------------------------------------------------------------------------+
|                        ENTERPRISE PRODUCTION TOPOLOGY                             |
|                                                                                   |
|  [ Client / CloudFront ]                                                          |
|         |                                                                         |
|         v                                                                         |
|  [ AWS WAF + Amazon API Gateway ] (OAuth 2.0 / Amazon Cognito Authorizer)         |
|         |                                                                         |
|         v VPC Private Link                                                        |
|  [ AWS Lambda in Private VPC ]                                                    |
|         ├── Secrets Manager / AWS Systems Manager Parameter Store                 |
|         ├── AWS IAM Database Authentication to CockroachDB Dedicated / VPC Peering|
|         └── Bedrock VPC Gateway Endpoint                                          |
+-----------------------------------------------------------------------------------+
```

1. **Authentication & Authorization:** Transition from public Function URL to Amazon API Gateway backed by Amazon Cognito User Pools or enterprise OAuth2/OIDC providers.
2. **Secret Management:** Move database connection strings from environment variables to **AWS Secrets Manager** with automatic 30-day credential rotation.
3. **Private Networking:** Deploy Lambda functions inside dedicated Amazon VPC subnets with AWS PrivateLink connections to CockroachDB Dedicated and Bedrock VPC Endpoints, eliminating public internet traversal.
4. **Audit Immutability:** Enable CockroachDB changefeeds (`CDC`) streaming `audit_log` events directly to Amazon S3 / AWS Security Lake for immutable compliance retention.
