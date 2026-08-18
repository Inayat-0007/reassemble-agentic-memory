# REASSEMBLE — Brainstorm & Ideas

> Captured: 2026-08-18 21:00 IST

## Core Concept

**"The model is non-deterministic. The state underneath it isn't."**

### The One-Liner
> RAG retrieves. Reassemble reconstructs.

### The Elevator Pitch
> AI agents lose their memory when they crash. Reassemble gives them durable memory backed by CockroachDB — semantic knowledge, workflow checkpoints, and audit trails that survive any failure.

---

## MVP Scope (Hackathon — Aug 18-19, 2026)

### ✅ Build Now
- [x] Semantic memory with vector embeddings (CockroachDB + Titan V2)
- [x] Workflow checkpointing (4-step incident investigation)
- [x] Crash simulation and recovery from durable state
- [x] Memory supersession (new validated facts replace stale advice)
- [x] LLM reasoning over reconstructed context (Nova Lite)
- [x] Audit logging
- [x] Browser-based demo UI
- [x] CockroachDB MCP integration for dev/ops

### ❌ Do NOT Build (Deadline Optimization)
- Login / authentication system
- User accounts or multi-tenancy
- Payment integration
- Complex React/Vue frontend
- Container orchestration (ECS/EKS/K8s)
- SageMaker or custom ML pipelines
- OAuth implementation
- Custom MCP server
- Multi-agent orchestration framework
- Production-grade security hardening

---

## Future Ideas (Post-Hackathon)

### Memory Evolution
- **Confidence decay**: Memories lose confidence over time unless revalidated
- **Memory chains**: Link related memories into reasoning chains
- **Source credibility**: Weight memories by source reliability
- **Conflict resolution**: Automated detection and resolution of contradictory memories
- **Memory compaction**: Summarize and merge similar old memories

### Multi-Agent Collaboration
- Shared memory pool across multiple agents
- Agent-specific memory namespaces
- Memory access control (read/write permissions per agent)
- Collaborative learning (one agent's validated finding becomes another's knowledge)

### Advanced Workflows
- Branching workflows (decision trees)
- Parallel step execution
- Conditional checkpoints
- Workflow templates for common incident types
- Automatic retry with exponential backoff

### Observability & Analytics
- Memory usage dashboards
- Workflow completion metrics
- Supersession frequency analysis
- Embedding space visualization
- Agent decision audit trails

### Enterprise Features
- Role-based access control
- Tenant isolation
- Compliance audit export
- Data retention policies
- Encryption at rest for sensitive memories

---

## Judge-Specific Angles

### Kiki Carter — Product/Impact
> "The model is non-deterministic. The state underneath it isn't."
- Focus on: reliability, crash recovery, real-world ops scenarios
- Show: workflow surviving worker death

### Rob Reid — Technical Depth
> "We separate semantic memory from transactional workflow state, use a distributed vector index for retrieval, and keep execution checkpoints durable."
- Focus on: schema design, vector indexing, supersession logic
- Show: EXPLAIN query plan, database records

### David Joy — Innovation/Scale
> "Multiple agents can share the same durable memory and workflow state instead of maintaining isolated context windows."
- Focus on: distributed architecture, multi-agent potential
- Show: CockroachDB's distributed nature

---

## Key Technical Insights

1. **Why CockroachDB over pgvector?**
   - Distributed by default — scales horizontally
   - Transactional + vector in the same database
   - No separate vector DB needed (Pinecone, Weaviate, etc.)
   - Managed MCP server for AI tooling

2. **Why single Lambda file?**
   - Minimizes deployment complexity
   - No build step needed
   - Embedded HTML = no CORS issues, no separate hosting
   - Perfect for hackathon deadline

3. **Why memory supersession over versioning?**
   - Agents should act on current best knowledge
   - Old advice (increase pool size) can be actively harmful
   - Supersession creates a clear audit trail
   - Simpler than full version control for MVP

---

## Memorable Quotes for Demo

- "The model can fail. The worker can fail. The agent's memory doesn't have to."
- "RAG retrieves. Reassemble reconstructs."
- "AI agents are non-deterministic. Reassemble makes their memory and execution state durable."
- "The agent didn't just retrieve the old answer. It learned that the old answer became invalid."
- "The worker is gone. But the workflow is not."

---

*Last updated: 2026-08-18 21:00 IST*
