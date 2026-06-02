# Security Policy

## Reporting a vulnerability

Please report security issues privately through GitHub Security Advisories or the maintainer contact listed for the derived repository.

## Template security notes

- Never commit credentials, API keys, personal tokens, private project IDs, or production secrets.
- Treat `PROJECT_TOKEN` as sensitive and scope it to the minimum permissions required.
- Review changes under `.github/workflows/` and `scripts/` carefully because automation can affect repository and project state.
- Optional memory hooks must exclude sensitive content before enablement.
