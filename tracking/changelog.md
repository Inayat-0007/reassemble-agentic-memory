# Changelog

All notable changes to the REASSEMBLE project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-18

### Added
- Initial Lambda handler with embedded HTML frontend
- CockroachDB schema (4 tables: `memories`, `workflows`, `workflow_steps`, `audit_log`)
- Vector index on `memories` table (`VECTOR(1024)`)
- Amazon Bedrock integration (Nova Lite for reasoning, Titan V2 for embeddings)
- Semantic memory retrieval using cosine distance
- Workflow checkpointing system (4-step incident investigation)
- Simulated worker crash and recovery flow
- Memory supersession (validated lessons replace stale advice)
- Audit logging for all workflow events
- Browser UI with demo controls
- CockroachDB MCP configuration example
- MIT license
- Demo script
