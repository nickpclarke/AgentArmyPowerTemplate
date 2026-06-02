# Agent Synchronization

In AgentArmyPowerTemplate, all three armies (Claude Code, Codex, and Antigravity/Gemini) read from **the exact same agent definitions** located in `.claude/agents/categories/`.

To support different runtimes and platforms, these source definitions are compiled and synchronized across your environment.

## The Synchronization Cycle

```
      [.claude/agents/categories/]  <--- (Source of Truth)
                   │
         ┌─────────┼─────────┐
         ▼         ▼         ▼
    Claude Code  Codex  Antigravity
     (Native)    (.toml)   (Plugins)
```

1. **Source of Truth**: All edits are made directly to the markdown files in `.claude/agents/categories/`.
2. **Claude Code Native**: Claude Code reads these markdown files directly at runtime.
3. **Codex Synchronization**: Compiles source markdown files into Codex-compatible TOML definitions in `.codex/agents/`.
4. **Antigravity Synchronization**: Generates native plugin directories and `plugin.json` manifests in `.agents/plugins/`.

---

## Synchronization Commands

You can run the full compilation cycle locally using the synchronization script:

```bash
# Run full sync cycle (Codex TOML + Antigravity Plugins)
python scripts/sync_agents_to_codex.py
python scripts/sync_agents_to_antigravity.py
```

### Automation (Hooks)

The template includes a local Codex post-sync hook in `.codex/hooks.json` to keep things updated automatically during active coding sessions:

```json
{
  "post-sync": "python scripts/sync_agents_to_codex.py"
}
```
