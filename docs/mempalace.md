# Optional MemPalace

MemPalace can provide cross-session memory for local AI assistants, but it is not enabled by default in this template.

Before enabling memory hooks, decide:

- What content may be persisted.
- Where memory files are stored.
- Whether memories are committed, ignored, or private.
- How sensitive information is excluded.

Teams that opt in can wire `scripts/mempalace_hook.py` into their local assistant settings after reviewing policy requirements.
