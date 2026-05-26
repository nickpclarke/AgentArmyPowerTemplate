# local-stack secrets

This directory holds **dev-only** secrets that the compose stack mounts at
`/run/secrets/*` inside each container. `setup.sh` / `setup.ps1` generates
them automatically the first time you run the stack — you don't need to
touch this directory by hand.

The actual `*.txt` files are gitignored. Only this README and `.gitignore`
should ever be committed.

For real (non-dev) credentials, use Azure Key Vault references — see
[docs/arcadedb-secret-hardening.md](../../../docs/arcadedb-secret-hardening.md).
