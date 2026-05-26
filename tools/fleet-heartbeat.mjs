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

import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';

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
const treePaths = (repo) => {
  const o = gh(['api', `repos/${OWNER}/${repo}/git/trees/main?recursive=1`, '--jq', '.tree[].path']);
  return o ? o.split('\n') : [];
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

for (const spoke of SPOKES) {
  for (const c of repoTrees[spoke].filter(isContract)) {
    const base = c.split('/').pop();
    if (registry && !registry.includes(base)) {
      add(HUB, 'warn', 'unregistered-contract',
        `${spoke}/${c} is not registered in docs/contracts.md — add it (producer/consumers/status/ADR).`);
    }
  }
}

// backend OpenAPI must be vendored into its consumers (fe + mc)
for (const spoke of ['frontend-core', 'middle-core']) {
  const ok = repoTrees[spoke].some((p) => p.endsWith('backend-core.openapi.json'));
  if (!ok) add(spoke, 'gap', 'unvendored-contract',
    `backend-core OpenAPI is not vendored in ${spoke} — vendor it + generate the client.`, GAP_LABEL);
}

const postmanNote = SPOKES.flatMap((s) => repoTrees[s].filter(isContract)).length
  ? 'Verify each contract has a published Postman spec + mock (run locally with Key Vault creds — not checkable from the heartbeat).'
  : null;

// ---- 2. Agent / skills pack drift (hub-authoritative, one-way hub→spoke) ----
const hubAgents = repoTrees[HUB].filter((p) => p.startsWith('.claude/agents/') && p.endsWith('.md'));
for (const spoke of SPOKES) {
  const spokeAgents = repoTrees[spoke].filter((p) => p.startsWith('.claude/agents/') && p.endsWith('.md'));
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
  for (const path of repoTrees[repo].filter(isImageManifest)) {
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
  console.log(JSON.stringify({ mode: APPLY ? 'apply' : 'dry-run', findings, health, containers, dispatched, postmanNote }, null, 2));
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
