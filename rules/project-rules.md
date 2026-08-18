# REASSEMBLE — Project Rules & Scope Guardrails

> **Hackathon Deadline:** August 19, 2026 @ 02:30 AM IST  
> **Current Focus:** Delivering a flawless end-to-end demo of durable agent memory and checkpoint recovery.

---

## 1. Project Mission & Value Proposition

REASSEMBLE proves that AI agent memory and execution state must not live in transient runtime memory. When an agent crashes, experiences network timeouts, or transitions across workers, its state must be reconstructible from **CockroachDB**, while **Amazon Bedrock** provides reasoning and embeddings.

### Core Demo Story Arc
```
Agent starts incident -> Checkpoint 1 committed to CockroachDB
                      -> Checkpoint 2 committed
                      -> Simulated Worker Crash (Lambda execution killed)
                      -> New worker spawns -> Reads CockroachDB state
                      -> Resumes at Checkpoint 3 & 4
                      -> Commits validated lesson -> Supersedes outdated memory
                      -> Semantic Q&A proves agent learned new ground truth
```

---

## 2. Priority Ordering

All development decisions must follow this strict priority hierarchy:

```
1. WORKING LIVE DEMO (Top Priority)
   └── End-to-end incident flow + crash simulation + state recovery + semantic memory recall works reliably.

2. CLEAN & ROBUST CORE CODE
   └── Reliable SQL queries, safe connection handling, error catching, clean prompt engineering.

3. ESSENTIAL DEMO FEATURES
   └── Vector search, memory supersession toggle, audit log visibility, MCP query verification.

4. POLISHED DOCUMENTATION
   └── Demo script, architecture diagrams, clear rules and commit history.
```

---

## 3. Decision-Making Framework

When faced with a technical choice or feature idea:

1. **Does this strengthen the 3-minute judge demo?**
   - If **NO**, reject or defer immediately.
   - If **YES**, proceed to question 2.
2. **Can it be implemented, tested, and verified in < 30 minutes?**
   - If **NO**, simplify to an MVP version that fits the time budget.
3. **Does it introduce external dependencies or build complexity?**
   - If it requires compiling heavy native C binaries, setting up external auth providers, or npm build pipelines, **DO NOT BUILD IT**. Keep the stack lightweight (`pg8000`, `boto3`, vanilla HTML/JS).

---

## 4. Time Management & Timeline (Final Countdown)

| Time Window (IST) | Phase | Deliverables / Goals |
| :--- | :--- | :--- |
| **09:00 PM – 10:30 PM** | **Core Stability & Verification** | Complete database schema, verify vector indexing on CockroachDB, test Bedrock Nova Lite & Titan Embeddings integration. |
| **10:30 PM – 12:00 AM** | **End-to-End Demo Flow** | Verify full web UI cycle: Start Incident $\to$ Crash $\to$ Resume $\to$ Ask Agent. Test Managed MCP access. |
| **12:00 AM – 01:30 AM** | **Feature Freeze & Lambda Polish** | Package Lambda deployment zip, configure Function URL, test cold-starts, verify CORS and SSL. Zero new features after 1:00 AM. |
| **01:30 AM – 02:15 AM** | **Dry Runs & Documentation** | Run demo script 3 times end-to-end. Finalize README, screenshots, and submission materials. |
| **02:15 AM – 02:30 AM** | **Final Buffer & Submission** | Submit project link, repository, and demo video/walkthrough before 2:30 AM IST deadline. |

---

## 5. Strict "DO NOT ADD" List (Out of Scope)

The following components are explicitly **FORBIDDEN** for the hackathon MVP to prevent scope creep, dependency hell, and deployment failures:

| Forbidden Component | Why It Is Excluded | What We Use Instead |
| :--- | :--- | :--- |
| **User Authentication / Login / OAuth / Cognito** | Adds 2+ hours of configuration with zero demo value for judges | Public Lambda Function URL with demo state IDs |
| **Stripe / Billing / Payments API** | Irrelevant to durable agent memory demo | Simulated incident domain context |
| **React / Next.js / Vue / Webpack / Vite** | Requires Node build step, bundle size overhead, asset hosting | Single-file embedded HTML/CSS/Vanilla JS served by Lambda |
| **Kubernetes / ECS / Docker Orchestration** | Deployment complexity and long iteration cycles | Serverless AWS Lambda Function URL |
| **Redis / Memcached / In-Memory Cache** | Defeats the core thesis that CockroachDB is the single durable state store | CockroachDB distributed tables + vector indexes |
| **Complex Microservices / Multiple Lambdas** | Coordination overhead and multi-repo friction | Single cohesive Lambda handler with clean route dispatching |
| **Heavy ORM (SQLAlchemy, Django ORM)** | Cold-start penalty, package size inflation | Lightweight direct SQL with pure Python `pg8000` |

---

## 6. Security Rules for Hackathon MVP

1. **No Credentials in Source Control:**
   - `.env`, `.cursor/mcp.json`, and database passwords must be excluded via `.gitignore`.
2. **Lambda Environment Variables:**
   - Store `CRDB_URL`, `CHAT_MODEL_ID`, and `EMBED_MODEL_ID` securely in Lambda configuration.
3. **SSL Enforcement:**
   - All CockroachDB connections must use TLS/SSL (`sslmode=verify-full`).
4. **Parameterized SQL:**
   - Never use string interpolation in SQL queries. Always use `%s` placeholders to prevent SQL injection.
5. **IAM Least Privilege:**
   - Lambda execution role requires Bedrock runtime permissions (`bedrock:InvokeModel`, `bedrock:Converse`) and standard CloudWatch logging only.
