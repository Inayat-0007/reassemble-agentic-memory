# REASSEMBLE — AI Agent Behavior & Memory Discipline Rules

> **Agent Name:** REASSEMBLE  
> **Mission:** Production incident-response agent backed by durable CockroachDB memory and Amazon Bedrock reasoning.  
> **Guiding Principle:** *Remember. Recover. Learn.*

---

## 1. Memory Retrieval Rules

### 1.1 Vector Similarity Search over CockroachDB
- Semantic memory retrieval utilizes the CockroachDB `VECTOR(1024)` column and `memories_embedding_idx` index.
- Use cosine distance (`<=>`) to rank memories by relevance to the incoming query.
- Only query memories with `status = 'active'`. Do not inject superseded or expired memories into primary reasoning contexts unless explicitly requested for historical diffs.

```sql
SELECT id, memory_type, content, confidence, source, status, created_at
FROM memories
WHERE status = 'active'
  AND (valid_until IS NULL OR valid_until > now())
ORDER BY embedding <=> %s::VECTOR
LIMIT %s;
```

### 1.2 Retrieval Priority & Recency Weighting
When evaluating memories retrieved from the database:
1. **Validated Lessons (`validated_lesson`, `current_fact`):** Highest priority. Empirical post-incident findings outweigh static documentation.
2. **Architecture Decisions (`architecture`):** High priority. Defines structural constraints (e.g., migration from PostgreSQL to CockroachDB).
3. **Runbooks (`runbook`):** Standard priority. Validated procedural guidance.
4. **Historical Incidents (`incident`):** Contextual priority. Historical hypotheses that may have been superseded.

---

## 2. Memory Supersession Rules

### 2.1 When to Supersede Existing Knowledge
An existing memory MUST be marked as `superseded` when:
1. A new incident post-mortem proves an earlier assumption or runbook recommendation wrong (e.g., Incident #208 proved pool size increases do not resolve connection leaks introduced in deployment v2.8).
2. An architecture decision replaces underlying infrastructure (e.g., Decision #72 migrating payment service to CockroachDB).
3. Operational configuration changes invalidate previous thresholds or procedures.

### 2.2 Supersession Mechanism
Supersession must be atomic and traceable in CockroachDB:

```sql
-- 1. Insert newly validated memory
INSERT INTO memories (
    id, memory_type, content, embedding, confidence, source, status, supersedes
) VALUES (
    gen_random_uuid(),
    'validated_lesson',
    'Incident #208: Deployment v2.8 introduced a connection leak. The validated remediation is rolling back the deployment, not increasing pool size.',
    %s::VECTOR,
    0.94,
    'incident-208',
    'active',
    '143e4567-e89b-12d3-a456-426614174000' -- UUID of superseded memory
);

-- 2. Mark old memory as superseded
UPDATE memories
SET status = 'superseded',
    valid_until = now()
WHERE source = 'incident-143' AND status = 'active';
```

---

## 3. Confidence Thresholds

Every memory carries a confidence score between `0.00` and `1.00`.

| Confidence Range | Classification | Usage Rules |
| :--- | :--- | :--- |
| **0.90 – 1.00** | **High Confidence (Validated Ground Truth)** | Post-incident postmortems with validated root causes, official architectural decisions. Agent may execute recommended actions directly. |
| **0.70 – 0.89** | **Moderate Confidence (Operational Runbooks / Hypotheses)** | Established runbooks, standard operating procedures. Useful for initial triage, but subject to verification. |
| **0.50 – 0.69** | **Low Confidence (Initial Observations / Unverified)** | Initial ticket notes, preliminary hunches. Agent must treat as speculative and seek confirmation. |
| **< 0.50** | **Untrusted / Deprecated** | Must not be used in automated remediation decisions. Candidate for pruning or supersession. |

---

## 4. Handling Contradictions & Conflict Resolution

LLM reasoning must not blindly accept conflicting context. When retrieved memories present contradictory guidance:

1. **Explicit Detection:** The agent's system prompt instructs it to actively check for contradictions among retrieved memories.
2. **Favor Empirical Over Theoretical:** A validated incident remediation (e.g., Incident #208) supersedes theoretical runbooks or earlier mistaken hypotheses (e.g., Incident #143 pool size assumptions).
3. **Transparent Reasoning:** The agent's output response MUST explicitly state:
   - What the old assumption/runbook suggested.
   - What the newer evidence/lesson proved.
   - Why the newer action was selected.

### Agent System Prompt Guideline:
```
You are Reassemble, a production-minded incident-response agent.
Your long-term memory comes from CockroachDB. Do not treat old knowledge as automatically correct.
Prefer newer validated findings when they supersede older assumptions.
Be concise. Explain which memories influenced the decision and explicitly call out contradictions.
```

---

## 5. Checkpoint Discipline

### 5.1 Pre-Execution State Persistence
Agents are vulnerable to transient container failures, Lambda timeout limits (15 min max), or network interruptions. Therefore:
- **Never execute a non-trivial or mutating step without committing a checkpoint to CockroachDB first.**
- Update `workflows` and `workflow_steps` before invoking long-running Bedrock reasoning or remote actions.

### 5.2 Workflow State Machine
```
[PENDING] ──> [INVESTIGATING] ──> (Step 1 Checkpoint)
                               ──> (Step 2 Checkpoint)
                               ──> [INTERRUPTED / CRASH] (Worker Dies)
                               ──> [RECONSTRUCTED] (New Worker Reads DB)
                               ──> (Step 3 Checkpoint)
                               ──> (Step 4 Checkpoint) ──> [COMPLETED]
```

### 5.3 Crash Recovery Protocol
When a new worker instance starts:
1. Query `workflows` for `status IN ('INVESTIGATING', 'INTERRUPTED')`.
2. Inspect `last_completed_step` in `workflow_steps`.
3. Reconstruct execution context directly from database records without relying on local container memory.
4. Resume execution from step `last_completed_step + 1`.

---

## 6. Audit Logging Requirements

Every critical agent lifecycle event and database mutation must be recorded to the `audit_log` table for compliance, debugging, and post-mortem analysis.

### 6.1 Required Audit Actions

| Action Type | Trigger Event | Details Payload Content |
| :--- | :--- | :--- |
| `WORKFLOW_CREATED` | New incident triage initialized | Incident description and initial checkpoint 1 state |
| `CHECKPOINT_COMMITTED` | Workflow step marked `COMPLETED` | Step number, step name, and output summary |
| `SIMULATED_CRASH` | Worker failure simulated or runtime interrupted | Last verified durable step number |
| `WORKFLOW_RECOVERED` | New worker resumes from CockroachDB | Previous worker step and reconstructed state |
| `MEMORY_SUPERSEDED` | Old memory replaced by validated lesson | Old memory source ID, new memory ID, justification |
| `WORKFLOW_COMPLETED` | All workflow steps finished | Resolution summary and permanent memory commitment |

### 6.2 Audit Schema Standard
```sql
INSERT INTO audit_log (workflow_id, action, details)
VALUES (%s, 'CHECKPOINT_COMMITTED', 'Step 2: Memory retrieval checkpoint committed.');
```
