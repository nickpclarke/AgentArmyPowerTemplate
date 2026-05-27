// Thin wrapper around `git` for the fleet_deploy tool.
//
// Hard rules:
//   - All commands shell out to `git` with whitelisted argv (no `shell: true`).
//   - Read-only inspection (status, current-branch) before any mutating
//     operation. Refuses to proceed if the working tree is dirty.
//   - All operations bounded by a generous timeout.
//   - No support for arbitrary repo paths — caller passes a path that's
//     verified to exist + be a git repo before any operation runs.

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { existsSync } from "node:fs";
import path from "node:path";

const execFileP = promisify(execFile);
const GIT_TIMEOUT_MS = 90_000;

async function git(cwd, args) {
  return execFileP("git", args, { cwd, timeout: GIT_TIMEOUT_MS, maxBuffer: 4 * 1024 * 1024 });
}

export function assertGitRepo(repoPath) {
  if (!existsSync(repoPath)) throw new Error(`repo path does not exist: ${repoPath}`);
  if (!existsSync(path.join(repoPath, ".git"))) throw new Error(`not a git repo: ${repoPath}`);
}

export async function currentBranch(repoPath) {
  const { stdout } = await git(repoPath, ["rev-parse", "--abbrev-ref", "HEAD"]);
  return stdout.trim();
}

export async function workingTreeStatus(repoPath) {
  const { stdout } = await git(repoPath, ["status", "--porcelain"]);
  const lines = stdout.split("\n").filter(Boolean);
  return {
    clean: lines.length === 0,
    dirty_files: lines.slice(0, 20),  // sample if dirty
    dirty_count: lines.length,
  };
}

// Note: every caller-supplied argument below is also validated upstream
// against strict regexes (see BRANCH_RX / REMOTE_RX in tools.mjs). The `--`
// end-of-options sentinel here is defense-in-depth — if a future code path
// ever forgets to validate, the sentinel still prevents flag smuggling.

export async function fetchBranch(repoPath, remote, branch) {
  // `git fetch <remote> -- <refspec>` — modern git treats anything after
  // `--` as positional, even if it starts with `-`.
  const { stdout, stderr } = await git(repoPath, ["fetch", remote, "--", branch]);
  return { stdout: stdout.trim(), stderr: stderr.trim() };
}

export async function checkoutBranch(repoPath, branch) {
  // `git checkout <ref> --` separates the ref from any pathspec filter.
  // (`git checkout -- <ref>` would treat ref as a path — wrong shape.)
  // The branch never starts with `-` thanks to the upstream regex.
  const { stdout, stderr } = await git(repoPath, ["checkout", branch, "--"]);
  return { stdout: stdout.trim(), stderr: stderr.trim() };
}

export async function fastForward(repoPath, remote, branch) {
  // After checkout, pull --ff-only ensures we land on the latest. Refuses to
  // merge — if the branch has diverged from remote, the operator must resolve
  // it manually rather than the deploy doing something subtle.
  // `--` sentinel separates the branch refspec from option parsing.
  const { stdout, stderr } = await git(repoPath, ["pull", "--ff-only", remote, "--", branch]);
  return { stdout: stdout.trim(), stderr: stderr.trim() };
}

export async function currentSha(repoPath) {
  const { stdout } = await git(repoPath, ["rev-parse", "HEAD"]);
  return stdout.trim();
}

export async function shortLog(repoPath, count = 5) {
  const { stdout } = await git(repoPath, [
    "log", `-n${count}`, "--pretty=format:%h %s", "--no-color",
  ]);
  return stdout.split("\n").filter(Boolean);
}
