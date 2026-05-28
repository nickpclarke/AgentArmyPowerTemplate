// remediate.mjs — the remediation catalog + guarded executor.
//
// Each action declares whether it is eligible for AUTO execution. The guardrails
// are deliberate and must not be relaxed:
//   • auto actions reclaim ONLY build cache, dangling (untagged) images, and
//     stopped containers — never named volumes, never `-a` (which deletes
//     unused-but-tagged images), never `compose down`.
//   • a cooldown (config.remediation.cooldownMinutes) prevents prune-thrash.
//   • every auto run is reported back through the alert channels.
// Destructive/manual actions (aggressive prune, vhdx compaction) only ever
// print their runbook — they are never executed automatically.

import { docker } from './lib.mjs';

export const CATALOG = {
  'docker-prune-safe': {
    title: 'Reclaim Docker build cache + dangling images + stopped containers',
    auto: true,
    describe: 'docker container prune -f && docker image prune -f && docker builder prune -f',
    run(timeoutMs = 60000) {
      const steps = [
        ['container', ['container', 'prune', '-f']],
        ['image', ['image', 'prune', '-f']],            // dangling only — no -a
        ['builder', ['builder', 'prune', '-f']],
      ];
      const detail = [];
      let reclaimed = '';
      for (const [name, args] of steps) {
        const r = docker(args, timeoutMs);
        const m = r.out.match(/Total reclaimed space:\s*(.+)$/m);
        if (m) reclaimed += `${reclaimed ? ', ' : ''}${name}: ${m[1].trim()}`;
        detail.push(`${name} prune ${r.ok ? 'ok' : 'FAILED'}`);
      }
      return { ok: true, reclaimed: reclaimed || 'unknown', detail: detail.join('; ') };
    },
  },

  // Manual-only: removes unused-but-tagged images too. Needs a human to confirm
  // nothing in-flight depends on those images.
  'docker-prune-aggressive': {
    title: 'Aggressively reclaim ALL unused images (manual — removes tagged images)',
    auto: false,
    describe: 'docker system prune -a -f   # review first; does NOT remove named volumes',
  },

  // Manual-only runbook: the only thing that shrinks the ext4.vhdx FILE on C:
  // (pruning frees space INSIDE the vhdx but the file never auto-shrinks).
  'compact-wsl-vhdx': {
    title: 'Compact the WSL/Docker ext4.vhdx so freed space returns to Windows C:',
    auto: false,
    describe: [
      '# 1. Stop everything, then compact (run in an elevated PowerShell on the host):',
      'wsl --shutdown',
      '# 2a. Modern WSL — enable auto-shrink so it stays compact:',
      'wsl --manage <distro> --set-sparse true',
      '# 2b. Or compact in place with diskpart:',
      'diskpart',
      '#   select vdisk file="C:\\Users\\<you>\\AppData\\Local\\Docker\\wsl\\disk\\docker_data.vhdx"',
      '#   attach vdisk readonly  /  compact vdisk  /  detach vdisk',
      '# (Optimize-VHD also works if you have Hyper-V tools installed.)',
    ].join('\n'),
  },
};

// Execute the auto-eligible, config-allowed remediations referenced by the
// critical readings. Returns a list of result objects for alerting.
export function runAuto(readings, remediationCfg, timeoutMs = 60000) {
  const allow = new Set(remediationCfg.allow || ['docker-prune-safe']);
  const ids = new Set();
  for (const r of readings) {
    if (r.status !== 'critical') continue;
    for (const id of r.remediations || []) {
      const action = CATALOG[id];
      if (action?.auto && allow.has(id)) ids.add(id);
    }
  }
  const results = [];
  for (const id of ids) {
    const action = CATALOG[id];
    try {
      const res = action.run(timeoutMs);
      results.push({ id, title: action.title, ...res });
    } catch (e) {
      results.push({ id, title: action.title, ok: false, reclaimed: '', detail: e.message });
    }
  }
  return results;
}

// Collect the manual runbook lines for readings that need a human action.
export function manualRunbook(readings) {
  const ids = new Set();
  for (const r of readings) {
    for (const id of r.remediations || []) {
      const action = CATALOG[id];
      if (action && !action.auto) ids.add(id);
    }
  }
  return [...ids].map((id) => ({ id, title: CATALOG[id].title, describe: CATALOG[id].describe }));
}
