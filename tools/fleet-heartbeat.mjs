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
//   node tools/fleet-heartbeat.mjs --apply    # also create dispatch issues for gaps (dedup'd)
//   node tools/fleet-heartbeat.mjs --json      # machine-readable findings

import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';

const OWNER = 'nickpclarke';
const HUB = 'AgentArmy';
const SPOKES = ['frontend-core', 'backend-core', 'middle-core'];
const APPLY = process.argv.includes('--apply');
const JSON_OUT = process.argv.includes('--json');

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
    `backend-core OpenAPI is not vendored in ${spoke} — vendor it + generate the client.`, 'copilot-task');
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

// ---- 3. Fleet health -------------------------------------------------------
const health = {};
for (const repo of [HUB, ...SPOKES]) {
  const openPRs = Number(gh(['pr', 'list', '--repo', `${OWNER}/${repo}`, '--state', 'open', '--json', 'number', '--jq', 'length']) || '0');
  const recentFailedRuns = Number(gh(['run', 'list', '--repo', `${OWNER}/${repo}`, '--limit', '8', '--json', 'conclusion', '--jq', '[.[] | select(.conclusion=="failure")] | length']) || '0');
  health[repo] = { openPRs, recentFailedRuns };
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
if (JSON_OUT) {
  console.log(JSON.stringify({ mode: APPLY ? 'apply' : 'dry-run', findings, health, dispatched, postmanNote }, null, 2));
} else {
  let out = `# 🫀 Fleet heartbeat — ${new Date().toISOString()} (${APPLY ? 'APPLY' : 'dry-run'})\n\n`;
  out += `## Findings (${findings.length})\n`;
  out += findings.length
    ? findings.map((f) => `- **[${f.severity}] ${f.repo}** · ${f.kind}: ${f.detail}`).join('\n')
    : '- none — fleet contracts/agents in sync ✅';
  if (postmanNote) out += `\n\n> ⚠️ ${postmanNote}`;
  out += `\n\n## Health\n` + Object.entries(health).map(([r, h]) =>
    `- **${r}**: ${h.openPRs} open PR(s), ${h.recentFailedRuns} recent failed run(s)${h.recentFailedRuns ? ' ⚠️' : ''}`).join('\n');
  out += APPLY
    ? `\n\n## Dispatched (${dispatched.length})\n` + (dispatched.length ? dispatched.map((d) => `- ${d}`).join('\n') : '- nothing to dispatch')
    : `\n\n_(dry-run — re-run with \`--apply\` to dispatch ${findings.filter((f) => f.severity === 'gap').length} gap(s) as issues)_`;
  console.log(out);
}
