#!/usr/bin/env node
// contracts-package — package the fleet's contract artifacts (ARC-ADR-034) as a versioned,
// cosign-signed OCI artifact pushed to GHCR via ORAS. The standard way to ship non-image
// versioned artifacts; it REPLACES hand-copied vendoring + the always-firing drift check.
//
// Each artifact is gathered FROM ITS PRODUCER repo (hub or a sibling spoke checkout), staged
// under a {repo}/... tree, and pushed as one bundle. The single source of truth for what
// spokes pin + codegen from = tools/contracts.bundle.json (mirrors docs/contracts.md 'shipped').
//
//   node tools/contracts-package.mjs                  # DRY-RUN: gather + per-file sha256 + the oras plan
//   node tools/contracts-package.mjs --publish        # stage -> oras push ghcr.io/.../contracts:vX.Y.Z -> cosign sign
//   node tools/contracts-package.mjs --version 0.2.0  # override the manifest version
//
// Publish needs `oras` + `cosign` on PATH and a registry login (CI: `oras login ghcr.io -u
// <actor> -p $GITHUB_TOKEN`; cosign keyless via GH-OIDC), and the sibling spokes present
// (CI checks them out, or uses the ARC-ADR-034 read token). Locally it dry-runs. See
// tools/CONTRACTS-DISTRIBUTION.md.
import { readFileSync, writeFileSync, existsSync, mkdirSync, copyFileSync, rmSync } from "node:fs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST = path.join(REPO, "tools", "contracts.bundle.json");
const C = { reset: "\x1b[0m", dim: "\x1b[2m", green: "\x1b[32m", yellow: "\x1b[33m", red: "\x1b[31m", cyan: "\x1b[36m" };
const log = (s = "") => process.stdout.write(s + "\n");
const die = (s) => { log(`${C.red}✗ ${s}${C.reset}`); process.exit(1); };

const apply = process.argv.includes("--publish");
const vi = process.argv.indexOf("--version");
const verArg = vi > -1 ? process.argv[vi + 1] : null;

if (!existsSync(MANIFEST)) die(`no manifest at ${MANIFEST}`);
const m = JSON.parse(readFileSync(MANIFEST, "utf8"));
const version = verArg || m.version;
if (!version || !m.registry) die("manifest needs registry + version (or pass --version)");
const ref = `${m.registry}:${version}`;
const siblingRoot = path.resolve(REPO, m.siblingRoot || "..");
const repoDir = (repo) => (repo === "hub" || !repo ? REPO : path.join(siblingRoot, repo));

const resolved = [];
const missing = [];
for (const a of m.artifacts || []) {
  const abs = path.join(repoDir(a.repo), a.path);
  const staged = `${a.repo || "hub"}/${a.path}`;
  if (!existsSync(abs)) { missing.push({ ...a, abs, staged }); continue; }
  if (!a.mediaType) die(`artifact ${staged} has no mediaType`);
  const buf = readFileSync(abs);
  resolved.push({ ...a, abs, staged, sha256: createHash("sha256").update(buf).digest("hex"), bytes: buf.length });
}

log(`${C.cyan}contracts-package${C.reset} ${apply ? C.yellow + "(PUBLISH)" + C.reset : C.dim + "(dry-run — --publish to push)" + C.reset}`);
log(`  bundle: ${ref}   ${resolved.length} artifact(s) from ${new Set(resolved.map((r) => r.repo)).size} repo(s)`);
let lastRepo = "";
for (const r of resolved) {
  if (r.repo !== lastRepo) { log(`  ${C.cyan}${r.repo}${C.reset}`); lastRepo = r.repo; }
  log(`    ${r.mediaType.padEnd(38)} ${r.path}  ${C.dim}(${r.bytes}b sha256:${r.sha256.slice(0, 12)}…)${C.reset}`);
}
if (missing.length) {
  log(`  ${C.yellow}not found (spoke not checked out at ${siblingRoot}, or path moved):${C.reset}`);
  for (const x of missing) log(`    ${C.yellow}- ${x.repo}/${x.path}${C.reset}`);
}

if (!apply) {
  log(`\n${C.dim}→ would stage ${resolved.length} files under {repo}/… and: oras push ${ref} --artifact-type ${m.artifactType} <files> ; cosign sign${C.reset}`);
  if (missing.length) log(`${C.yellow}dry-run: ${missing.length} artifact(s) unresolved — check them out / run in CI before --publish.${C.reset}`);
  log(`${C.dim}dry-run — nothing pushed.${C.reset}`);
  process.exit(0);
}

if (missing.length) die(`refusing to publish a partial bundle — ${missing.length} artifact(s) unresolved (check out the spokes / run in CI).`);

// stage under a temp tree so OCI layer titles are clean {repo}/path, then push from there.
const stage = path.join(REPO, "tmp", `contracts-stage-${version}`);
rmSync(stage, { recursive: true, force: true });
const fileArgs = [];
for (const r of resolved) {
  const dest = path.join(stage, r.staged);
  mkdirSync(path.dirname(dest), { recursive: true });
  copyFileSync(r.abs, dest);
  fileArgs.push(`${r.staged}:${r.mediaType}`);
}
writeFileSync(path.join(stage, "bundle.manifest.json"), JSON.stringify(
  { version, artifactType: m.artifactType, artifacts: resolved.map((r) => ({ repo: r.repo, path: r.path, mediaType: r.mediaType, sha256: r.sha256 })) }, null, 2));
fileArgs.push("bundle.manifest.json:application/json");

let out = "";
try {
  out = execFileSync("oras", ["push", ref, ...(m.artifactType ? ["--artifact-type", m.artifactType] : []), ...fileArgs], { cwd: stage, encoding: "utf8" });
  process.stdout.write(out);
} catch (e) { die(`oras push failed (oras installed + logged in to ${m.registry.split("/")[0]}?): ${e.message}`); }
const digest = (out.match(/Digest:\s*(sha256:[0-9a-f]+)/) || [])[1];
try {
  execFileSync("cosign", ["sign", "--yes", digest ? `${m.registry}@${digest}` : ref], { stdio: "inherit" });
} catch (e) { die(`cosign sign failed: ${e.message}`); }
rmSync(stage, { recursive: true, force: true });
log(`${C.green}✓ published + signed ${ref}${digest ? "  (" + digest + ")" : ""}${C.reset}`);
log(`${C.dim}consumers pin: oras pull ${m.registry}@${digest || "<digest>"}${C.reset}`);
