# 3-Minute Technical Judging Demo Script

### 1. The Hook (0:00–0:20)
- "REASSEMBLE is a durable agentic-memory engine demonstrated through an SRE incident workflow."
- "AI workers and compute are disposable, but the agent's memory and workflow state remain durably anchored in CockroachDB."

### 2. Durable State Checkpointing (0:20–0:50)
1. Open the live dashboard: `https://wdixxgldo6nkydfcncocpvdqu40ukjkt.lambda-url.us-east-1.on.aws/`
2. Click **1. Start Incident**.
3. Point out state: `INVESTIGATING`, Step `1/4`.
4. Switch to CockroachDB SQL Console and run:
   ```sql
   SELECT workflow_id, status, last_completed_step, total_steps FROM workflows ORDER BY created_at DESC LIMIT 3;
   ```
5. "This checkpoint is persisted as an ACID database record in CockroachDB, not held in volatile Lambda memory."

### 3. Controlled Failure Injection & Recovery (0:50–1:50)
1. Click **2. Controlled Failure Injection**.
2. Point out state: `INTERRUPTED`, Step `2/4`.
3. "I'm deliberately injecting a worker failure after checkpoint 2. The failure is controlled, but the state transition and persistence are real."
4. Click **3. Resume from Checkpoint**.
5. Point out state: `COMPLETED`, Step `4/4`.
6. "A brand new worker execution reconstructs the state directly from CockroachDB, skips completed steps, and finishes the investigation without starting over."

### 4. Semantic Memory Evolution & Vector Search (1:50–2:25)
1. In the chat box, ask: `Why is checkout latency high?`
2. Point at the Seeded Demonstration Memories trace.
3. "The recovered workflow created validated demonstration evidence (`incident-208`) that supersedes the older advice (`incident-143`)."
4. "The agent performs cosine similarity search on CockroachDB's `VECTOR(1024)` index, recognizes the contradiction, and explicitly advises against increasing the connection pool."

### 5. Architecture & MCP Introspection (2:25–3:00)
1. Show `schema.sql`: highlight `embedding VECTOR(1024)` and `CREATE VECTOR INDEX`.
2. Show `.cursor/mcp.json`: "We use the CockroachDB Managed MCP server for live AI schema introspection, while AWS Lambda uses direct SQL for execution."
3. "The failure is controlled, the dataset is synthetic, but the persistence, vector retrieval, state transitions, and recovery are real."

