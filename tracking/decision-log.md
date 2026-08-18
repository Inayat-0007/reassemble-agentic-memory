# Architectural Decision Log

This log records key architectural, design, and implementation decisions made during the development of REASSEMBLE.

## Decision Summary

| Date | Decision | Rationale | Status |
| :--- | :--- | :--- | :--- |
| 2026-08-18 | Use single Lambda file | Maximizes development velocity, eliminates import path complexity, and ensures zero packaging mismatches under tight hackathon timeline (~5 hours remaining). | Accepted |
| 2026-08-18 | Use `pg8000` over `psycopg2` | Pure-Python PostgreSQL wire protocol driver with zero native C extensions (`libpq`), ensuring seamless AWS Lambda packaging across all OS environments without binary compilation or custom layers. | Accepted |
| 2026-08-18 | Embed HTML in Python | Eliminates separate frontend build pipeline (Webpack/Vite), S3 asset hosting, and CloudFront CDN setup. Full single-page UI is served directly from the Lambda handler at root `/`. | Accepted |
| 2026-08-18 | Use CockroachDB Cloud Basic | Fully managed, serverless distributed SQL database providing automated high availability, enterprise-grade consistency, and native `VECTOR(1024)` indexing on free tier. | Accepted |
| 2026-08-18 | Use Lambda Function URL | Direct public HTTPS invocation without API Gateway overhead, route mapping, cold-start layers, or 29s timeout limits (supports full 15-minute Lambda timeouts). | Accepted |
| 2026-08-18 | Direct SQL over MCP for runtime | Low-latency, deterministic, connection-pooled SQL execution for agent state checkpointing and cosine-similarity vector queries during active request lifecycles. | Accepted |
| 2026-08-18 | MCP for dev/ops workflow | CockroachDB Managed Model Context Protocol (MCP) server enables AI coding agents (Cursor/VS Code) to inspect live schemas, run ad-hoc verification queries, and fulfill hackathon criteria. | Accepted |
| 2026-08-18 | 1024-dim embeddings (Titan V2) | Matches Amazon Bedrock Titan Text Embeddings V2 default dimensionality, providing optimal balance between semantic capture resolution and CockroachDB vector indexing efficiency. | Accepted |

---

## Detailed Decision Records

### ADR 001: Single-File Lambda Architecture
- **Context**: Hackathon deadline is August 19, 2026 at 02:30 AM IST. We need a reliable deployment mechanism with zero dependency packaging friction.
- **Decision**: Keep the agent runtime, API routes, SQL operations, and embedded web interface within a single `lambda_function.py`.
- **Trade-offs**: Slightly larger single source file, but eliminates module resolution bugs and simplifies zip deployment.

### ADR 002: Pure-Python Database Driver (`pg8000`)
- **Context**: AWS Lambda runs in Linux execution environments. Compiling C-based database drivers like `psycopg2` or `psycopg2-binary` often causes architecture and shared library issues when built on Windows or macOS development machines.
- **Decision**: Use `pg8000.dbapi`, a 100% pure Python PostgreSQL protocol client.
- **Trade-offs**: Slightly lower throughput under extreme synthetic loads compared to compiled C drivers, but completely portable across Windows/Linux without compilation.

### ADR 003: Embedded HTML Single Page Application
- **Context**: Demonstrating durable agent memory requires an interactive visual interface with real-time feedback for incident initiation, crash simulation, checkpoint resumption, and semantic memory search.
- **Decision**: Embed HTML/CSS/JavaScript directly as a multiline raw string in `lambda_function.py`, served on GET `/`.
- **Trade-offs**: Frontend and backend are tightly coupled in one repository, but deployment requires only one upload to AWS Lambda.

### ADR 004: CockroachDB Cloud Basic for Durable Storage & Vector Indexing
- **Context**: Agent memory requires multi-step workflow persistence (durability across process crashes) and vector similarity search for associative memory recall.
- **Decision**: Leverage CockroachDB Cloud Basic with native `VECTOR(1024)` data types and `CREATE VECTOR INDEX` for cosine distance queries (`embedding <=> %s`).
- **Trade-offs**: Requires active cloud network connection, but provides distributed transactions, horizontal scalability, and full PostgreSQL wire protocol compatibility.

### ADR 005: Lambda Function URL
- **Context**: Need a public web endpoint for testing and judging evaluation without provisioning complex API Gateways or custom domain names.
- **Decision**: Enable AWS Lambda Function URL with Auth Type `NONE` and wildcard CORS.
- **Trade-offs**: Bypasses API Gateway request throttling and custom authorizers, which is acceptable for a hackathon MVP.

### ADR 006: Direct SQL for Agent Runtime & Checkpointing
- **Context**: Agent runtime requires immediate, synchronous, transactional read/write operations during incident execution and step checkpointing.
- **Decision**: Agent code executes direct SQL statements (`pg8000`) with parameterized queries rather than routing through an external MCP layer at runtime.
- **Trade-offs**: Runtime requires standard database credentials via environment variables, but guarantees deterministic execution and minimal latency.

### ADR 007: Managed MCP Server for Developer & AI Agent Operations
- **Context**: The hackathon evaluates modern agent tooling and database observability.
- **Decision**: Configure `.cursor/mcp.json` to connect to CockroachDB's Managed MCP server, allowing developer tools and AI agents to introspect tables, inspect schemas, and run administrative SQL.
- **Trade-offs**: Requires service account API key setup, but delivers deep developer ergonomics and demonstrates next-gen database-agent integration.

### ADR 008: 1024-Dimensional Vector Embeddings via Amazon Titan V2
- **Context**: Memory entries require semantic vector representation for associative querying.
- **Decision**: Standardize on Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`) generating 1024-dimension vectors.
- **Trade-offs**: Higher dimensionality than 256/512 variants, but delivers superior retrieval precision across technical incident runbooks and architecture decisions.
