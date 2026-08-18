# 3-minute demo

1. Open the app and click **Start Incident**.
2. Explain that workflow state and step checkpoints are written to CockroachDB.
3. Click **Simulate Worker Crash**.
4. Show the status `INTERRUPTED` and explain that checkpoint 2 is durable.
5. Click **Resume from Checkpoint**.
6. Show the workflow moving to `COMPLETED`.
7. Explain that the new worker did not need the old runtime memory; it reconstructed state from CockroachDB.
8. Point at the Memory Trace and highlight `incident-208`.
9. Explain that the validated lesson supersedes an older pool-size recommendation.
10. Click **Ask Agent** with: `Why is checkout latency high and what should we do?`
11. Show that the answer is based on semantic retrieval from the CockroachDB vector index.
12. In your code walkthrough, show `schema.sql`, `CREATE VECTOR INDEX`, and `.cursor/mcp.json`.
