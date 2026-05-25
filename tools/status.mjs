#!/usr/bin/env node
// AgentArmy platform status dashboard.
// Usage:
//   node tools/status.mjs            full live view (color in a TTY)
//   node tools/status.mjs --fast     local-only (skip GitHub network calls)
//   node tools/status.mjs --no-color force plain text
// Wired as a SessionStart hook (plain text) and runnable manually (color).
// Degrades gracefully: any missing tool / failed call is shown as unknown, never throws.

import { execFile } from "node:child_process";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ARGV = process.argv.slice(2);
const FAST = ARGV.includes("--fast") || ARGV.includes("--no-network");
const COLOR = process.stdout.isTTY && !ARGV.includes("--no-color");

const HUB = "nickpclarke/AgentArmy";
const SPOKES = ["nickpclarke/frontend-core", "nickpclarke/backend-core"];
const TARGETS = [
  "Azure Container Apps (dev)",
  "ArcadeDB (Azure ACI rg-arcadedb-test)",
  "GCP agentarmy-497217 / us-central1",
];
const NORTH_STAR = ["Ontology-Pipeline", "Reification-and-Hyperedges", "Factory-Loop-Test-Infrastructure"];

// --- tiny ANSI helpers (no deps) ---
const ansi = (code, s) => (COLOR ? `\x1b[${code}m${s}\x1b[0m` : s);
const dim = (s) => ansi("2", s);
const bold = (s) => ansi("1", s);
const green = (s) => ansi("32", s);
const red = (s) => ansi("31", s);
const yellow = (s) => ansi("33", s);
const cyan = (s) => ansi("36", s);
const OK = green("●"), WARN = yellow("○"), BAD = red("✕"), NA = dim("·");

const firstLine = (s) => (s || "").split(/\r?\n/)[0].trim();

// run a command; never throws; returns {ok,out}
function run(cmd, args, { timeout = 8000, cwd = ROOT } = {}) {
  return new Promise((resolve) => {
    execFile(cmd, args, { cwd, timeout, windowsHide: true, maxBuffer: 16 * 1024 * 1024 }, (err, stdout) => {
      resolve({ ok: !err, out: (stdout || "").trim() });
    });
  });
}
async function ver(cmd, args = ["--version"]) {
  const r = await run(cmd, args, { timeout: 4000 });
  return r.ok ? firstLine(r.out) : null;
}
async function ghJson(args, { timeout = 9000 } = {}) {
  if (FAST) return null;
  const r = await run("gh", args, { timeout });
  if (!r.ok) return null;
  try { return JSON.parse(r.out); } catch { return null; }
}
async function readJson(rel) {
  try { return JSON.parse(await readFile(path.join(ROOT, rel), "utf8")); } catch { return null; }
}
async function readText(rel) {
  try { return await readFile(path.join(ROOT, rel), "utf8"); } catch { return null; }
}

async function vaultNotes() {
  const base = path.join(ROOT, "obsidian", "labs", "AgentArmyLabs");
  const out = [];
  async function walk(dir) {
    let entries;
    try { entries = await readdir(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (e.name.startsWith(".")) continue;
      const full = path.join(dir, e.name);
      if (e.isDirectory()) await walk(full);
      else if (e.name.endsWith(".md")) {
        try { const s = await stat(full); out.push({ name: e.name.replace(/\.md$/, ""), mtime: s.mtimeMs }); } catch {}
      }
    }
  }
  await walk(base);
  return out;
}

function prLine(p) {
  const tag = p.isDraft ? dim("draft") : cyan("ready");
  return `   ${dim("#" + p.number)} ${truncate(p.title, 52)}  ${tag}`;
}
const truncate = (s, n) => (s && s.length > n ? s.slice(0, n - 1) + "…" : s || "");

async function main() {
  const model = await readJson("templates/middle-core/generated/model-runtime.fixture.json");
  const modelYaml = await readText("model/middle-core/model.yaml");
  const schema = (modelYaml && (modelYaml.match(/schema_version:\s*(\S+)/) || [])[1]) || "?";

  // gather everything in parallel
  const [
    branch, head, dirty,
    vNode, vDotnet, vPython, vGh, vAz, vGcloud, vDocker,
    hubPRs, fePRs, bePRs,
    gate, issues, merged, notes,
  ] = await Promise.all([
    run("git", ["rev-parse", "--abbrev-ref", "HEAD"]).then((r) => r.out),
    run("git", ["rev-parse", "--short", "HEAD"]).then((r) => r.out),
    run("git", ["status", "--porcelain"]).then((r) => r.out.split(/\r?\n/).filter(Boolean).length),
    ver("node"), ver("dotnet"), ver("python", ["--version"]).then((v) => v || null),
    ver("gh", ["--version"]), ver("az", ["version", "-o", "tsv"]).then(() => "ok").catch(() => null),
    ver("gcloud", ["--version"]), ver("docker", ["--version"]),
    ghJson(["pr", "list", "--repo", HUB, "--state", "open", "--json", "number,title,isDraft,headRefName"]),
    ghJson(["pr", "list", "--repo", SPOKES[0], "--state", "open", "--json", "number"]),
    ghJson(["pr", "list", "--repo", SPOKES[1], "--state", "open", "--json", "number"]),
    ghJson(["run", "list", "--repo", HUB, "--workflow", "middle-core-model.yml", "--limit", "1", "--json", "conclusion,status"]),
    ghJson(["issue", "list", "--repo", HUB, "--state", "open", "--limit", "100", "--json", "number,title,labels"]),
    ghJson(["pr", "list", "--repo", HUB, "--state", "merged", "--limit", "6", "--json", "number,title"]),
    vaultNotes(),
  ]);

  const L = [];
  const rule = dim("─".repeat(70));
  L.push("");
  L.push(bold(cyan("  AGENTARMY — PLATFORM STATUS")) + dim(`   ${new Date().toISOString().replace("T", " ").slice(0, 16)}`));
  L.push("  " + rule);

  // ENVIRONMENT
  L.push(bold("  ENVIRONMENT"));
  if (model) L.push(`   model   ${cyan(model.model_id)} (${schema})  ${dim("·")}  ${model.object_types?.length ?? "?"} objects · ${model.state_machines?.length ?? "?"} machines · ${model.scenario_ids?.length ?? "?"} scenarios`);
  L.push(`   git     ${branch} @ ${head}${dirty ? yellow(`  (${dirty} uncommitted)`) : green("  (clean)")}`);
  const tools = [["node", vNode], ["dotnet", vDotnet], ["python", vPython], ["gh", vGh ? "ok" : null], ["az", vAz], ["gcloud", vGcloud ? "ok" : null], ["docker", vDocker]]
    .map(([n, v]) => `${v ? OK : BAD} ${n}${v && v !== "ok" ? dim(" " + ((v.match(/\d[\d.]*/) || [""])[0])) : ""}`).join("  ");
  L.push(`   tools   ${tools}`);
  L.push(`   targets ${dim(TARGETS.join(" · "))}`);
  L.push("");

  // STATUS suite
  const gateConcl = gate && gate[0] ? gate[0].conclusion || gate[0].status : null;
  const gateDot = gateConcl === "success" ? OK : gateConcl ? BAD : (FAST ? NA : WARN);
  L.push(bold("  STATUS") +
    `   ${dirty ? WARN : OK} repo-clean   ${gateDot} ci-gate${gateConcl ? dim("(" + gateConcl + ")") : (FAST ? dim("(skipped)") : dim("(?)"))}   ${vDotnet ? OK : BAD} dotnet   ${vNode ? OK : BAD} node   ${vGh ? OK : BAD} gh`);
  L.push("");

  // LAYERS
  L.push(bold("  LAYERS / REPOS"));
  const hubOpen = Array.isArray(hubPRs) ? hubPRs.length : null;
  L.push(`   ${OK} AgentArmy ${dim("(hub)")}      ${branch === "main" ? "main" : dim(branch)}   ${prCount(hubOpen)}`);
  L.push(`   ${OK} frontend-core ${dim("(spoke)")}  ${dim("main")}   ${prCount(Array.isArray(fePRs) ? fePRs.length : null)}`);
  L.push(`   ${OK} backend-core ${dim("(spoke)")}   ${dim("main")}   ${prCount(Array.isArray(bePRs) ? bePRs.length : null)}`);
  L.push("");

  // PRs IN FLIGHT
  if (Array.isArray(hubPRs)) {
    L.push(bold(`  PRs IN FLIGHT`) + dim(` (${hubPRs.length} on hub)`));
    if (hubPRs.length === 0) L.push(dim("   none open"));
    else hubPRs.slice(0, 8).forEach((p) => L.push(prLine(p)));
    L.push("");
  } else if (!FAST) {
    L.push(bold("  PRs IN FLIGHT") + dim("  (unavailable — gh)"));
    L.push("");
  }

  // PROGRAM
  if (Array.isArray(issues)) {
    const by = {};
    for (const i of issues) for (const lab of i.labels || []) by[lab.name] = (by[lab.name] || 0) + 1;
    const counts = ["Epic", "Feature", "Enabler", "Spike", "Bug"].map((k) => `${by[k] || 0} ${k.toLowerCase()}${(by[k] || 0) === 1 ? "" : "s"}`).join(" · ");
    L.push(bold("  PROGRAM") + dim(` (${issues.length} open issues)`));
    L.push(`   ${counts}`);
    const pin = issues.find((i) => /PIN-E\b/.test(i.title));
    if (pin) L.push(`   ${cyan("RT5 pinning")} → Epic #${pin.number} (PIN-*: see board)`);
    L.push("");
  }

  // LABS
  L.push(bold("  LABS") + dim(" (in-repo Obsidian vault)"));
  notes.sort((a, b) => b.mtime - a.mtime);
  L.push(`   ${notes.length} notes  ${dim("·")}  north-star: ${NORTH_STAR.filter((n) => notes.some((x) => x.name === n)).map(cyan).join(", ") || dim("—")}`);
  if (notes.length) L.push(`   recent: ${dim(notes.slice(0, 3).map((n) => n.name).join(", "))}`);
  L.push("");

  // RECENT MERGES
  if (Array.isArray(merged) && merged.length) {
    L.push(bold("  RECENT MERGES"));
    merged.forEach((p) => L.push(`   ${green("✓")} ${dim("#" + p.number)} ${truncate(p.title, 56)}`));
    L.push("");
  }

  L.push("  " + rule);
  L.push(dim("  full live view: node tools/status.mjs   ·   fast/local: --fast"));
  L.push("");
  process.stdout.write(L.join("\n") + "\n");
}

const prCount = (n) => (n === null ? dim("PRs ?") : n === 0 ? dim("0 open PR") : yellow(`${n} open PR${n === 1 ? "" : "s"}`));

main().catch((e) => { process.stdout.write(`status dashboard error: ${e?.message || e}\n`); });
