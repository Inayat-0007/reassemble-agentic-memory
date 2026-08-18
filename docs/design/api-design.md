# REASSEMBLE — API Design Document

**Project:** REASSEMBLE — Durable Agent Memory  
**Component:** RESTful API Specification  
**Protocol:** HTTPS / JSON over AWS Lambda Function URL  
**CORS Policy:** Universal (`*`) enabled for web client integration  

---

## 1. API Architecture & Global Conventions

The REASSEMBLE API exposes six primary HTTP endpoints handled by a unified AWS Lambda controller (`lambda_function.py`). All responses conform to standard HTTP status codes and provide JSON payloads (except `GET /` which serves the embedded SPA).

### 1.1 Standard Response Headers
Every API response returned by AWS Lambda includes the following standardized HTTP headers:

```http
Content-Type: application/json
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: content-type
Access-Control-Allow-Methods: GET,POST,OPTIONS
```

### 1.2 Error Response Format
When an exception occurs during request execution, the API returns a structured JSON error body:

```json
{
  "error": "Descriptive error message string"
}
```

---

## 2. Endpoint Specifications

### 2.1 `GET /` — Single Page Application UI

Serves the interactive single-page application (SPA) client directly from Lambda.

- **HTTP Method:** `GET`
- **Path:** `/`
- **Content-Type:** `text/html; charset=utf-8`
- **Authentication:** None (Public)

#### Request
- **Headers:** None required.
- **Request Body:** None.

#### Response
- **Status Code:** `200 OK`
- **Body:** Complete standalone HTML5 document containing the UI layout, styling, and client-side JavaScript controllers.

#### Error Cases
| Status Code | Reason | Response Body |
| :--- | :--- | :--- |
| `500 Internal Server Error` | Unexpected execution failure in handler | `{"error": "<exception_details>"}` |

---

### 2.2 `POST /api/memories` — Refresh & Ingest Memory

Initializes the schema if absent, seeds baseline incident memories if unpopulated, and retrieves top active semantic memories using vector search.

- **HTTP Method:** `POST`
- **Path:** `/api/memories`
- **Content-Type:** `application/json`

#### Request
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {}
  ```

#### Response
- **Status Code:** `200 OK`
- **Response Body Example:**
  ```json
  {
    "answer": "Loaded persistent semantic memory from CockroachDB.",
    "memories": [
      {
        "id": "1d8b945e-6e2c-49a8-a3f2-c9a173820b12",
        "memory_type": "runbook",
        "content": "Runbook #12: If checkout latency exceeds 2 seconds, inspect payment database connection pressure, active sessions, and recent deployment changes.",
        "confidence": 0.95,
        "source": "runbook-12",
        "status": "active"
      },
      {
        "id": "3a7c81df-29bb-41a4-9271-e5d893f18a44",
        "memory_type": "architecture",
        "content": "Architecture Decision #72: The payment service was migrated from PostgreSQL to CockroachDB. Connection behavior and operational limits must be evaluated on the new architecture.",
        "confidence": 0.98,
        "source": "decision-72",
        "status": "active"
      },
      {
        "id": "5f210d7a-1123-4c91-bdf0-7a8e2354c009",
        "memory_type": "incident",
        "content": "Incident #143: Checkout latency increased after a deployment. Engineers initially suspected payment database connection-pool exhaustion.",
        "confidence": 0.72,
        "source": "incident-143",
        "status": "active"
      }
    ]
  }
  ```

#### Database Operations
1. `ensure_schema(c)`: Runs DDL statements to ensure `memories`, `workflows`, `workflow_steps`, `audit_log`, and `memories_embedding_idx` exist.
2. `seed_memories(c)`: Checks row count; if empty, embeds and inserts baseline demo memories with Titan Text Embeddings V2.
3. `retrieve_memories(c, query, limit=5)`: Vector similarity query using `<=>` against `"checkout latency after deployment"`.

#### Error Cases
| Status Code | Condition | Example Response |
| :--- | :--- | :--- |
| `500 Internal Server Error` | Database connection timeout or Bedrock embedding failure | `{"error": "connection to server at 'host' failed: timeout"}` |

---

### 2.3 `POST /api/chat` — Agent Chat & Memory Reassembly

Accepts a user natural language query, computes its semantic embedding, queries CockroachDB for relevant active memories, and calls Amazon Bedrock Nova Lite to synthesize a reasoned response.

- **HTTP Method:** `POST`
- **Path:** `/api/chat`
- **Content-Type:** `application/json`

#### Request
- **Headers:** `Content-Type: application/json`
- **Request Body Schema:**
  ```json
  {
    "message": "string (required)",
    "workflow_id": "string (optional UUID)"
  }
  ```
- **Request Body Example:**
  ```json
  {
    "message": "Why is checkout latency high and what should we do?",
    "workflow_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
  }
  ```

#### Response
- **Status Code:** `200 OK`
- **Response Body Example:**
  ```json
  {
    "answer": "Based on retrieved operational records, checkout latency is elevated due to Deployment v2.8, which introduced a connection leak in the payment service (Incident #208).\n\nKey Analysis:\n1. Runbook #12 and Incident #143 originally suspected connection pool exhaustion.\n2. However, Incident #191 proved that increasing pool size does not resolve root cause.\n3. The latest validated finding (Incident #208, 94% confidence) supersedes older pool exhaustion theories.\n\nRecommended Action:\nRoll back Deployment v2.8 immediately and apply the connection leak fix. Do not increase database pool size.",
    "memories": [
      {
        "id": "7c1234ef-89ab-4cde-0123-456789abcdef",
        "memory_type": "validated_lesson",
        "content": "Incident #208: Deployment v2.8 introduced a connection leak in the payment service. The validated remediation was to roll back the deployment and fix the leak, not to blindly increase the pool size.",
        "confidence": 0.94,
        "source": "incident-208",
        "status": "active"
      },
      {
        "id": "1d8b945e-6e2c-49a8-a3f2-c9a173820b12",
        "memory_type": "runbook",
        "content": "Runbook #12: If checkout latency exceeds 2 seconds, inspect payment database connection pressure, active sessions, and recent deployment changes.",
        "confidence": 0.95,
        "source": "runbook-12",
        "status": "active"
      }
    ]
  }
  ```

#### Processing Pipeline
1. `bedrock_embed(message)`: Invokes Titan Text Embeddings V2 with dimension=1024.
2. `retrieve_memories(...)`: Executes `ORDER BY embedding <=> %s::VECTOR LIMIT 5` on active records.
3. `generate_answer(...)`: Prompts Nova Lite via `bedrock.converse` with system prompt enforcing memory provenance and contradiction detection.

#### Error Cases
| Status Code | Condition | Example Response |
| :--- | :--- | :--- |
| `500 Internal Server Error` | Model invocation error or invalid JSON body | `{"error": "Bedrock converse throttled"}` |

---

### 2.4 `POST /api/demo/start` — Initialize Workflow Incident

Starts an autonomous incident response workflow and commits durable Step 1 checkpoint.

- **HTTP Method:** `POST`
- **Path:** `/api/demo/start`
- **Content-Type:** `application/json`

#### Request
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {}
  ```

#### Response
- **Status Code:** `200 OK`
- **Response Body Example:**
  ```json
  {
    "workflow_id": "c71a39f0-2651-40e9-91fb-7cf4a406606f",
    "answer": "Workflow created. Durable checkpoint 1 committed. Memory retrieval is ready.",
    "state": {
      "workflow_id": "c71a39f0-2651-40e9-91fb-7cf4a406606f",
      "status": "INVESTIGATING",
      "last_completed_step": 1,
      "total_steps": 4
    },
    "memories": [
      {
        "id": "5f210d7a-1123-4c91-bdf0-7a8e2354c009",
        "memory_type": "incident",
        "content": "Incident #143: Checkout latency increased after a deployment...",
        "confidence": 0.72,
        "source": "incident-143",
        "status": "active"
      }
    ]
  }
  ```

#### Transactional Steps Committed
1. Generates `workflow_id = gen_random_uuid()`.
2. Inserts row into `workflows` with `status = 'INVESTIGATING'`.
3. Inserts 4 child rows into `workflow_steps` (`1: Load incident context`, `2: Retrieve relevant memory`, `3: Validate current hypothesis`, `4: Commit resolution memory`).
4. Updates Step 1 status to `COMPLETED` and updates `workflows.last_completed_step = 1`.
5. Inserts audit event `WORKFLOW_CREATED`.

---

### 2.5 `POST /api/demo/crash` — Simulate Worker Interruption

Simulates a sudden compute worker termination mid-execution. Durably commits Step 2 and sets status to `INTERRUPTED`.

- **HTTP Method:** `POST`
- **Path:** `/api/demo/crash`
- **Content-Type:** `application/json`

#### Request
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "workflow_id": "c71a39f0-2651-40e9-91fb-7cf4a406606f"
  }
  ```

#### Response
- **Status Code:** `200 OK`
- **Response Body Example:**
  ```json
  {
    "workflow_id": "c71a39f0-2651-40e9-91fb-7cf4a406606f",
    "answer": "⚠️ Worker interrupted after checkpoint 2. The important state is already persisted in CockroachDB.",
    "state": {
      "workflow_id": "c71a39f0-2651-40e9-91fb-7cf4a406606f",
      "status": "INTERRUPTED",
      "last_completed_step": 2,
      "total_steps": 4
    },
    "memories": [...]
  }
  ```

#### Transactional Steps Committed
1. Updates `workflow_steps` (Step 2) to `COMPLETED` with result *"Memory retrieval checkpoint committed."*.
2. Updates `workflows` record to `status = 'INTERRUPTED'` and `last_completed_step = 2`.
3. Commits `audit_log` entry with action `SIMULATED_CRASH`.

#### Error Cases
| Status Code | Condition | Example Response |
| :--- | :--- | :--- |
| `500 Internal Server Error` | Missing `workflow_id` parameter | `{"error": "Start the demo first."}` |

---

### 2.6 `POST /api/demo/resume` — Reconstruct State & Resume

Invoked by a newly spawned worker to reconstruct state from CockroachDB, finish remaining steps, and store validated learnings that supersede older hypotheses.

- **HTTP Method:** `POST`
- **Path:** `/api/demo/resume`
- **Content-Type:** `application/json`

#### Request
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "workflow_id": "c71a39f0-2651-40e9-91fb-7cf4a406606f"
  }
  ```

#### Response
- **Status Code:** `200 OK`
- **Response Body Example:**
  ```json
  {
    "workflow_id": "c71a39f0-2651-40e9-91fb-7cf4a406606f",
    "answer": "✅ New worker reconstructed state from CockroachDB, completed the remaining steps, and stored a validated memory that supersedes older advice.",
    "state": {
      "workflow_id": "c71a39f0-2651-40e9-91fb-7cf4a406606f",
      "status": "COMPLETED",
      "last_completed_step": 4,
      "total_steps": 4
    },
    "memories": [
      {
        "id": "e932b1a8-5544-482e-9901-7299a9cfb011",
        "memory_type": "validated_lesson",
        "content": "Incident #208: Deployment v2.8 introduced a connection leak in the payment service. The validated remediation was to roll back the deployment and fix the leak, not to blindly increase the pool size.",
        "confidence": 0.94,
        "source": "incident-208",
        "status": "active"
      }
    ]
  }
  ```

#### Transactional Steps Committed
1. Reads `workflows` record to confirm existence and current step index.
2. Updates Step 3 and Step 4 in `workflow_steps` to `COMPLETED`.
3. Updates `workflows` to `status = 'COMPLETED'` and `last_completed_step = 4`.
4. Idempotently inserts `incident-208` memory into `memories` table with vector embedding and confidence `0.94`.
5. Executes supersession query:
   ```sql
   UPDATE memories 
   SET status = 'superseded', valid_until = now() 
   WHERE source = 'incident-143' AND status = 'active';
   ```
6. Commits `audit_log` entry with action `WORKFLOW_COMPLETED`.

#### Error Cases
| Status Code | Condition | Example Response |
| :--- | :--- | :--- |
| `500 Internal Server Error` | Missing `workflow_id` or workflow ID does not exist | `{"error": "Workflow not found."}` |
