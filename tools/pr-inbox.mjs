#!/usr/bin/env node
// AgentArmy cross-repo PR/issue comment inbox.
// One place to see the back-and-forth across the hub + spoke repos so the hub can pick up
// and reply via comments.
//
// Usage:
//   node tools/pr-inbox.mjs                 recent comments across all repos, newest first
//   node tools/pr-inbox.mjs --repo middle-core   only that repo
//   node tools/pr-inbox.mjs --mentions       only comments that @-mention an agent/me
//   node tools/pr-inbox.mjs --limit 40       cap the feed (default 25)
//
// Zero-dep; uses the gh CLI. Never throws — a failed repo is shown as unavailable.

import { execFile } from "node:child_process";

const OWNER = "nickpclarke";
const HUB = `${OWNER}/AgentArmy`;
const SPOKES = [`${OWNER}/frontend-core`, `${OWNER}/backend-core`, `${OWNER}/middle-core`];
const REPOS = [HUB, ...SPOKES];

// Bot/agent comment authors worth calling out in the feed.
const AGENTS = ["claude", "github-actions", "gemini-code-assist", "copilot", "copilot-pull-request-reviewer"];
// Handles you can @-mention in a comment to pull an agent in.
const MENTIONABLE = ["@claude", "@gemini-code-assist", "@copilot"];

const ARGV = process.argv.slice(2);
const COLOR = process.stdout.isTTY && !ARGV.includes("--no-color");
const onlyRepo = (() => { const i = ARGV.indexOf("--repo"); return i >= 0 ? ARGV[i + 1] : null; })();
const onlyMentions = ARGV.includes("--mentions");
const LIMIT = (() => { const i = ARGV.indexOf("--limit"); return i >= 0 ? parseInt(ARGV[i + 1], 10) : 25; })();

const ansi = (c, s) => (COLOR ? `\x1b[${c}m${s}\x1b[0m` : s);
const dim = (s) => ansi("2", s), bold = (s) => ansi("1", s), cyan = (s) => ansi("36", s);
const green = (s) => ansi("32", s), yellow = (s) => ansi("33", s), magenta = (s) => ansi("35", s);

function gh(args) {
  return new Promise((resolve) => {
    execFile("gh", args, { timeout: 15000, windowsHide: true, maxBuffer: 16 * 1024 * 1024 }, (err, out) => {
      if (err) return resolve(null);
      try { resolve(JSON.parse(out)); } catch { resolve(null); }
    });
  });
}

const repoName = (full) => full.split("/")[1];
const numFromUrl = (u) => { const m = (u || "").match(/\/(?:issues|pull)\/(\d+)/); return m ? m[1] : "?"; };
const ago = (iso) => {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 3600) return `${Math.round(s / 60)}m`;
  if (s < 86400) return `${Math.round(s / 3600)}h`;
  return `${Math.round(s / 86400)}d`;
};
const snippet = (b) => (b || "").replace(/\s+/g, " ").trim().slice(0, 90);

async function repoComments(full) {
  // /issues/comments covers both issue and PR conversation comments.
  const data = await gh(["api", `repos/${full}/issues/comments?sort=created&direction=desc&per_page=15`]);
  if (!Array.isArray(data)) return { full, ok: false, items: [] };
  const items = data.map((c) => ({
    repo: repoName(full),
    num: numFromUrl(c.issue_url || c.html_url),
    author: c.user?.login || "?",
    body: c.body || "",
    url: c.html_url,
    at: c.created_at,
  }));
  return { full, ok: true, items };
}

async function openPrCounts(full) {
  const prs = await gh(["pr", "list", "--repo", full, "--state", "open", "--json", "number"]);
  return Array.isArray(prs) ? prs.length : null;
}

async function main() {
  const repos = onlyRepo ? REPOS.filter((r) => repoName(r) === onlyRepo) : REPOS;
  const [comments, prCounts] = await Promise.all([
    Promise.all(repos.map(repoComments)),
    Promise.all(repos.map(openPrCounts)),
  ]);

  let feed = comments.flatMap((r) => r.items);
  if (onlyMentions) feed = feed.filter((i) => /@(claude|gemini|copilot)/i.test(i.body));
  feed.sort((a, b) => new Date(b.at) - new Date(a.at));
  feed = feed.slice(0, LIMIT);

  const L = [];
  L.push("");
  L.push(bold(cyan("  AGENTARMY — PR/ISSUE COMMENT INBOX")) + dim(`   ${new Date().toISOString().slice(0, 16).replace("T", " ")}`));
  L.push("  " + dim("─".repeat(72)));
  // open-PR snapshot per repo
  const snap = repos.map((r, i) => `${repoName(r)} ${prCounts[i] == null ? dim("?") : yellow(prCounts[i] + " PR")}`).join("   ");
  L.push("  " + dim("open PRs: ") + snap);
  const unavailable = comments.filter((r) => !r.ok).map((r) => repoName(r.full));
  if (unavailable.length) L.push("  " + dim("unavailable: " + unavailable.join(", ")));
  L.push("");

  if (!feed.length) {
    L.push(dim("  no comments found"));
  } else {
    for (const i of feed) {
      const who = AGENTS.some((a) => i.author.toLowerCase().includes(a)) ? magenta(i.author) : green(i.author);
      const mention = /@(claude|gemini|copilot)/i.test(i.body) ? yellow(" @") : "";
      L.push(`  ${dim(ago(i.at).padStart(3))}  ${cyan((i.repo + " #" + i.num).padEnd(20))} ${who}${mention}`);
      L.push(`       ${dim(snippet(i.body))}`);
      L.push(`       ${dim(i.url)}`);
    }
  }
  L.push("");
  L.push("  " + dim("─".repeat(72)));
  L.push("  " + dim(`mention an agent in a reply: ${MENTIONABLE.join("  ")}   ·   --repo <name> · --mentions · --limit N`));
  L.push("");
  process.stdout.write(L.join("\n") + "\n");
}

main().catch((e) => process.stdout.write(`pr-inbox error: ${e?.message || e}\n`));
