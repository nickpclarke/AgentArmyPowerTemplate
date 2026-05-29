# Contract distribution — versioned OCI bundle (ARC-ADR-034)

The fleet's inter-layer contracts (OpenAPI/AsyncAPI specs, the ontology discipline box,
the fleet-interface vocabularies, shared schemas) ship as **one versioned, cosign-signed
OCI artifact** on GHCR — `ghcr.io/nickpclarke/contracts:vX.Y.Z`. Spokes **pin a version**
and codegen from it. This replaces hand-copied vendoring (the copies that drift:
`backend-core.openapi.json` duplicated into frontend-core, `agui-stream` in two spokes,
`fleet-interface/` vendored 3×). Why OCI/ORAS and not a registry/packages: see ARC-ADR-034.

## What's in the bundle
Declared in [`tools/contracts.bundle.json`](contracts.bundle.json) — the single source of
truth, mirroring the **shipped** rows of [docs/contracts.md](../docs/contracts.md). Each
artifact is gathered from **its producer repo** (hub or a sibling spoke) and staged under a
`{repo}/...` tree. Today: 23 artifacts across hub + backend-core + middle-core + frontend-core.

## Cut a release
1. Add/adjust artifacts in `tools/contracts.bundle.json`; bump `version` (semver). Merge the PR
   (the version bump is the reviewable change — drift becomes a diff, not silent rot).
2. The publish workflow (below) runs `node tools/contracts-package.mjs --publish`.
   Locally it **dry-runs** (`node tools/contracts-package.mjs`) — gather + per-file sha256 + the plan.

## Publish workflow (add as `.github/workflows/contracts-publish.yml`)
```yaml
name: contracts-publish
on:
  push: { tags: ["contracts-v*"] }      # or workflow_dispatch
permissions: { contents: read, packages: write, id-token: write }   # id-token: cosign keyless
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # the spokes must be present for the repo-aware gather (siblingRoot = ..):
      - uses: actions/checkout@v4
        with: { repository: nickpclarke/backend-core, path: ../backend-core, token: "${{ secrets.FLEET_READ_TOKEN }}" }
      - uses: actions/checkout@v4
        with: { repository: nickpclarke/middle-core,  path: ../middle-core,  token: "${{ secrets.FLEET_READ_TOKEN }}" }
      - uses: actions/checkout@v4
        with: { repository: nickpclarke/frontend-core, path: ../frontend-core, token: "${{ secrets.FLEET_READ_TOKEN }}" }
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - uses: oras-project/setup-oras@v1
        with: { version: "1.3.0" }
      - uses: sigstore/cosign-installer@v3
      - run: echo "${{ github.token }}" | oras login ghcr.io -u ${{ github.actor }} --password-stdin
      - run: node tools/contracts-package.mjs --publish
```
`FLEET_READ_TOKEN` = the ARC-ADR-034 read-only fleet token (lever #1). cosign uses keyless
GH-OIDC (no key material) via `id-token: write`.

## Consume (any spoke, identical pattern)
```bash
oras pull ghcr.io/nickpclarke/contracts:0.1.0 -o ./contracts-vendor/     # pin a version (or @sha256:… digest)
cosign verify ghcr.io/nickpclarke/contracts:0.1.0 \
  --certificate-identity-regexp '.*' --certificate-oidc-issuer https://token.actions.githubusercontent.com
# then codegen from local files, e.g.:
#   TS:     npx openapi-typescript ./contracts-vendor/backend-core/contracts/backend-core.openapi.json -o src/api.d.ts
#   Python: datamodel-codegen --input ./contracts-vendor/backend-core/contracts/backend-core.openapi.json ...
#   .NET:   the F# projections (ARC-ADR-033) read ./contracts-vendor/<repo>/...
```
Pin the version as a literal in the spoke's workflow/lockfile — bumping it is a reviewable PR.

## Heartbeat (follow-on)
`tools/fleet-heartbeat.mjs`'s vendoring check flips from "is this copy stale?" to "is the
spoke pinned to the latest `contracts` tag?" once spokes declare a pin (e.g. a
`contracts.version` file). Until then the copies remain; the bundle is additive.
