# Local secrets (gitignored)

This directory holds local secret files for the example compose stack. **Never
commit real secrets.** Add `**/.secrets/` to your spoke's `.gitignore` (this repo
already ignores it via the template `.dockerignore`, but `.gitignore` is what
keeps it out of git).

Create two files before running the example:

```bash
printf 'change-me-root'   > arcadedb_root_password.txt
printf 'change-me-reader' > arcadedb_password.txt
```

- `arcadedb_root_password.txt` → ArcadeDB `root` (admin; used only for bootstrap).
- `arcadedb_password.txt`      → `platform_reader` (read-only) — the same file the
  doctor and cockpit read via `ARCADEDB_PASSWORD_FILE`.

Avoid the characters `:` `[` `]` `{` `}` in the service password — they are
delimiters in ArcadeDB's `defaultDatabases` setting.
