# REASSEMBLE — Git Commit & Branching Conventions

> **Standard:** Conventional Commits v1.0.0  
> **Repository:** REASSEMBLE — Durable Agent Memory

---

## 1. Commit Message Structure

Every commit message must follow the Conventional Commits format:

```
<type>(<scope>): <short summary in imperative mood>

[optional multi-line body explaining WHY and WHAT changed]

[optional footer(s), e.g., references or breaking changes]
```

### 1.1 Header Format Rules
- **Subject line length:** 50–72 characters maximum.
- **Case:** Lowercase type and scope. Subject starts with a lowercase letter or standard term (e.g., `feat(crdb): add vector distance ordering`).
- **Punctuation:** No trailing period (`.`) in the subject line.
- **Mood:** Use the imperative, present tense ("add", "fix", "update", NOT "added", "fixing", "updated").

---

## 2. Commit Types

| Type | Description | Example |
| :--- | :--- | :--- |
| `feat` | New feature or capability for the agent, UI, or API | `feat(bedrock): add Nova Lite reasoning prompt` |
| `fix` | Bug fix or patch | `fix(crdb): handle pg8000 connection timeout gracefully` |
| `docs` | Documentation updates (README, rules, guides, demo script) | `docs(rules): add memory supersession and agent rules` |
| `refactor` | Code refactoring with no behavior change | `refactor(lambda): extract query execution into db helper` |
| `perf` | Performance improvement (e.g., query tuning, index optimization) | `perf(crdb): add vector index on memories embedding` |
| `chore` | Maintenance tasks, dependency updates, zip packaging scripts | `chore(deps): update requirements.txt for pg8000` |
| `ui` | Frontend styling, layout adjustments, HTML/CSS tweaks | `ui(dashboard): improve step indicator and memory cards` |
| `test` | Adding or updating tests or verification scripts | `test(mcp): verify select_query MCP tool responses` |

---

## 3. Allowed Scopes

Scopes categorize the component of the REASSEMBLE architecture affected:

- `lambda` — AWS Lambda handler, routing, request/response lifecycle
- `crdb` — CockroachDB queries, connection management, pg8000 driver
- `schema` — SQL tables (`memories`, `workflows`, `workflow_steps`, `audit_log`), DDL
- `bedrock` — Amazon Bedrock integration (Nova Lite, Titan Embeddings V2)
- `mcp` — CockroachDB Managed MCP configuration (`.cursor/mcp.json`)
- `ui` — Web frontend (HTML, CSS, vanilla JS, demo action buttons)
- `rules` — Repository rules, coding standards, agent behavioral instructions
- `deps` — Python dependencies, packaging, build scripts

---

## 4. Branch Naming Conventions

All feature and bug branches must use kebab-case with an appropriate prefix:

```
<prefix>/<short-description>
```

| Branch Type | Prefix | Example |
| :--- | :--- | :--- |
| **Feature** | `feature/` | `feature/vector-memory-search`, `feature/mcp-integration` |
| **Bug Fix** | `bugfix/` | `bugfix/fix-pg8000-ssl-url-parsing`, `bugfix/step-render-overflow` |
| **Urgent Hotfix** | `hotfix/` | `hotfix/lambda-bedrock-permission-timeout` |
| **Documentation** | `docs/` | `docs/add-project-rules-and-demo-script` |
| **Chore / Setup** | `chore/` | `chore/prepare-lambda-deployment-zip` |

---

## 5. Commit Description Guidelines (What to Include in the Body)

When a change is non-trivial, include a body separated by an empty line with the following details:

1. **Context & Rationale:** Why is this change necessary? What problem does it solve?
2. **Key Changes:** Bulleted list of specific implementation details.
3. **Verification / Testing:** How was the change tested (e.g., Lambda invocation, local test, CockroachDB MCP query check)?

### Concrete Examples

#### Example 1: New Feature
```git
feat(crdb): add vector indexing and cosine distance search for agent memories

Implement distributed vector search using CockroachDB vector indexing.
Memories are converted to 1024-dimension embeddings via Titan Embeddings V2
and queried using the <=> operator.

- Add memories_embedding_idx VECTOR INDEX to schema.sql
- Implement retrieve_memories() with active status filter and top-K limit
- Connect Bedrock embedding generation with CockroachDB query

Tested locally and on AWS Lambda with 5 sample incident memories.
```

#### Example 2: Bug Fix
```git
fix(lambda): correct pg8000 connection parameters parsing

pg8000 does not parse full postgresql:// URI strings directly.
Extracted urlparse components to pass explicit host, port, user,
password, database, and ssl_context kwargs.

- Resolve connection failure on CockroachDB Cloud cluster
- Set connection timeout to 15 seconds to avoid Lambda freeze
```

#### Example 3: Documentation / Rules
```git
docs(rules): define agent decision rules and checkpoint discipline

Add ai-agent-rules.md and project-rules.md specifying:
- Confidence score thresholds for memory retrieval
- Memory supersession rules (incident-208 superseding incident-143)
- Checkpoint discipline prior to risky agent operations
- Scope restrictions for hackathon MVP delivery
```

---

## 6. Pre-Commit Checklist

Before pushing commits:
- [ ] No API keys, passwords, or connection URLs committed (`CRDB_URL`, AWS secret keys).
- [ ] Code passes basic linting and syntax validation.
- [ ] Schema changes in `schema.sql` match `ensure_schema()` in `lambda_function.py`.
- [ ] Commit message conforms to `type(scope): description`.
