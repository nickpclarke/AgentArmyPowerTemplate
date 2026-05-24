import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'
import { performance } from 'node:perf_hooks'

export const STATUS_RANK = {
  pass: 0,
  skip: 1,
  warn: 2,
  fail: 3,
  error: 4,
}

export function createContext(options = {}) {
  const repoRoot = options.repoRoot || resolve(process.cwd())
  return {
    repoRoot,
    startedAt: new Date(),
    runId: options.runId || `${new Date().toISOString().replace(/[:.]/g, '-')}-local`,
    strict: Boolean(options.strict),
    timeoutMs: Number(options.timeoutMs || process.env.AGENTARMY_DOCTOR_TIMEOUT_MS || 3500),
    env: process.env,
  }
}

export function makeCheck(input) {
  return {
    id: input.id,
    component: input.component,
    status: input.status,
    severity: input.severity || 'recommended',
    duration_ms: Math.max(0, Math.round(input.duration_ms || 0)),
    message: input.message || '',
    evidence: redact(input.evidence || {}),
    redactions: input.redactions || [],
  }
}

export async function timedCheck(input, fn) {
  const started = performance.now()
  try {
    const result = await fn()
    return makeCheck({
      ...input,
      ...result,
      duration_ms: performance.now() - started,
    })
  } catch (error) {
    return makeCheck({
      ...input,
      status: 'error',
      message: error.message || String(error),
      duration_ms: performance.now() - started,
    })
  }
}

export function summarize(checks) {
  const summary = { pass: 0, warn: 0, fail: 0, skip: 0, error: 0 }
  for (const check of checks) {
    summary[check.status] = (summary[check.status] || 0) + 1
  }
  let status = 'pass'
  if (summary.error > 0) status = 'error'
  else if (summary.fail > 0) status = 'fail'
  else if (summary.warn > 0) status = 'warn'
  else if (summary.pass === 0 && summary.skip > 0) status = 'skip'
  return { summary, status }
}

export function buildEnvelope(context, checks, artifacts = []) {
  const { summary, status } = summarize(checks)
  return {
    schema_version: 'doctor.v1',
    run_id: context.runId,
    generated_at: new Date().toISOString(),
    scope: context.strict ? 'strict' : 'local',
    status,
    summary,
    checks,
    artifacts,
  }
}

export function writeArtifact(repoRoot, outputPath, contents) {
  const absolutePath = resolve(repoRoot, outputPath)
  mkdirSync(resolve(absolutePath, '..'), { recursive: true })
  writeFileSync(absolutePath, contents, 'utf8')
  return {
    kind: outputPath.endsWith('.md') ? 'markdown' : outputPath.endsWith('.json') ? 'json' : 'text',
    path: slashPath(relative(repoRoot, absolutePath)),
  }
}

export function commandExists(command, args = ['--version']) {
  try {
    const output = execFileSync(command, args, {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 3000,
    })
    return { ok: true, output: output.trim() }
  } catch (error) {
    return {
      ok: false,
      output: String(error.stderr || error.message || error).trim(),
    }
  }
}

export function runCommand(command, args = [], options = {}) {
  try {
    const output = execFileSync(command, args, {
      cwd: options.cwd,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: options.timeoutMs || 5000,
      env: options.env || process.env,
    })
    return { ok: true, output: output.trim() }
  } catch (error) {
    return {
      ok: false,
      output: String(error.stdout || error.stderr || error.message || error).trim(),
      code: error.status,
    }
  }
}

export function readJsonIfExists(path) {
  if (!existsSync(path)) return null
  return JSON.parse(readFileSync(path, 'utf8'))
}

export function findServiceManifest(repoRoot) {
  const candidates = [
    join(repoRoot, 'agentarmy.services.json'),
    join(repoRoot, '.agent', 'services.json'),
  ]
  for (const candidate of candidates) {
    const parsed = readJsonIfExists(candidate)
    if (parsed) return { path: candidate, manifest: parsed }
  }
  return null
}

export function slashPath(value) {
  return value.replace(/\\/g, '/')
}

export function redact(value) {
  if (typeof value === 'string') return redactString(value)
  if (Array.isArray(value)) return value.map((item) => redact(item))
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => {
      if (/password|secret|token|key|credential/i.test(key)) return [key, '[redacted]']
      return [key, redact(item)]
    }))
  }
  return value
}

export function redactString(value) {
  return String(value)
    .replace(/(https?:\/\/)[^/\s@]+@/g, '$1[redacted]@')
    .replace(/(password|secret|token|key|credential)=([^&\s]+)/gi, '$1=[redacted]')
    .replace(/(sk-[A-Za-z0-9_-]{8,})/g, '[redacted-key]')
}

export function strictStatus(context, defaultStatus = 'skip') {
  return context.strict ? 'fail' : defaultStatus
}

export async function fetchJson(url, options = {}) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), options.timeoutMs || 3500)
  try {
    const response = await fetch(url, {
      method: options.method || 'GET',
      headers: options.headers || {},
      body: options.body,
      signal: controller.signal,
    })
    const body = await response.json().catch(() => ({}))
    return { ok: response.ok, status: response.status, body }
  } finally {
    clearTimeout(timeout)
  }
}
