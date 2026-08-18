# REASSEMBLE — Coding Standards & Best Practices

> **Project:** REASSEMBLE — Durable Agent Memory  
> **Runtime:** AWS Lambda (Python 3.11+)  
> **Core Stack:** CockroachDB (Vector Indexing + Managed MCP), Amazon Bedrock (Nova Lite + Titan Embeddings V2), `pg8000`, `boto3`

---

## 1. Python Standards & Code Formatting

### 1.1 PEP 8 Compliance
- Adhere strictly to [PEP 8](https://peps.python.org/pep-0008/) style guidelines.
- Standard 4-space indentation (no tabs).
- Maximum line length: **100 characters** for code; **120 characters** for docstrings and SQL template literals.
- Keep source files organized in logical sections:
  1. Module docstring and global configuration
  2. Standard library imports
  3. Third-party imports (`boto3`, `pg8000`)
  4. Local imports (if modularized)
  5. Constants and environment variables
  6. Database helpers and clients
  7. Domain business logic (Memory, Workflow, Agent reasoning)
  8. Lambda routing and entrypoint (`lambda_handler`)

### 1.2 Type Hints
- Type annotations are strongly encouraged for all function signatures and return types to improve IDE completions, self-documentation, and safety during rapid hackathon iteration.

```python
from typing import Any, Dict, List, Optional, Tuple

def retrieve_memories(
    conn: Any,
    query: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve top-K active memories matching query embedding."""
    ...
```

---

## 2. Naming Conventions

| Category | Convention | Example | Notes |
| :--- | :--- | :--- | :--- |
| **Modules / Files** | `snake_case.py` | `lambda_function.py`, `db_utils.py` | Concise, descriptive |
| **Functions** | `snake_case` | `ensure_schema()`, `retrieve_memories()` | Verb-first action names |
| **Variables / Arguments** | `snake_case` | `workflow_id`, `chat_response` | Descriptive; avoid single letters except loop index |
| **Classes** | `PascalCase` | `MemoryRecord`, `WorkflowState` | Nouns |
| **Constants** | `SCREAMING_SNAKE` | `DEFAULT_TIMEOUT`, `EMBED_DIMENSIONS` | Module-level immutable config |
| **Environment Vars** | `SCREAMING_SNAKE` | `CRDB_URL`, `CHAT_MODEL_ID`, `AWS_REGION` | Passed through Lambda runtime |
| **Database Tables** | `snake_case` (plural) | `memories`, `workflows`, `workflow_steps`, `audit_log` | Matches `schema.sql` |
| **Database Columns** | `snake_case` | `memory_type`, `valid_until`, `last_completed_step` | Consistent SQL dialect |

---

## 3. Database Connection & Query Management (CockroachDB)

### 3.1 Connection Lifecycle in Serverless
AWS Lambda containers are ephemeral and can be frozen or reused across invocations:
- Do **not** open global connection instances that leak or break across freeze/thaw cycles without error recovery.
- Use explicit helper functions to acquire fresh or validated connections.
- Always close cursors in `finally` blocks or context managers.

```python
from urllib.parse import urlparse, unquote
import ssl
import pg8000.dbapi

def get_db_connection():
    """Establish SSL connection to CockroachDB using pg8000."""
    crdb_url = os.environ["CRDB_URL"]
    parsed = urlparse(crdb_url)
    
    params = {
        "host": parsed.hostname,
        "port": parsed.port or 26257,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": (parsed.path or "/defaultdb").lstrip("/"),
        "ssl_context": ssl.create_default_context(),
        "timeout": 15,
    }
    return pg8000.dbapi.connect(**params)
```

### 3.2 SQL Parameterization & Injection Defense
- **NEVER** use Python f-strings or string concatenation for query variables.
- Always use parameterized queries (`%s` placeholders for `pg8000` / PostgreSQL dialect).
- For vector casting, parameterize the vector literal and cast explicitly: `%s::VECTOR`.

```python
# CORRECT
cur.execute(
    """
    SELECT id, content, confidence 
    FROM memories 
    WHERE status = 'active'
    ORDER BY embedding <=> %s::VECTOR
    LIMIT %s
    """,
    (vector_literal, limit)
)

# FORBIDDEN (SQL INJECTION RISK)
# cur.execute(f"SELECT * FROM memories WHERE status = '{status}'")
```

### 3.3 Idempotent Schema Initialization
- All DDL statements must include `IF NOT EXISTS` guards (`CREATE TABLE IF NOT EXISTS`, `CREATE VECTOR INDEX IF NOT EXISTS`).
- DDL errors on vector index creation should be handled gracefully if the index already exists.

---

## 4. Error Handling Patterns

### 4.1 Explicit Exception Handling
- Avoid blanket `except:` clauses without logging. Catch specific exceptions (`pg8000.dbapi.Error`, `botocore.exceptions.BotoCoreError`, `ValueError`, `KeyError`).
- Return structured JSON error responses with proper HTTP status codes.

```python
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handle_api_error(err: Exception) -> Dict[str, Any]:
    logger.error("API Handler Failure: %s", str(err), exc_info=True)
    if isinstance(err, ValueError):
        return response(400, {"error": "Bad Request", "details": str(err)})
    if isinstance(err, KeyError):
        return response(400, {"error": "Missing Required Parameter", "details": str(err)})
    return response(500, {"error": "Internal Server Error", "details": str(err)})
```

### 4.2 Graceful Fallbacks for External Dependencies
- **Bedrock Throttling/Timeouts:** If Bedrock invocation fails during live demo, return an actionable fallback message rather than crashing the Lambda execution context.
- **CockroachDB Connectivity:** Ensure connection timeouts are configured (e.g., 15s) so the Lambda does not hang until execution timeout.

---

## 5. Security Standards

### 5.1 Zero Secret Exposure
- **Never commit credentials:** Passwords, API tokens, service account keys, or connection strings must NEVER be committed to Git.
- Use `.env` locally (git-ignored) and environment variables in AWS Lambda.
- CockroachDB connection strings (`CRDB_URL`) must use SSL (`sslmode=verify-full`).
- Managed MCP service-account tokens must stay in `.cursor/mcp.json` (git-ignored).

### 5.2 Frontend & API Perimeter Security
- The public Lambda Function URL serves the frontend demo UI and JSON API.
- Do not expose administrative DDL or database drop tools to unauthenticated endpoints.
- Client-side code receives only filtered payloads (never raw database credentials or internal AWS role tokens).

---

## 6. AWS Lambda Architecture & Performance Patterns

### 6.1 Cold Start Optimization
- Keep dependencies minimal. The project uses `pg8000` (pure Python, zero binary C-extension compilation issues) and `boto3` (built into the Lambda Python runtime).
- Initialize AWS SDK clients (`boto3.client("bedrock-runtime")`) outside the handler for connection reuse across warm invocations.

### 6.2 Standard HTTP Handler & CORS Structure
- The entrypoint `lambda_handler(event, context)` dispatches routes based on HTTP method and path:
  - `GET /` -> Embedded HTML Web Interface
  - `POST /api/chat` -> Semantic memory retrieval + Bedrock Converse
  - `POST /api/demo/start` -> Start incident workflow + Checkpoint 1
  - `POST /api/demo/crash` -> Simulate worker crash + Checkpoint 2
  - `POST /api/demo/resume` -> Reconstruct state from CockroachDB + Checkpoint 3 & 4
  - `POST /api/memories` -> View active vector memories
- Always return standard CORS headers on both responses and preflight `OPTIONS` requests.
