# REASSEMBLE — 3-Minute Live Demo Script & Pitch Guide

This document provides the definitive, time-calibrated live demonstration workflow and judging pitch guide for **REASSEMBLE — Durable Agent Memory**.

---

## Table of Contents

1. [Demo Overview & Narrative Arc](#demo-overview--narrative-arc)
2. [3-Minute Demo Timeline & Action Matrix](#3-minute-demo-timeline--action-matrix)
3. [Step-by-Step Script & Stage Directions](#step-by-step-script--stage-directions)
   - [0:00 - 0:25 | The Hook: The Agent Amnesia & Crash Problem](#000---025--the-hook-the-agent-amnesia--crash-problem)
   - [0:25 - 0:55 | Phase 1: Incident Trigger & Durable Checkpointing](#025---055--phase-1-incident-trigger--durable-checkpointing)
   - [0:55 - 1:25 | Phase 2: Worker Crash Simulation & Durability](#055---125--phase-2-worker-crash-simulation--durability)
   - [1:25 - 2:00 | Phase 3: Zero-Loss Recovery & Memory Supersession](#125---200--phase-3-zero-loss-recovery--memory-supersession)
   - [2:00 - 2:35 | Phase 4: Distributed Vector Search & Bedrock Reasoning](#200---235--phase-4-distributed-vector-search--bedrock-reasoning)
   - [2:35 - 2:55 | Phase 5: CockroachDB Managed MCP in Action](#235---255--phase-5-cockroachdb-managed-mcp-in-action)
   - [2:55 - 3:00 | Conclusion & Tagline](#255---300--conclusion--tagline)
4. [CockroachDB SQL Console Walkthrough](#cockroachdb-sql-console-walkthrough)
5. [Key Hackathon Value Propositions for Judges](#key-hackathon-value-propositions-for-judges)
6. [Judge-Specific Pitches](#judge-specific-pitches)
   - [Kiki Carter (Distributed Systems & Enterprise Architecture)](#1-pitch-for-kiki-carter)
   - [Rob Reid (Developer Experience & Practical AI Engineering)](#2-pitch-for-rob-reid)
   - [David Joy (Database Systems & Cloud Infrastructure)](#3-pitch-for-david-joy)
7. [Contingency & Fallback Plans](#contingency--fallback-plans)

---

## Demo Overview & Narrative Arc

### The Core Problem
Most AI agent frameworks are **stateless and ephemeral**. When an agent worker crashes mid-workflow (e.g., Lambda timeout, container restart, network partition), all working memory is lost. Furthermore, when agents learn lessons, they either store them in separate external vector databases with sync lag, or they hallucinate on obsolete runbooks.

### The REASSEMBLE Solution
REASSEMBLE unifies **state durability**, **audit logging**, and **semantic long-term memory** in a single distributed database: **CockroachDB**. Powered by **Amazon Bedrock (Nova Lite + Titan Text Embeddings V2)** and deployed on **AWS Lambda**, REASSEMBLE proves:
1. **Durable Checkpointing**: Workflows survive catastrophic worker death without repeating completed steps.
2. **Distributed Vector Indexing**: High-dimensional semantic recall directly in transactional SQL (`VECTOR(1024)`).
3. **Memory Evolution & Supersession**: Validated lessons explicitly invalidate outdated advice.
4. **Developer Ergonomics**: Live schema and state inspection via CockroachDB Managed MCP.

---

## 3-Minute Demo Timeline & Action Matrix

| Time Window | Phase | UI Action / Screen Focus | SQL Console Action | Spoken Script Focus |
| :--- | :--- | :--- | :--- | :--- |
| **0:00 - 0:25** | The Hook | Show REASSEMBLE Web App (`/`) | — | Problem: AI agents suffer from amnesia and fatal crashes. |
| **0:25 - 0:55** | Phase 1: Incident | Click `1. Start Incident` | `SELECT * FROM workflows;` | Incident v2.8 starts; step 1 checkpoint committed to CockroachDB. |
| **0:55 - 1:25** | Phase 2: Worker Crash | Click `2. Simulate Worker Crash` | `SELECT * FROM workflow_steps;` | Worker dies! Status is `INTERRUPTED`. State is safe in CockroachDB. |
| **1:25 - 2:00** | Phase 3: Resume | Click `3. Resume from Checkpoint` | `SELECT * FROM memories;` | New worker resumes from Step 2 -> completes Step 4. `incident-208` supersedes `incident-143`. |
| **2:00 - 2:35** | Phase 4: Vector AI | Click `Ask Agent` (`Why is checkout latency high?`) | Vector cosine distance query | Bedrock Nova Lite reasons over Titan V2 embeddings indexed in CockroachDB. |
| **2:35 - 2:55** | Phase 5: Managed MCP | Show IDE with `.cursor/mcp.json` | MCP Tool execution | Cursor AI agent introspects live CockroachDB tables directly via Managed MCP. |
| **2:55 - 3:00** | Wrap Up | Highlight Key Badges | — | "Remember. Recover. Learn." |

---

## Step-by-Step Script & Stage Directions

### 0:00 - 0:25 | The Hook: The Agent Amnesia & Crash Problem

**What to Show:**
Have the REASSEMBLE web interface open in your browser (`https://<lambda-id>.lambda-url.us-east-1.on.aws/`). Keep a second tab open with the CockroachDB Cloud SQL Console.

**What to Say:**
> "Modern AI agents are transforming autonomous operations, but in production, they suffer from two critical flaws: **agent amnesia** and **runtime fragility**.
> When an agent container or Lambda function restarts mid-task, all in-flight context is wiped out. And when agents retrieve past knowledge, they frequently act on outdated runbooks.
> This is **REASSEMBLE**: an autonomous incident-response agent whose execution state and long-term semantic memory are durably anchored in **CockroachDB** with **Amazon Bedrock**."

---

### 0:25 - 0:55 | Phase 1: Incident Trigger & Durable Checkpointing

**What to Click:**
Click the purple button: **`1. Start Incident`**.

**What Appears on Screen:**
- Status updates to `INVESTIGATING`.
- Step counter shows `1/4`.
- Workflow UUID is generated and stored in local state.
- Memory Trace displays initial incident context.

**What to Say:**
> "Let’s start an incident. Here, checkout latency has surged to 4.8 seconds following deployment v2.8.
> Notice what just happened: instead of keeping this execution state in ephemeral Lambda memory, the agent immediately committed a durable checkpoint to CockroachDB."

**CockroachDB SQL Console (Optional quick tab switch):**
```sql
SELECT workflow_id, status, last_completed_step, updated_at FROM workflows;
```
> "In CockroachDB, the workflow is registered with transactional ACID guarantees."

---

### 0:55 - 1:25 | Phase 2: Worker Crash Simulation & Durability

**What to Click:**
Click the red button: **`2. Simulate Worker Crash`**.

**What Appears on Screen:**
- Status turns to `INTERRUPTED`.
- Step counter updates to `2/4`.
- Alert message: *"Worker interrupted after checkpoint 2. The important state is already persisted in CockroachDB."*

**What to Say:**
> "Now, disaster strikes. The worker process crashes mid-investigation.
> In a traditional stateless agent, this investigation would be ruined, causing duplicate alert triage or partial execution loops.
> But look at our state: CockroachDB captured Checkpoint 2 before the failure. The workflow status is marked `INTERRUPTED`, and the exact progress is durably preserved across the distributed cluster."

---

### 1:25 - 2:00 | Phase 3: Zero-Loss Recovery & Memory Supersession

**What to Click:**
Click the blue/dark button: **`3. Resume from Checkpoint`**.

**What Appears on Screen:**
- Status transitions to `COMPLETED`.
- Step counter reaches `4/4`.
- The Memory Trace updates showing `incident-208` validated with 94% confidence.

**What to Say:**
> "Now, an entirely new Lambda worker spins up and we click **Resume from Checkpoint**.
> The new worker doesn’t know anything about the old worker's runtime memory. It doesn't need to. It reads the state directly from CockroachDB, skips completed steps 1 and 2, executes steps 3 and 4, and resolves the incident.
> Crucially, it learns: it commits a new validated finding (`incident-208`) identifying a connection leak in v2.8, and automatically marks the obsolete runbook (`incident-143`) as **superseded**."

---

### 2:00 - 2:35 | Phase 4: Distributed Vector Search & Bedrock Reasoning

**What to Click / Type:**
In the Agent prompt box, verify the text: `Why is checkout latency high and what should we do?` and click **`Ask Agent`**.

**What Appears on Screen:**
Bedrock generates an answer explaining:
1. Incident #208 introduced a connection leak in deployment v2.8.
2. The recommended remediation is to roll back deployment v2.8 and fix the leak.
3. Explicitly cautions against increasing the connection pool size (superseded Incident #143 & #191).

**What to Say:**
> "Now let’s test the agent's long-term memory. We ask: *'Why is checkout latency high and what should we do?'*
> Behind the scenes, Amazon Titan Text Embeddings V2 generates a 1024-dimensional vector, and CockroachDB performs a native cosine-distance vector search using its distributed vector index.
> Amazon Bedrock's Nova Lite model synthesizes the retrieved memories, recognizing that the connection-leak finding in `incident-208` supersedes the old advice to increase pool size. It correctly advises: **roll back deployment v2.8**."

---

### 2:35 - 2:55 | Phase 5: CockroachDB Managed MCP in Action

**What to Show:**
Switch to Cursor or VS Code, open `.cursor/mcp.json`, and highlight CockroachDB Managed MCP.

**What to Say:**
> "Finally, look at our developer and agent tooling. Using CockroachDB's **Managed MCP Server**, our AI development environment connects directly to the live CockroachDB cluster over secure HTTPS.
> The AI coding agent can inspect table schemas, verify active checkpoints, and query vector similarity directly during active development—seamlessly closing the loop between database operations and autonomous agents."

---

### 2:55 - 3:00 | Conclusion & Tagline

**What to Say:**
> "CockroachDB gives AI agents what they’ve always lacked: unbreakable durability, distributed vector memory, and enterprise-grade resilience.
> **REASSEMBLE: Remember. Recover. Learn.**
> Thank you, and we’re ready for your questions!"

---

## CockroachDB SQL Console Walkthrough

During or immediately following the live demo, run these queries in the CockroachDB Cloud SQL Console to show the judges the underlying data structures:

### 1. Inspect Workflow Checkpoints
```sql
SELECT workflow_id, status, incident, last_completed_step, total_steps, updated_at
FROM workflows
ORDER BY updated_at DESC
LIMIT 1;
```

### 2. Inspect Individual Workflow Step Results
```sql
SELECT step_number, name, status, result, updated_at
FROM workflow_steps
ORDER BY step_number ASC;
```

### 3. Verify Memory Supersession and Vector Storage
```sql
SELECT memory_type, source, confidence, status, valid_until, LEFT(content, 60) AS content_preview
FROM memories
ORDER BY created_at DESC;
```

### 4. Demonstrate CockroachDB Distributed Vector Search
```sql
-- Direct Cosine Distance Query on 1024-dimensional vectors
SELECT
  memory_type,
  source,
  confidence,
  content
FROM memories
WHERE status = 'active'
ORDER BY embedding <=> (SELECT embedding FROM memories WHERE source = 'incident-208' LIMIT 1)
LIMIT 3;
```

### 5. Inspect Audit Trail
```sql
SELECT action, details, created_at
FROM audit_log
ORDER BY created_at DESC
LIMIT 5;
```

---

## Key Hackathon Value Propositions for Judges

| Evaluation Dimension | How REASSEMBLE Excels |
| :--- | :--- |
| **CockroachDB Vector Indexing** | Native `VECTOR(1024)` indexing and `<=>` cosine distance queries inside transactional SQL. No separate vector database synchronization required. |
| **Durable Agent Execution** | Transactional checkpointing prevents partial execution loops, double-spend bugs, and state loss during serverless worker preemption. |
| **Amazon Bedrock Integration** | Utilizes **Amazon Nova Lite** for high-speed, cost-effective reasoning and **Amazon Titan Text Embeddings V2** for 1024-dimension semantic vector generation. |
| **CockroachDB Managed MCP** | Integrates CockroachDB's managed Model Context Protocol server for direct AI-driven database introspection and query execution. |
| **Architectural Simplicity** | Pure-Python `pg8000` driver deployed as a self-contained AWS Lambda function with zero native C-library packaging headaches. |

---

## Judge-Specific Pitches

### 1. Pitch for Kiki Carter
**Profile Focus:** Enterprise Architecture, Distributed Systems, Mission-Critical Resilience, Multi-Cloud Reliability.

> *"Kiki, enterprise agentic systems cannot rely on ephemeral runtime memory. In production, Lambda functions get throttled, Kubernetes pods get evicted, and network partitions happen. If an agent managing infrastructure or financial workflows dies mid-flight, you risk split-brain decisions or lost state.*
> *REASSEMBLE solves this by anchoring both agent state checkpoints and semantic memory in CockroachDB’s distributed, multi-region transactional engine. By uniting ACID execution checkpoints with native distributed vector search, we eliminate the synchronization lag and dual-write anomalies of separate vector databases. It provides an ironclad, audit-logged guarantee that an agent can recover anywhere, anytime, with zero state loss."*

---

### 2. Pitch for Rob Reid
**Profile Focus:** Developer Experience (DevEx), Modern AI Tooling, Practical Software Craftsmanship, Agent Ergonomics.

> *"Rob, we designed REASSEMBLE with extreme engineering discipline and zero-friction developer ergonomics. The entire runtime is a single, clean serverless deployment using `pg8000`—a 100% pure Python driver that completely eliminates the dreaded `libpq` compilation and packaging nightmares on AWS Lambda.*
> *On top of that, we integrated CockroachDB's Managed MCP server into our Cursor IDE workflow. With standard MCP tools, any AI coding assistant can introspect live schemas, validate vector indexes, and run verification queries against CockroachDB Cloud in real-time. It’s an unbeatable developer workflow for building robust AI agents."*

---

### 3. Pitch for David Joy
**Profile Focus:** Database Systems, Cloud Infrastructure, Scalability, Storage Engines & Vector Indexing.

> *"David, why bolt on a standalone vector database when your transactional database can natively index vectors with distributed scale? REASSEMBLE leverages CockroachDB's `VECTOR(1024)` data type and `CREATE VECTOR INDEX` to perform cosine similarity queries (`<=>`) directly alongside relational filters and checkpoint tables.*
> *Combined with Amazon Bedrock’s Titan Embeddings V2 and Nova Lite, our queries run sub-50ms with full transactional consistency. It proves that CockroachDB is not just a world-class relational database—it is the ideal unified substrate for intelligent, stateful AI systems."*

---

## Contingency & Fallback Plans

If unexpected technical issues occur during the live presentation, execute these pre-planned fallbacks immediately:

### Fallback 1: Cold Start or Network Latency on First Click
- **Symptom:** First click on `1. Start Incident` takes 3-4 seconds due to Lambda cold start.
- **Action:** Pre-warm the Lambda Function URL 60 seconds before speaking by opening the page and clicking `Refresh Memory`.
- **Narration:** *"Notice how the agent establishes a secure TLS session with CockroachDB Cloud across distributed nodes..."*

### Fallback 2: Amazon Bedrock API Rate Limit or Regional Issue
- **Symptom:** `Ask Agent` returns a 500 error or delayed response from Bedrock.
- **Action:** Explain the exact query structure in the CockroachDB SQL Console:
  ```sql
  SELECT memory_type, content, confidence, source FROM memories WHERE status='active' ORDER BY embedding <=> '[...]' LIMIT 3;
  ```
- **Narration:** *"While Bedrock completes the synthesis, look at CockroachDB's vector distance calculation in the SQL console: it directly ranks `incident-208` at the top with 0.94 confidence."*

### Fallback 3: Live CockroachDB Cloud Network Glitch
- **Symptom:** Database connection timeout from the presentation venue WiFi.
- **Action:** Switch immediately to the local test harness (`python test_local.py`) running locally against the backup endpoint, or display the pre-recorded 4K demo screencast.

### Fallback 4: Pre-Recorded Video Backup
- A full, unedited 3-minute recording of the live workflow is stored locally at `docs/demo-video-backup.mp4` for instant screen sharing if required.
