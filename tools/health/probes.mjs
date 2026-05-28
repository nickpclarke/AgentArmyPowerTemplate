// probes.mjs — the four health probes. Each is `(ctx) => Reading[]` and is a
// pure function of ctx (config + already-collected Windows data + helpers), so
// adding a new signal is just appending a function to the exported list.
//
//   host-disk  → free space on the drives that actually halt the PC (C:)
//   docker     → engine reachable + total/reclaimable disk usage
//   containers → per-container health + restart-loop detection
//   wsl        → ext4.vhdx sizes (the files that silently grow on C:)

import { statfsSync } from 'node:fs';
import { docker, grade, reading, sizeToGB, worst, REPO_ROOT } from './lib.mjs';

// ---- host disk -------------------------------------------------------------
function hostDiskProbe(ctx) {
  const t = ctx.config.thresholds;
  // Windows / WSL: the real "PC stops" signal is the Windows fixed drive(s).
  if (ctx.win?.drives?.length) {
    const want = new Set((ctx.config.drives || ['C']).map((d) => String(d).toUpperCase()));
    const drives = ctx.win.drives.filter((d) => want.has(String(d.letter).toUpperCase()));
    const pick = drives.length ? drives : ctx.win.drives; // fall back to all if filter misses
    return pick.map((d) => {
      const status = worst([
        grade(d.freeGB, t.hostDiskFreeGB, 'low'),
        grade(d.usedPct, t.hostDiskUsedPct, 'high'),
      ]);
      return reading({
        id: `host-disk.${d.letter}`,
        component: 'host-disk',
        label: `${d.letter}: drive`,
        value: d.freeGB,
        unit: 'GB free',
        status,
        message: `${d.letter}: ${d.freeGB} GB free / ${d.sizeGB} GB (${d.usedPct}% used)`,
        evidence: d,
        remediations: status === 'critical' ? ['docker-prune-safe', 'compact-wsl-vhdx'] : [],
      });
    });
  }

  // Plain Linux (incl. this cloud env): fall back to statfs on the repo mount.
  try {
    const s = statfsSync(REPO_ROOT);
    const sizeGB = +((s.bsize * s.blocks) / 1e9).toFixed(1);
    const freeGB = +((s.bsize * s.bavail) / 1e9).toFixed(1);
    const usedPct = +((1 - s.bavail / s.blocks) * 100).toFixed(1);
    const status = worst([
      grade(freeGB, t.hostDiskFreeGB, 'low'),
      grade(usedPct, t.hostDiskUsedPct, 'high'),
    ]);
    return [reading({
      id: 'host-disk.local',
      component: 'host-disk',
      label: 'local mount',
      value: freeGB,
      unit: 'GB free',
      status,
      message: `${freeGB} GB free / ${sizeGB} GB (${usedPct}% used) on ${REPO_ROOT}`,
      evidence: { freeGB, sizeGB, usedPct },
      remediations: status === 'critical' ? ['docker-prune-safe'] : [],
    })];
  } catch (e) {
    return [reading({ id: 'host-disk.local', component: 'host-disk', label: 'local mount',
      status: 'skip', message: `statfs failed: ${e.message}` })];
  }
}

// ---- docker engine + disk usage --------------------------------------------
function dockerProbe(ctx) {
  const out = [];
  const ver = docker(['version', '--format', '{{json .Server.Version}}'], ctx.timeoutMs);
  if (!ver.ok && !docker(['--version'], 2000).ok) {
    return [reading({ id: 'docker.engine', component: 'docker', label: 'engine',
      status: 'skip', message: 'docker CLI not installed' })];
  }
  const reachable = ver.ok && ver.out && ver.out !== 'null';
  out.push(reading({
    id: 'docker.engine', component: 'docker', label: 'engine',
    status: reachable ? 'ok' : 'warn',
    message: reachable ? `engine reachable (server ${ver.out.replace(/"/g, '')})` : 'docker CLI present but engine not reachable',
    evidence: { reachable },
  }));
  if (!reachable) return out;

  // docker system df --format json → one JSON object per resource type.
  const df = docker(['system', 'df', '--format', '{{json .}}'], ctx.timeoutMs);
  if (df.ok && df.out) {
    let totalGB = 0;
    let reclaimGB = 0;
    const rows = {};
    for (const line of df.out.split(/\r?\n/).filter(Boolean)) {
      try {
        const r = JSON.parse(line);
        const sz = sizeToGB(r.Size);
        const rc = sizeToGB(r.Reclaimable);
        totalGB += sz;
        reclaimGB += rc;
        rows[r.Type] = { size: r.Size, reclaimable: r.Reclaimable };
      } catch { /* skip unparseable row */ }
    }
    totalGB = +totalGB.toFixed(1);
    reclaimGB = +reclaimGB.toFixed(1);
    const t = ctx.config.thresholds;
    const usageStatus = grade(totalGB, t.dockerTotalGB, 'high');
    out.push(reading({
      id: 'docker.usage', component: 'docker', label: 'disk usage',
      value: totalGB, unit: 'GB', status: usageStatus,
      message: `docker is using ${totalGB} GB (${reclaimGB} GB reclaimable)`,
      evidence: rows,
      remediations: usageStatus !== 'ok' ? ['docker-prune-safe'] : [],
    }));
    const reclaimStatus = grade(reclaimGB, t.dockerReclaimableGB, 'high');
    out.push(reading({
      id: 'docker.reclaimable', component: 'docker', label: 'reclaimable',
      value: reclaimGB, unit: 'GB', status: reclaimStatus,
      message: `${reclaimGB} GB reclaimable (build cache + dangling + stopped)`,
      evidence: rows,
      remediations: reclaimStatus !== 'ok' ? ['docker-prune-safe'] : [],
    }));
  }
  return out;
}

// ---- containers: health + restart loops ------------------------------------
function containersProbe(ctx) {
  // Skip cleanly if the engine isn't up (dockerProbe already surfaced that).
  if (!docker(['version', '--format', '{{.Server.Version}}'], 2500).ok) {
    return [reading({ id: 'containers', component: 'containers', label: 'containers',
      status: 'skip', message: 'engine not reachable' })];
  }
  const ids = docker(['ps', '-aq'], ctx.timeoutMs);
  if (!ids.ok || !ids.out) {
    return [reading({ id: 'containers', component: 'containers', label: 'containers',
      status: 'ok', message: 'no containers' })];
  }
  const idList = ids.out.split(/\r?\n/).filter(Boolean);
  // One batched inspect for name / restart count / health / state.
  const fmt = '{{.Name}}|{{.RestartCount}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}|{{.State.Status}}';
  const insp = docker(['inspect', '--format', fmt, ...idList], ctx.timeoutMs);
  if (!insp.ok) {
    return [reading({ id: 'containers', component: 'containers', label: 'containers',
      status: 'warn', message: 'could not inspect containers' })];
  }
  const t = ctx.config.thresholds;
  const out = [];
  for (const line of insp.out.split(/\r?\n/).filter(Boolean)) {
    const [rawName, restartStr, health, state] = line.split('|');
    const name = (rawName || '').replace(/^\//, '');
    const restarts = parseInt(restartStr, 10) || 0;
    let status = grade(restarts, t.containerRestarts, 'high');
    if (health === 'unhealthy' || state === 'restarting') status = 'critical';
    if (status === 'ok') continue; // only surface containers that need attention
    out.push(reading({
      id: `containers.${name}`, component: 'containers', label: name,
      value: restarts, unit: 'restarts', status,
      message: `${name}: state=${state} health=${health} restarts=${restarts}`,
      evidence: { state, health, restarts },
    }));
  }
  if (!out.length) {
    out.push(reading({ id: 'containers', component: 'containers', label: 'containers',
      status: 'ok', message: `${idList.length} container(s), all healthy` }));
  }
  return out;
}

// ---- WSL ext4.vhdx growth --------------------------------------------------
function wslProbe(ctx) {
  if (!ctx.win?.wsl?.length) {
    return [reading({ id: 'wsl', component: 'wsl', label: 'wsl',
      status: 'skip', message: 'no WSL data (not on Windows/WSL)' })];
  }
  const t = ctx.config.thresholds;
  return ctx.win.wsl
    .filter((d) => d.vhdxGB > 0)
    .map((d) => {
      const status = grade(d.vhdxGB, t.wslVhdxGB, 'high');
      return reading({
        id: `wsl.${d.distro}`, component: 'wsl', label: d.distro,
        value: d.vhdxGB, unit: 'GB', status,
        message: `${d.distro} (${d.state}): ext4.vhdx ${d.vhdxGB} GB`,
        evidence: d,
        // vhdx compaction is a manual runbook (needs wsl --shutdown); never auto.
        remediations: status === 'critical' ? ['compact-wsl-vhdx'] : [],
      });
    });
}

export const probes = [hostDiskProbe, dockerProbe, containersProbe, wslProbe];
