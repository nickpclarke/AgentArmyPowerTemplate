#!/usr/bin/env node
// fleet-heartbeat.mjs — AgentArmy fleet "heartbeat": one script that inventories
// contracts, detects drift, checks fleet health, and dispatches the gaps.
//
// Per-artifact authority (the safe-bidirectional rule — never blind two-way overwrite):
//   • hub-owned   → .claude/agents, .claude/skills, docs/decisions, docs/contracts.md  (push hub→spokes)
//   • spoke-owned → each spoke's own contracts (BFF, MCR-F4 projection, …)            (reflect spoke→hub registry)
//   • gaps/drift  → dispatched as labelled issues; the two armies execute.
//
// Scope: READ + `gh` only. No web. No Postman publish (needs local Key Vault creds — flagged, not done).
// Security: uses execFileSync (array args, NO shell) — no string-interpolated commands.
//
// Usage:
//   node tools/fleet-heartbeat.mjs            # dry-run: report only (default)
//   node tools/fleet-heartbeat.mjs --apply    # file a dedup'd issue per gap as agent-army-task (no auto-spawn)
//   node tools/fleet-heartbeat.mjs --apply --auto  # gaps as copilot-task → Copilot coding agent auto-spawns
//   node tools/fleet-heartbeat.mjs --json      # machine-readable findings
//   node tools/fleet-heartbeat.mjs --dora      # add DORA metrics block (deploy freq / lead time / CFR / MTTR)
//   node tools/fleet-heartbeat.mjs --slo       # probe known live services' health endpoints + warn on non-2xx
//   node tools/fleet-heartbeat.mjs --secrets   # check KV secret ages against the rotation policy + warn on stale
//   node tools/fleet-heartbeat.mjs --disk      # warn when host free disk < 5 GB (override: AGENTARMY_DISK_MIN_FREE_GB)

import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync, statfsSync } from 'node:fs';

const OWNER = 'nickpclarke';
const HUB = 'AgentArmy';
const SPOKES = ['frontend-core', 'backend-core', 'middle-core'];
const APPLY = process.argv.includes('--apply');
const AUTO = process.argv.includes('--auto');
const JSON_OUT = process.argv.includes('--json');

// Hard gaps route to Copilot (auto-execute) only with --auto; otherwise they file as
// agent-army-task so an unattended/daily --apply run never spawns a Copilot worker swarm.
const GAP_LABEL = AUTO ? 'copilot-task' : 'agent-army-task';

// execFile (no shell) — args are passed literally, so no command injection.
const gh = (args) => {
  try { return execFileSync('gh', args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); }
  catch { return ''; }
};
// Tree fetch can hiccup in the cloud-routine context (transient gh-api error,
// rate-limit, etc.). Distinguish "tree fetch failed" from "tree is genuinely
// empty" so file-based gap checks don't fire as false positives (real-world
// fire: AgentArmy #207, 2026-05-26 cron run — all 3 PR workflows reported
// missing on a healthy repo because the tree call returned empty).
const MIN_TREE_FILES = 10; // any real repo has more files than this
const treePaths = (repo) => {
  for (let attempt = 0; attempt < 2; attempt++) {
    const o = gh(['api', `repos/${OWNER}/${repo}/git/trees/main?recursive=1`, '--jq', '.tree[].path']);
    if (o) {
      const paths = o.split('\n');
      if (paths.length >= MIN_TREE_FILES) return paths;
    }
  }
  return null; // distinct from [] — signals the tree fetch failed
};
const isContract = (p) => /\.(openapi|asyncapi)\.(json|ya?ml)$/.test(p);
const isImageManifest = (p) => p === 'image.json' || p.endsWith('/image.json');

// Fetch a file's raw content from a repo at main. Returns null if missing or unreadable.
// Uses the GitHub raw-content endpoint — one API call per file, no base64 decode.
const fetchFile = (repo, path) => {
  const raw = gh(['api', `repos/${OWNER}/${repo}/contents/${path}?ref=main`,
    '-H', 'Accept: application/vnd.github.raw']);
  return raw || null;
};

const findings = [];
const add = (repo, severity, kind, detail, label = 'agent-army-task') => findings.push({ repo, severity, kind, detail, label });

// ---- 1. Contract inventory + registry coverage -----------------------------
const registry = existsSync('docs/contracts.md') ? readFileSync('docs/contracts.md', 'utf8') : '';
const repoTrees = Object.fromEntries([HUB, ...SPOKES].map((r) => [r, treePaths(r)]));

// Tree-fetch failures → emit a warn AND skip dispatch decisions for these repos
// this cycle (a missing tree would false-positive every file-based gap).
const treeFetchFailed = new Set(
  Object.entries(repoTrees).filter(([, v]) => v === null).map(([k]) => k),
);
for (const repo of treeFetchFailed) {
  add(repo, 'warn', 'tree-fetch-failed',
    `gh api git/trees/main returned empty/failed after a retry (transient hiccup likely); file-based dispatch checks skipped for this cycle.`);
}
// Safe-empty fallback for warn-only iterators that don't dispatch.
const safeTree = (repo) => repoTrees[repo] || [];

for (const spoke of SPOKES) {
  for (const c of safeTree(spoke).filter(isContract)) {
    const base = c.split('/').pop();
    if (registry && !registry.includes(base)) {
      add(HUB, 'warn', 'unregistered-contract',
        `${spoke}/${c} is not registered in docs/contracts.md — add it (producer/consumers/status/ADR).`);
    }
  }
}

// backend OpenAPI must be vendored into its consumers (fe + mc). Skip the spoke
// if its tree fetch failed (don't dispatch on a phantom-empty tree).
for (const spoke of ['frontend-core', 'middle-core']) {
  if (treeFetchFailed.has(spoke)) continue;
  const ok = repoTrees[spoke].some((p) => p.endsWith('backend-core.openapi.json'));
  if (!ok) add(spoke, 'gap', 'unvendored-contract',
    `backend-core OpenAPI is not vendored in ${spoke} — vendor it + generate the client.`, GAP_LABEL);
}

const postmanNote = SPOKES.flatMap((s) => safeTree(s).filter(isContract)).length
  ? 'Verify each contract has a published Postman spec + mock (run locally with Key Vault creds — not checkable from the heartbeat).'
  : null;

// ---- 2. Agent / skills pack drift (hub-authoritative, one-way hub→spoke) ----
const hubAgents = safeTree(HUB).filter((p) => p.startsWith('.claude/agents/') && p.endsWith('.md'));
for (const spoke of SPOKES) {
  const spokeAgents = safeTree(spoke).filter((p) => p.startsWith('.claude/agents/') && p.endsWith('.md'));
  if (hubAgents.length && spokeAgents.length < Math.floor(hubAgents.length * 0.5)) {
    add(spoke, 'warn', 'agent-pack-drift',
      `agent pack out of sync: hub has ${hubAgents.length} agent files, ${spoke} has ${spokeAgents.length}. Re-run the hub→spoke sync.`);
  }
}

// ---- 2b. PR-event subscriptions (PRs are the webhook surface) --------------
// PRs are event-driven: each repo must keep its pull_request-triggered automation
// wired. Issues are cron/poll-driven (this heartbeat + the /loop mind); PRs ride
// the GitHub webhook → the review/loop/@claude workflows. Enforce as a rule.
const EXPECTED_PR_WORKFLOWS = ['copilot-review.yml', 'review-loop.yml', 'claude.yml'];
for (const repo of [HUB, ...SPOKES]) {
  if (treeFetchFailed.has(repo)) continue; // don't dispatch on a phantom-empty tree
  const wf = repoTrees[repo].filter((p) => p.startsWith('.github/workflows/'));
  const missing = EXPECTED_PR_WORKFLOWS.filter((w) => !wf.some((p) => p.endsWith('/' + w)));
  if (missing.length) {
    add(repo, 'gap', 'pr-subscription-missing',
      `${repo} is not fully subscribed to PR events — missing ${missing.join(', ')}. Wire the pull_request-triggered workflow(s) so PRs get review / review-loop / @claude.`,
      GAP_LABEL);
  }
}

// ---- 2c. Container inventory by tier (ARC-ADR-023) -------------------------
// Enumerate every image.json across hub+spokes, read its tier, and group the
// fleet's containers by Platform / Application / Function. Drift detection:
// (a) image.json missing the `tier` field (ADR-023 says new manifests should
// declare it); (b) `kind: "multi-service"` is a likely anti-pattern in the
// new tiering model ("fusion images" are retired — Platform DBs shouldn't be
// bundled into an Application image.json).
const containers = { platform: [], application: [], function: [], untiered: [] };
for (const repo of [HUB, ...SPOKES]) {
  for (const path of safeTree(repo).filter(isImageManifest)) {
    const raw = fetchFile(repo, path);
    if (!raw) continue;
    let manifest;
    try { manifest = JSON.parse(raw); } catch {
      add(repo, 'warn', 'image-manifest-unparseable',
        `${repo}/${path} could not be parsed as JSON — fix the manifest.`);
      continue;
    }
    const entry = {
      repo, path,
      name: manifest.name || '(unnamed)',
      kind: manifest.kind || '(no kind)',
      tier: manifest.tier || null,
      doctor: manifest.doctor?.proves ? manifest.doctor.proves.join(', ') : '—',
      deploy: manifest.deploy?.target || '—',
    };
    if (entry.tier && containers[entry.tier]) containers[entry.tier].push(entry);
    else containers.untiered.push(entry);
    if (!entry.tier) {
      add(repo, 'warn', 'image-missing-tier',
        `${repo}/${path} ("${entry.name}") declares no \`tier\` — add tier: platform | application | function per ARC-ADR-023.`);
    }
    if (entry.kind === 'multi-service' && entry.tier === 'application') {
      add(repo, 'warn', 'tier-bundle-antipattern',
        `${repo}/${path} ("${entry.name}") is tier=application but kind=multi-service — likely bundles Platform DBs into an app image. ADR-023 retires this 'fusion image' pattern; split into image.json (app only) + a separate stack file referencing templates/local-stack.`);
    }
  }
}

// ---- 2d. Contract version skew (ARC-ADR-024 / release-manager finding) ----
// When backend-core.openapi.json bumps its info.version, consumers must vendor
// the new spec or risk runtime breakage. Compare the producer's info.version
// against each consumer's vendored copy and warn on mismatch. Today we only
// implement this for backend-core.openapi.json (the highest-leverage contract);
// extend the producers list as more shared contracts get version-stamped.
const PRODUCER_CONTRACTS = [
  { producerRepo: 'backend-core', producerPath: 'contracts/backend-core.openapi.json',
    consumers: ['frontend-core', 'middle-core'] },
];
const readVersion = (raw) => {
  if (!raw) return null;
  try {
    if (raw.trim().startsWith('{')) return JSON.parse(raw)?.info?.version || null;
    // YAML — naive grep for `version: x.y.z` under `info:` (good enough for OpenAPI)
    const m = raw.match(/^info:\s*[\s\S]*?\n\s+version:\s+["']?([^"'\s]+)/m);
    return m ? m[1] : null;
  } catch { return null; }
};
for (const c of PRODUCER_CONTRACTS) {
  if (treeFetchFailed.has(c.producerRepo)) continue;
  const producerRaw = fetchFile(c.producerRepo, c.producerPath);
  const producerVer = readVersion(producerRaw);
  if (!producerVer) continue;
  for (const cons of c.consumers) {
    if (treeFetchFailed.has(cons)) continue;
    const consPath = safeTree(cons).find((p) => p.endsWith(c.producerPath.split('/').pop()));
    if (!consPath) continue; // unvendored — already caught by the contract-vendoring check
    const consVer = readVersion(fetchFile(cons, consPath));
    if (consVer && consVer !== producerVer) {
      add(cons, 'warn', 'contract-version-skew',
        `${cons} vendors ${consPath} at v${consVer}; producer ${c.producerRepo} is at v${producerVer} — run the contract-consumer-update playbook (ADR-024 finding 4 / ADR-005).`);
    }
  }
}

// ---- 2e. OTel readiness (ARC-ADR-024 / observability-engineer finding) ----
// ADR-010 says traces should originate at frontend-core's BFF and propagate
// through middle-core → backend-core. Detect SDK init presence per spoke.
const OTEL_HEURISTIC = {
  'frontend-core': ['instrumentation.ts', 'instrumentation.js', 'src/instrumentation.ts'],
  'backend-core': ['app/otel_setup.py', 'otel_setup.py', 'app/instrumentation.py'],
  'middle-core': ['otel_setup.py', 'src/instrumentation.rs', 'agent_runtime/otel_setup.py'],
};
for (const [spoke, candidates] of Object.entries(OTEL_HEURISTIC)) {
  if (treeFetchFailed.has(spoke)) continue;
  const has = candidates.some((c) => safeTree(spoke).some((p) => p.endsWith(c)));
  if (!has) {
    add(spoke, 'warn', 'otel-not-initialized',
      `${spoke} has no OpenTelemetry SDK init file (looked for: ${candidates.join(', ')}). Per ADR-010 + ADR-024, every spoke originates/propagates traceparent — wire OTel SDK + emit traces.`);
  }
}

// ---- 2f. Secrets staleness (ADR-024 + docs/security/secrets-rotation.md) ----
// Reads Key Vault secret `updated` timestamps via `az` and warns when any
// exceeds its rotation cadence + a 14-day grace window. Off by default
// (`--secrets`) because it requires az login + KV read perms; daily heartbeat
// runs in the cloud routine don't have that context.
const SECRETS_PROBE = process.argv.includes('--secrets');
// Cadence in days, per docs/security/secrets-rotation.md.
const SECRETS_POLICY = [
  { name: 'JWT_SIGNING_KEY', cadenceDays: 90 },
  { name: 'OPENAI_API_KEY', cadenceDays: 180 },
  { name: 'ANTHROPIC_API_KEY', cadenceDays: 180 },
  { name: 'ARCADEDB_ROOT_PASSWORD', cadenceDays: 180 },
  { name: 'ARCADEDB_PASSWORD', cadenceDays: 180 },
  { name: 'POSTGRES_PASSWORD', cadenceDays: 180 },
  { name: 'PROJECT_TOKEN', cadenceDays: 90 },
  { name: 'GHRUNNERPAT', cadenceDays: 90 },
  { name: 'GITHUB_WEBHOOK_SECRET', cadenceDays: 180 },
];
const GRACE_DAYS = 14;
const secretsState = [];
if (SECRETS_PROBE) {
  const KV = process.env.AGENTARMY_KV || 'akv01-agentarmy';
  const nowMs = Date.now();
  for (const s of SECRETS_POLICY) {
    let updatedIso = '';
    try {
      updatedIso = execFileSync('az',
        ['keyvault', 'secret', 'show', '--vault-name', KV, '--name', s.name,
         '--query', 'attributes.updated', '-o', 'tsv'],
        { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }
      ).trim();
    } catch { /* missing/inaccessible — surface as warn */ }
    if (!updatedIso) {
      secretsState.push({ name: s.name, status: 'missing', cadenceDays: s.cadenceDays });
      add(HUB, 'warn', 'secret-not-found',
        `KV secret ${s.name} not present in ${KV} (or no read perm). docs/security/secrets-rotation.md expects it.`);
      continue;
    }
    const ageDays = Math.floor((nowMs - new Date(updatedIso).getTime()) / 86400000);
    const stale = ageDays > s.cadenceDays;
    const overdueGrace = ageDays > s.cadenceDays + GRACE_DAYS;
    secretsState.push({ name: s.name, ageDays, cadenceDays: s.cadenceDays, stale, overdueGrace });
    if (overdueGrace) {
      add(HUB, 'warn', 'secret-stale',
        `KV secret ${s.name} age=${ageDays}d exceeds cadence ${s.cadenceDays}d + ${GRACE_DAYS}d grace. Rotate per docs/security/secrets-rotation.md.`);
    }
  }
}

// ---- 3. Fleet health + issue queue (the "subscribe to every open issue" surface)
const health = {};
const parseIssues = (raw) => { try { return JSON.parse(raw || '[]'); } catch { return []; } };
for (const repo of [HUB, ...SPOKES]) {
  const openPRs = Number(gh(['pr', 'list', '--repo', `${OWNER}/${repo}`, '--state', 'open', '--json', 'number', '--jq', 'length']) || '0');
  const recentFailedRuns = Number(gh(['run', 'list', '--repo', `${OWNER}/${repo}`, '--limit', '8', '--json', 'conclusion', '--jq', '[.[] | select(.conclusion=="failure")] | length']) || '0');
  const openIssues = Number(gh(['issue', 'list', '--repo', `${OWNER}/${repo}`, '--state', 'open', '--json', 'number', '--jq', 'length']) || '0');
  const armyTask = parseIssues(gh(['issue', 'list', '--repo', `${OWNER}/${repo}`, '--state', 'open', '--label', 'agent-army-task', '--limit', '50', '--json', 'number,title']));
  const copilotTask = parseIssues(gh(['issue', 'list', '--repo', `${OWNER}/${repo}`, '--state', 'open', '--label', 'copilot-task', '--limit', '50', '--json', 'number,title']));
  health[repo] = { openPRs, openIssues, recentFailedRuns, armyTask, copilotTask };
}

// ---- 3b. DORA metrics (ARC-ADR-024 / platform-architect finding) ----------
// Four DORA metrics, computed from GH Actions data only — no external service:
//   • Deployment Frequency = successful runs of the deploy workflow / period
//   • Lead Time for Changes ≈ PR open → merge median (proxy: merge ≈ deploy)
//   • Change Failure Rate  = failed deploy-workflow runs / total deploy runs
//   • MTTR (approx)        = elapsed between a failed deploy run and the
//                            next successful one on the same workflow
// Window: last 30 days. Off by default; emit only when --dora is set so
// daily heartbeats don't fan out N more `gh run list` calls than needed.
const DORA = process.argv.includes('--dora');
const DEPLOY_WORKFLOWS = ['arcadedb-aca-deploy.yml']; // extend per repo as deploy lanes land
const doraMetrics = {};
if (DORA) {
  const sinceISO = new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString();
  for (const repo of [HUB, ...SPOKES]) {
    if (treeFetchFailed.has(repo)) continue;
    const wfs = safeTree(repo).filter((p) => p.startsWith('.github/workflows/') && DEPLOY_WORKFLOWS.some((w) => p.endsWith('/' + w)));
    if (!wfs.length) continue;
    const wf = wfs[0].split('/').pop();
    // Recent runs of this workflow (limit 100 — plenty for 30d at fleet cadence).
    const runsRaw = gh(['api', `repos/${OWNER}/${repo}/actions/workflows/${wf}/runs?per_page=100&created=>=${sinceISO.slice(0, 10)}`, '--jq', '.workflow_runs']);
    let runs = []; try { runs = JSON.parse(runsRaw || '[]'); } catch {}
    const successes = runs.filter((r) => r.conclusion === 'success');
    const failures = runs.filter((r) => r.conclusion === 'failure');
    // MTTR approx: average time between each failure and the next success on this workflow.
    const sorted = runs.slice().sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    let mttrSecs = 0, mttrCount = 0;
    for (let i = 0; i < sorted.length; i++) {
      if (sorted[i].conclusion !== 'failure') continue;
      const next = sorted.slice(i + 1).find((r) => r.conclusion === 'success');
      if (next) { mttrSecs += (new Date(next.created_at) - new Date(sorted[i].created_at)) / 1000; mttrCount++; }
    }
    doraMetrics[repo] = {
      workflow: wf,
      windowDays: 30,
      deployFrequency: successes.length,
      changeFailureRate: runs.length ? +(failures.length / runs.length).toFixed(3) : 0,
      mttrAvgMinutes: mttrCount ? Math.round(mttrSecs / mttrCount / 60) : null,
      totalRuns: runs.length,
    };
  }
}

// ---- 3c. SLO burn-rate probe (ARC-ADR-024 / sre-engineer finding) ----------
// Probes each known live service's health endpoint; warns on non-2xx (the
// "fleet on fire" surface ADR-024 calls for at solo-team scale). The list of
// targets is intentionally explicit — the heartbeat shouldn't try to be a
// service-discovery layer. Off by default; emit only when --slo is set.
const SLO_PROBE = process.argv.includes('--slo');
const SLO_TARGETS = [
  { name: 'frontend-core (ACA, public)', url: 'https://frontend-core.kindcoast-b0a6ea84.eastus.azurecontainerapps.io/', expect: [200, 301, 302] },
  // backend-core + arcadedb are internal-ingress; reachable only from inside
  // the ACA env. Add an in-env probe-runner later (or expose a minimal status
  // page via the frontend BFF) before promoting them here.
  // local-fleet MCP control plane — proves all 3 layers up: cloudflared
  // connector alive + tunnel routing → :8765 + MCP server process. 200
  // = healthy; non-2xx means one of those layers needs attention.
  { name: 'local-fleet MCP (mcp.untool.ai)', url: 'https://mcp.untool.ai/healthz', expect: [200] },
  { name: 'untool.ai frontend (via tunnel)', url: 'https://untool.ai/', expect: [200, 301, 302, 308] },
];
const sloProbes = [];
if (SLO_PROBE) {
  for (const t of SLO_TARGETS) {
    const code = Number(gh(['api', t.url, '--jq', '.']) ? '0' : '0'); // unreliable via gh, use curl shape
    // gh API doesn't fit arbitrary URLs cleanly; fall back to execFileSync('curl', ...)
    let curlOut = '';
    try { curlOut = execFileSync('curl', ['-sS', '-o', '/dev/null', '-w', '%{http_code}', '--max-time', '5', t.url], { encoding: 'utf8' }).trim(); } catch {}
    const status = Number(curlOut) || 0;
    const ok = t.expect.includes(status);
    sloProbes.push({ name: t.name, url: t.url, status, ok });
    if (!ok) add(HUB, 'warn', 'slo-probe-failed',
      `${t.name} health probe -> ${status} (expected ${t.expect.join('/')}). Investigate before user-visible burn accrues.`);
  }
}

// ---- 3d. Host disk probe (ARC-ADR-024 follow-up) ---------------------------
// Backstop against the 2026-05-26 disk-cascade incident (Docker VHDX filled
// the dev box, jobs OOM'd / failed in cryptic ways). Off by default; emit only
// when --disk is set. Uses Node's portable statfs (works on Linux + Windows).
const DISK_PROBE = process.argv.includes('--disk');
const DISK_MIN_FREE_GB = Number(process.env.AGENTARMY_DISK_MIN_FREE_GB) || 5;
let diskStatus = null;
if (DISK_PROBE) {
  try {
    const s = statfsSync(process.cwd());
    const totalGB = Math.round((s.bsize * s.blocks) / 1e9);
    const availGB = Math.round((s.bsize * s.bavail) / 1e9);
    const usePct = `${Math.round((1 - s.bavail / s.blocks) * 100)}%`;
    diskStatus = { availGB, totalGB, usePct };
    if (availGB < DISK_MIN_FREE_GB) {
      add(HUB, 'warn', 'host-disk-low',
        `Host disk ${availGB} GB free / ${totalGB} GB total (${usePct} used) — under threshold ${DISK_MIN_FREE_GB} GB. Run aggressive prune before the next CI/build wave.`);
    }
  } catch (e) {
    add(HUB, 'warn', 'host-disk-probe-failed', `statfs failed: ${e.message}`);
  }
}

// ---- 4. Dispatch (optional, --apply) ---------------------------------------
const dispatched = [];
if (APPLY) {
  for (const f of findings.filter((x) => x.severity === 'gap')) {
    const dupe = Number(gh(['issue', 'list', '--repo', `${OWNER}/${f.repo}`, '--state', 'open', '--search', `heartbeat: ${f.kind}`, '--json', 'number', '--jq', 'length']) || '0');
    if (dupe > 0) { dispatched.push(`skipped (dupe): ${f.repo} / ${f.kind}`); continue; }
    const labelArgs = [];
    for (const l of [f.label, 'Enabler']) {
      if (Number(gh(['label', 'list', '--repo', `${OWNER}/${f.repo}`, '--search', l, '--json', 'name', '--jq', 'length']) || '0') > 0) labelArgs.push('--label', l);
    }
    const url = gh(['issue', 'create', '--repo', `${OWNER}/${f.repo}`,
      '--title', `[Enabler] heartbeat: ${f.kind}`,
      '--body', `${f.detail}\n\n— dispatched by the fleet heartbeat (tools/fleet-heartbeat.mjs)`,
      ...labelArgs]);
    dispatched.push(url || `(create failed: ${f.repo} / ${f.kind})`);
  }
}

// ---- Output ----------------------------------------------------------------
// Render a single tier's container list as a markdown table row block.
const renderTier = (label, list) => {
  if (!list.length) return `- _(none)_`;
  return list.map((c) =>
    `- **${c.name}** (\`${c.repo}/${c.path}\`) · kind=\`${c.kind}\` · proves: ${c.doctor} · deploy: \`${c.deploy}\``
  ).join('\n');
};

if (JSON_OUT) {
  console.log(JSON.stringify({ mode: APPLY ? 'apply' : 'dry-run', findings, health, containers, doraMetrics, sloProbes, secretsState, diskStatus, dispatched, postmanNote }, null, 2));
} else {
  let out = `# 🫀 Fleet heartbeat — ${new Date().toISOString()} (${APPLY ? 'APPLY' : 'dry-run'})\n\n`;
  out += `## Findings (${findings.length})\n`;
  out += findings.length
    ? findings.map((f) => `- **[${f.severity}] ${f.repo}** · ${f.kind}: ${f.detail}`).join('\n')
    : '- none — fleet contracts/agents in sync ✅';
  if (postmanNote) out += `\n\n> ⚠️ ${postmanNote}`;

  // Tier-grouped container inventory (ARC-ADR-023) — answers "what's deployed
  // where, by tier" in one glance. The fleet's 'shape report'.
  const totalContainers = containers.platform.length + containers.application.length + containers.function.length + containers.untiered.length;
  out += `\n\n## Container Inventory by Tier (ARC-ADR-023)\n`;
  out += `_${totalContainers} image.json manifest(s) across hub + ${SPOKES.length} spoke(s)._\n\n`;
  out += `### Platform tier (${containers.platform.length})  — slow lifecycle, has state\n`;
  out += renderTier('platform', containers.platform);
  out += `\n\n### Application tier (${containers.application.length})  — one container per spoke, stateless\n`;
  out += renderTier('application', containers.application);
  out += `\n\n### Function tier (${containers.function.length})  — small, stateless, independently rolled out\n`;
  out += renderTier('function', containers.function);
  if (containers.untiered.length) {
    out += `\n\n### ⚠️ Untiered (${containers.untiered.length}) — missing \`tier\` field\n`;
    out += renderTier('untiered', containers.untiered);
  }

  // DORA (only if --dora flag) — emit a compact per-repo table.
  if (DORA && Object.keys(doraMetrics).length) {
    out += `\n\n## DORA (last 30 days)\n`;
    out += Object.entries(doraMetrics).map(([r, m]) =>
      `- **${r}** (${m.workflow}): deploys=${m.deployFrequency} · CFR=${(m.changeFailureRate * 100).toFixed(1)}% · MTTR=${m.mttrAvgMinutes ?? 'n/a'} min · total runs=${m.totalRuns}`
    ).join('\n');
  }

  // SLO probes (only if --slo flag) — one line per probed target.
  if (SLO_PROBE && sloProbes.length) {
    out += `\n\n## SLO Probes\n`;
    out += sloProbes.map((p) =>
      `- ${p.ok ? '✅' : '⚠️'} ${p.name} → ${p.status} (${p.url})`
    ).join('\n');
  }

  // Secrets staleness (only if --secrets flag) — per-secret age vs cadence.
  if (SECRETS_PROBE && secretsState.length) {
    out += `\n\n## Secrets Staleness\n`;
    out += secretsState.map((s) => {
      if (s.status === 'missing') return `- ❓ ${s.name} — not found in KV (cadence ${s.cadenceDays}d)`;
      const icon = s.overdueGrace ? '⚠️' : s.stale ? '🟡' : '✅';
      return `- ${icon} ${s.name} — age ${s.ageDays}d / cadence ${s.cadenceDays}d`;
    }).join('\n');
  }

  // Host disk (only if --disk flag) — preventive backstop for the
  // 2026-05-26 disk-cascade incident.
  if (DISK_PROBE && diskStatus) {
    const icon = diskStatus.availGB < DISK_MIN_FREE_GB ? '⚠️' : '✅';
    out += `\n\n## Host Disk\n- ${icon} ${diskStatus.availGB} GB free / ${diskStatus.totalGB} GB total (${diskStatus.usePct} used) — threshold ${DISK_MIN_FREE_GB} GB`;
  }

  out += `\n\n## Health & Issue Queue\n` + Object.entries(health).map(([r, h]) =>
    `- **${r}**: ${h.openIssues} open issue(s) · ${h.openPRs} open PR(s) · ${h.recentFailedRuns} recent failed run(s)${h.recentFailedRuns ? ' ⚠️' : ''}` +
    (h.armyTask.length ? `\n  - dispatched (agent-army-task, ${h.armyTask.length}, waiting pickup): ${h.armyTask.map((i) => `#${i.number}`).join(', ')}` : '') +
    (h.copilotTask.length ? `\n  - copilot-task (${h.copilotTask.length}, auto-spawns): ${h.copilotTask.map((i) => `#${i.number}`).join(', ')}` : '')
  ).join('\n');
  out += APPLY
    ? `\n\n## Dispatched (${dispatched.length})\n` + (dispatched.length ? dispatched.map((d) => `- ${d}`).join('\n') : '- nothing to dispatch')
    : `\n\n_(dry-run — re-run with \`--apply\` to dispatch ${findings.filter((f) => f.severity === 'gap').length} gap(s) as issues)_`;
  console.log(out);
}
