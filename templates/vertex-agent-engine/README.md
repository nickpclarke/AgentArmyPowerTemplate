# Vertex AI Agent Engine Adapter

This is a placeholder for the future AgentArmy lifecycle adapter for Vertex AI Agent Engine workloads.

Do not treat this adapter as production-ready yet. Before a spoke uses this target, add:

- packaging rules for the agent runtime
- cloud build/deploy workflow or script
- required environment variables and secrets
- smoke and evaluation checks
- rollback or revision strategy

Until then, use the lifecycle promotion manifest to reserve the target name:

```json
{
  "cloud": "gcp",
  "build": "cloud-build",
  "runtime": "vertex-ai-agent-engine"
}
```
