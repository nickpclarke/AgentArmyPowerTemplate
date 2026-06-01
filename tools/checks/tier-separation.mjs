// tier-separation.mjs — executable ARC-ADR-023 cross-tier-bundling check.
//
// The rule (ARC-ADR-023 "Container Tiering Strategy"): an Application- or
// Function-tier spoke must NOT bundle or run Platform-tier infrastructure
// (databases, brokers, triple stores) locally. It consumes the running platform
// instances via environment variables (ARCADEDB_URL, NATS_URL, FUSEKI_URL,
// DATABASE_URL, …). Platform infra is hub-owned and lives ONLY under
// templates/local-stack/ and templates/*-image/ — the `$ownership_note` in
// scripts/spoke_sync.config.json codifies exactly this ("spokes consume the
// running instances via env, not by vendoring the Dockerfile").
//
// ADR-023 §Implementation flags this checker as future work ("the fleet-heartbeat
// should warn on cross-tier bundling"). The heartbeat already inventories
// image.json manifests by tier, but few manifests exist yet — the real leak
// vector is a spoke wiring a Platform DB straight into a docker-compose or
// Dockerfile. This module closes that gap.
//
// The core (scanTierSeparation) is PURE over [{ path, content }] so it can be
// driven two ways with no shelling out:
//   • the fleet heartbeat feeds it files fetched remotely (gh raw content), and
//   • the fleet_check_tiers MCP tool feeds it files read from a local checkout.

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, relative, sep, resolve } from "node:path";

// Platform-tier service markers — image refs / base images / compose service
// images that indicate a Platform-tier dependency is being *bundled* rather than
// *consumed via env*. Deliberately conservative (anchored to image-ish tokens)
// to avoid flagging an `*_URL` env reference, which is the correct pattern.
export const PLATFORM_MARKERS = [
  { name: "ArcadeDB",    env: "ARCADEDB_URL", re: /arcadedb/i },
  { name: "PostgreSQL",  env: "DATABASE_URL", re: /\b(?:postgres(?:ql)?|postgis|pgvector)\b/i },
  { name: "NATS",        env: "NATS_URL",     re: /(?:^|[/"'\s:])nats(?:-server|io)?(?:[:"'\s]|$)/i },
  { name: "Fuseki/Jena", env: "FUSEKI_URL",   re: /\b(?:fuseki|jena)\b/i },
  { name: "Neo4j",       env: "NEO4J_URL",    re: /\bneo4j\b/i },
  { name: "Redis",       env: "REDIS_URL",    re: /(?:^|[/"'\s:])redis(?:[:"'\s]|$)/i },
];

// Paths where Platform infra is LEGITIMATELY defined (hub-owned). Never flagged.
export const ALLOWED_PLATFORM_PATHS = [
  /(?:^|\/)templates\/local-stack\//,
  /(?:^|\/)templates\/[^/]+-image\//,
];

// Test fixtures / harnesses are not runtime infra: an intentionally-"bad" example
// or an integration test that spins up a real DB is NOT a tier violation. The rule
// is about a spoke's *deployable* compose/Dockerfile, so skip test paths entirely.
export const TEST_PATH_PATTERNS = [
  /(?:^|\/)(?:fixtures?|__fixtures__|__tests__|tests?|spec|e2e)\//i,
];

export const isComposeFile = (p) =>
  /(?:^|\/)(?:docker-)?compose(?:[.-][\w.-]+)?\.ya?ml$/i.test(p);

export const isDockerfile = (p) =>
  /(?:^|\/)Dockerfile(?:\.[\w.-]+)?$/.test(p) || /\.dockerfile$/i.test(p);

// Find the first line that BUNDLES a platform marker — an `image:` value in a
// compose file, or a `FROM` base image in a Dockerfile. Crucially this inspects
// only image/FROM references, NOT env vars: `ARCADEDB_URL=${ARCADEDB_URL}` is the
// *correct* consume-via-env pattern and must never be flagged. Comment lines are
// skipped. Returns { line, text, marker } (1-indexed) or null.
const findBundledPlatform = (content, { compose }) => {
  const lines = content.split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const trimmed = raw.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    let value = null;
    if (compose) {
      const m = /^\s*image:\s*["']?([^"'#]+)/i.exec(raw);
      if (m) value = m[1].trim();
    } else {
      const m = /^\s*FROM\s+(?:--platform=\S+\s+)?(\S+)/i.exec(raw);
      if (m) value = m[1];
    }
    if (!value) continue;
    for (const marker of PLATFORM_MARKERS) {
      if (marker.re.test(value)) return { line: i + 1, text: trimmed.slice(0, 200), marker };
    }
  }
  return null;
};

/**
 * Pure core. Scan compose/Dockerfile entries for bundled Platform-tier infra.
 *
 * @param {object} args
 * @param {{path:string, content:string}[]} args.files  Candidate files (any non
 *   compose/Dockerfile path is ignored). `content` may be "" for an unreadable
 *   file — it is skipped, not counted as scanned.
 * @param {string|null} [args.repo]   Repo name, echoed back in the result.
 * @param {boolean} [args.isHub]      The hub legitimately defines platform infra,
 *   so isHub:true short-circuits to ok with nothing scanned.
 * @returns {{ok:boolean, repo:string|null, scanned:number,
 *   violations:{path:string, kind:string, marker:string, line:number, detail:string}[]}}
 */
export function scanTierSeparation({ files, repo = null, isHub = false }) {
  const violations = [];
  let scanned = 0;
  if (isHub) return { ok: true, repo, scanned, violations };
  for (const { path: p, content } of files || []) {
    const compose = isComposeFile(p);
    const docker = isDockerfile(p);
    if (!compose && !docker) continue;
    if (ALLOWED_PLATFORM_PATHS.some((re) => re.test(p))) continue;
    if (TEST_PATH_PATTERNS.some((re) => re.test(p))) continue;
    if (typeof content !== "string" || !content) continue;
    scanned++;
    const hit = findBundledPlatform(content, { compose });
    if (hit) {
      violations.push({
        path: p,
        kind: compose ? "compose-platform-service" : "dockerfile-platform-base",
        marker: hit.marker.name,
        line: hit.line,
        detail:
          `${p}:${hit.line} bundles Platform-tier "${hit.marker.name}" (\`${hit.text}\`) — ` +
          `an Application/Function spoke must consume it via ${hit.marker.env} (ARC-ADR-023), not run it locally.`,
      });
    }
  }
  return { ok: violations.length === 0, repo, scanned, violations };
}

// --- local-filesystem convenience (used by the fleet_check_tiers MCP tool) ---

const SKIP_DIRS = new Set([
  "node_modules", ".git", ".venv", "venv", "dist", "build", ".next",
  "__pycache__", ".claude", ".codex", ".agents", "target",
  // test infra is not runtime infra (see TEST_PATH_PATTERNS)
  "tests", "test", "fixtures", "__tests__", "spec", "e2e",
]);

const collectLocalFiles = (rootDir) => {
  const out = [];
  const walk = (dir) => {
    let entries;
    try { entries = readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (e.isDirectory()) {
        if (!SKIP_DIRS.has(e.name)) walk(join(dir, e.name));
        continue;
      }
      if (!e.isFile()) continue;
      const abs = join(dir, e.name);
      const rel = relative(rootDir, abs).split(sep).join("/");
      if (isComposeFile(rel) || isDockerfile(rel)) {
        try { out.push({ path: rel, content: readFileSync(abs, "utf8") }); }
        catch { /* unreadable — skip */ }
      }
    }
  };
  walk(rootDir);
  return out;
};

// The hub is the checkout that defines the platform stack.
export const looksLikeHub = (rootDir) =>
  existsSync(join(rootDir, "templates", "local-stack", "docker-compose.yml"));

/**
 * Scan a local checkout directory. Walks for compose/Dockerfiles and runs the
 * pure core. isHub is auto-detected from the platform-stack signature unless set.
 */
export function checkRepoDir(rootDir, { repo = null, isHub = null } = {}) {
  const root = resolve(rootDir);
  const hub = isHub == null ? looksLikeHub(root) : isHub;
  const files = collectLocalFiles(root);
  return { ...scanTierSeparation({ files, repo, isHub: hub }), isHub: hub, root };
}
