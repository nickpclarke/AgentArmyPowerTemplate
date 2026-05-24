import { createServer } from 'node:http'
import { readFile, readFileSync } from 'node:fs'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
loadEnv(path.join(__dirname, '.env'))

const PORT = Number(process.env.PORT || 8787)
const HOST = process.env.HOST || '127.0.0.1'
const ARCADEDB_URL = (process.env.ARCADEDB_URL || 'http://localhost:2480').replace(/\/+$/, '')
const ARCADEDB_USER = process.env.ARCADEDB_USER || 'root'
const ARCADEDB_PASSWORD_RESULT = readArcadeDbPassword(process.env)
const ARCADEDB_PASSWORD = ARCADEDB_PASSWORD_RESULT.value
const DEFAULT_DB = process.env.ARCADEDB_DATABASE || process.env.DB_NAME || 'knowledge'
const ALLOW_MUTATION = String(process.env.ARCADEDB_ALLOW_MUTATION || 'false').toLowerCase() === 'true'
const MAX_JSON_BODY_BYTES = Number(process.env.COCKPIT_MAX_JSON_BODY_BYTES || 1_000_000)
const PUBLIC_DIR = path.join(__dirname, 'public')
const REPO_ROOT = path.resolve(__dirname, '..', '..')
const DOCTOR_ARTIFACT = path.join(REPO_ROOT, 'tests', 'artifacts', 'doctor', 'latest.json')
const RECENT_LIMIT = 18

if (ARCADEDB_PASSWORD_RESULT.error) {
  console.error('ARCADEDB_PASSWORD_FILE could not be read. Check the mounted secret path and file permissions.')
  process.exit(1)
}

if (!ARCADEDB_PASSWORD) {
  console.error('ArcadeDB password is required. Set ARCADEDB_PASSWORD_FILE to a mounted secret file, or set ARCADEDB_PASSWORD from a runtime secret.')
  process.exit(1)
}

const telemetry = {
  startedAt: new Date().toISOString(),
  probes: [],
  commands: [],
}

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`)
    if (url.pathname.startsWith('/api/')) {
      await routeApi(req, res, url)
      return
    }
    await serveStatic(res, url.pathname)
  } catch (error) {
    const status = Number(error.statusCode || 500)
    sendJson(res, status, problem(status === 413 ? 'Payload too large' : 'Cockpit server error', error))
  }
})

server.listen(PORT, HOST, () => {
  console.log(`Arcade Cockpit listening at http://${HOST}:${PORT}`)
  console.log(`ArcadeDB target: ${ARCADEDB_URL} db=${DEFAULT_DB}`)
  console.log(`ArcadeDB credential source: ${ARCADEDB_PASSWORD_RESULT.source}`)
})

async function routeApi(req, res, url) {
  if (req.method === 'GET' && url.pathname === '/api/config') {
    sendJson(res, 200, {
      target: ARCADEDB_URL,
      defaultDatabase: DEFAULT_DB,
      mutationEnabled: ALLOW_MUTATION,
      startedAt: telemetry.startedAt,
    })
    return
  }

  if (req.method === 'GET' && url.pathname === '/api/health') {
    sendJson(res, 200, await healthProbe())
    return
  }

  if (req.method === 'GET' && url.pathname === '/api/databases') {
    sendJson(res, 200, { databases: await listDatabases() })
    return
  }

  if (req.method === 'GET' && url.pathname === '/api/graph') {
    const db = cleanDb(url.searchParams.get('db') || DEFAULT_DB)
    sendJson(res, 200, await graphSnapshot(db))
    return
  }

  if (req.method === 'GET' && url.pathname === '/api/schema') {
    const db = cleanDb(url.searchParams.get('db') || DEFAULT_DB)
    sendJson(res, 200, await schemaSnapshot(db))
    return
  }

  if (req.method === 'GET' && url.pathname === '/api/telemetry') {
    sendJson(res, 200, telemetrySnapshot())
    return
  }

  if (req.method === 'GET' && url.pathname === '/api/doctor') {
    sendJson(res, 200, doctorSnapshot())
    return
  }

  if (req.method === 'POST' && url.pathname === '/api/query') {
    const body = await readJson(req)
    const db = cleanDb(body.db || DEFAULT_DB)
    const sql = String(body.sql || '').trim()
    if (!sql) {
      sendJson(res, 400, problem('SQL is required'))
      return
    }
    if (!ALLOW_MUTATION && !isReadOnlySql(sql)) {
      sendJson(res, 403, problem('Read-only mode is enabled', 'Set ARCADEDB_ALLOW_MUTATION=true to allow mutating SQL.'))
      return
    }
    const result = await timedCommand(db, sql, body.params || undefined, 'query-console')
    sendJson(res, 200, result)
    return
  }

  sendJson(res, 404, problem('Unknown cockpit endpoint'))
}

async function healthProbe() {
  const started = performance.now()
  const status = {
    ok: false,
    ready: false,
    databases: [],
    latencyMs: 0,
    target: ARCADEDB_URL,
    checkedAt: new Date().toISOString(),
    error: null,
  }
  try {
    const ready = await arcadeFetch('/api/v1/ready', { method: 'GET' })
    status.ready = ready.status === 200 || ready.status === 204
    status.databases = await listDatabases()
    status.ok = status.ready
  } catch (error) {
    status.error = String(error.message || error)
  }
  status.latencyMs = Math.round(performance.now() - started)
  pushLimited(telemetry.probes, status)
  return status
}

async function listDatabases() {
  const response = await arcadeFetch('/api/v1/databases', { method: 'GET' })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.error || body.detail || response.statusText)
  return Array.isArray(body.result) ? body.result : []
}

async function graphSnapshot(db) {
  const [sources, chunks, jobs, stats, schema] = await Promise.all([
    safeCommand(db, 'SELECT source, source_id, kind, count(*) AS chunk_count FROM Chunk GROUP BY source_id, source, kind'),
    safeCommand(db, 'SELECT @rid AS id, source, source_id, kind, chunk_index, content FROM Chunk LIMIT 120'),
    safeCommand(db, 'SELECT @rid AS id, job_id, source, source_id, kind, status, chunks_ingested, updated_at FROM IngestJob ORDER BY updated_at DESC LIMIT 80'),
    statsSnapshot(db),
    schemaSnapshot(db),
  ])

  const nodes = new Map()
  const edges = []
  const addNode = (id, patch) => nodes.set(id, { ...(nodes.get(id) || {}), id, ...patch })
  const addEdge = (from, to, type, weight = 1) => edges.push({ from, to, type, weight })

  addNode(`db:${db}`, { label: db, type: 'database', tone: 'cyan', size: 22, meta: stats })

  for (const type of schema.types) {
    addNode(`type:${type.name}`, {
      label: type.name,
      type: 'type',
      tone: type.name === 'Chunk' ? 'lime' : type.name === 'IngestJob' ? 'magenta' : 'cyan',
      size: 13 + Math.min(18, Math.sqrt(type.count || 0) * 3),
      meta: type,
    })
    addEdge(`db:${db}`, `type:${type.name}`, 'contains', 0.7)
  }

  for (const source of sources.rows) {
    const sourceId = source.source_id || source.source || 'unknown-source'
    addNode(`source:${sourceId}`, {
      label: source.source || sourceId,
      type: 'source',
      tone: source.kind === 'image' ? 'magenta' : 'lime',
      size: 12 + Math.min(20, Number(source.chunk_count || 1)),
      meta: source,
    })
    addEdge('type:Chunk', `source:${sourceId}`, 'groups', 0.9)
  }

  for (const chunk of chunks.rows) {
    const id = `chunk:${chunk.id || chunk['@rid'] || `${chunk.source_id}:${chunk.chunk_index}`}`
    const sourceId = chunk.source_id || chunk.source || 'unknown-source'
    addNode(id, {
      label: chunk.kind === 'image' ? chunk.source || 'image' : shortText(chunk.content || chunk.source || 'chunk', 42),
      type: 'chunk',
      tone: chunk.kind === 'image' ? 'magenta' : 'lime',
      size: 6,
      meta: chunk,
    })
    addEdge(`source:${sourceId}`, id, 'chunks', 0.45)
  }

  for (const job of jobs.rows) {
    const id = `job:${job.job_id || job.id || job.source_id}`
    const sourceId = job.source_id || job.source || 'unknown-source'
    addNode(id, {
      label: `${job.status || 'job'}: ${job.source || sourceId}`,
      type: 'job',
      tone: job.status === 'failed' ? 'red' : job.status === 'done' ? 'cyan' : 'magenta',
      size: 9,
      meta: job,
    })
    addEdge('type:IngestJob', id, 'tracks', 0.6)
    addEdge(id, `source:${sourceId}`, 'landed', 0.4)
  }

  return {
    database: db,
    generatedAt: new Date().toISOString(),
    stats,
    nodes: [...nodes.values()],
    edges,
    warnings: [...sources.warnings, ...chunks.warnings, ...jobs.warnings, ...schema.warnings],
  }
}

async function schemaSnapshot(db) {
  const candidates = ['Chunk', 'StoredObject', 'IngestJob']
  const types = []
  const warnings = []
  for (const name of candidates) {
    const countResult = await safeCommand(db, `SELECT count(*) AS n FROM ${name}`)
    const sampleResult = await safeCommand(db, `SELECT FROM ${name} LIMIT 5`)
    if (countResult.ok || sampleResult.ok) {
      types.push({
        name,
        count: Number(countResult.rows[0]?.n || 0),
        sample: sampleResult.rows,
        fields: fieldInventory(sampleResult.rows),
      })
    } else {
      warnings.push(`${name}: ${countResult.error || sampleResult.error}`)
    }
  }
  return { database: db, types, warnings }
}

async function statsSnapshot(db) {
  const chunkCount = await safeCount(db, 'Chunk')
  const objectCount = await safeCount(db, 'StoredObject')
  const jobCount = await safeCount(db, 'IngestJob')
  const images = await safeCommand(db, "SELECT count(*) AS n FROM Chunk WHERE kind = 'image'")
  const sources = await safeCommand(db, 'SELECT source_id FROM Chunk GROUP BY source_id')
  return {
    chunks: chunkCount,
    objects: objectCount,
    jobs: jobCount,
    images: Number(images.rows[0]?.n || 0),
    sources: sources.rows.length,
    recentCommands: telemetry.commands.length,
  }
}

async function safeCount(db, type) {
  const result = await safeCommand(db, `SELECT count(*) AS n FROM ${type}`)
  return Number(result.rows[0]?.n || 0)
}

async function safeCommand(db, sql, params) {
  try {
    const result = await timedCommand(db, sql, params, 'cockpit-sampler', false)
    return { ok: true, rows: result.rows, elapsedMs: result.elapsedMs, warnings: [] }
  } catch (error) {
    return { ok: false, rows: [], error: String(error.message || error), warnings: [String(error.message || error)] }
  }
}

async function timedCommand(db, sql, params, label, record = true) {
  const started = performance.now()
  const response = await arcadeFetch(`/api/v1/command/${encodeURIComponent(db)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language: 'sql', command: sql, ...(params ? { params } : {}) }),
  })
  const body = await response.json().catch(() => ({}))
  const elapsedMs = Math.round(performance.now() - started)
  if (!response.ok) {
    throw new Error(body.detail || body.error || response.statusText)
  }
  const rows = Array.isArray(body.result) ? body.result : []
  if (record) {
    pushLimited(telemetry.commands, {
      label,
      db,
      sql,
      rows: rows.length,
      elapsedMs,
      at: new Date().toISOString(),
      readOnly: isReadOnlySql(sql),
    })
  }
  return { db, sql, rows, elapsedMs, at: new Date().toISOString() }
}

async function arcadeFetch(apiPath, options = {}) {
  const token = Buffer.from(`${ARCADEDB_USER}:${ARCADEDB_PASSWORD}`).toString('base64')
  return fetch(`${ARCADEDB_URL}${apiPath}`, {
    ...options,
    headers: {
      Authorization: `Basic ${token}`,
      ...(options.headers || {}),
    },
  })
}

function telemetrySnapshot() {
  const lastProbe = telemetry.probes.at(-1) || null
  const latencies = telemetry.commands.map((item) => item.elapsedMs)
  const avg = latencies.length ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : 0
  return {
    startedAt: telemetry.startedAt,
    lastProbe,
    averageCommandMs: avg,
    probes: telemetry.probes,
    commands: telemetry.commands,
  }
}

function doctorSnapshot() {
  if (!existsSync(DOCTOR_ARTIFACT)) {
    return {
      available: false,
      status: 'skip',
      message: 'No doctor artifact found. Run node tools/agentarmy-doctor.mjs --write-artifacts from the repo root.',
      artifact: path.relative(REPO_ROOT, DOCTOR_ARTIFACT).replace(/\\/g, '/'),
    }
  }
  try {
    const artifact = JSON.parse(readFileSync(DOCTOR_ARTIFACT, 'utf8'))
    return {
      available: true,
      status: artifact.status || 'warn',
      generatedAt: artifact.generated_at || null,
      summary: artifact.summary || {},
      artifact: path.relative(REPO_ROOT, DOCTOR_ARTIFACT).replace(/\\/g, '/'),
      checks: Array.isArray(artifact.checks) ? artifact.checks.slice(0, 12) : [],
    }
  } catch (error) {
    return {
      available: false,
      status: 'error',
      message: `Doctor artifact could not be parsed: ${error.message}`,
      artifact: path.relative(REPO_ROOT, DOCTOR_ARTIFACT).replace(/\\/g, '/'),
    }
  }
}

async function serveStatic(res, pathname) {
  const cleanPath = pathname === '/' ? '/index.html' : pathname
  const filePath = path.normalize(path.join(PUBLIC_DIR, cleanPath))
  if (!filePath.startsWith(PUBLIC_DIR) || !existsSync(filePath)) {
    sendJson(res, 404, problem('Not found'))
    return
  }
  const ext = path.extname(filePath)
  let body = await readFilePromise(filePath)
  if (cleanPath === '/index.html') {
    body = await injectBootstrap(body)
  }
  res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' })
  res.end(body)
}

async function injectBootstrap(body) {
  const text = body.toString('utf8')
  const config = {
    target: ARCADEDB_URL,
    defaultDatabase: DEFAULT_DB,
    mutationEnabled: ALLOW_MUTATION,
    startedAt: telemetry.startedAt,
  }
  let graph = null
  let health = null
  try {
    health = await healthProbe()
    graph = health.ready ? await graphSnapshot(DEFAULT_DB) : null
  } catch (error) {
    health = { ok: false, ready: false, error: String(error.message || error), target: ARCADEDB_URL }
  }
  const doctor = doctorSnapshot()
  const bootstrap = `<script>window.__ARCADE_BOOTSTRAP__ = ${JSON.stringify({ config, graph, health, doctor }).replace(/</g, '\\u003c')}</script>`
  return text.replace('    <script type="module" src="/app.js"></script>', `    ${bootstrap}\n    <script type="module" src="/app.js"></script>`)
}

function readFilePromise(filePath) {
  return new Promise((resolve, reject) => {
    readFile(filePath, (error, data) => {
      if (error) reject(error)
      else resolve(data)
    })
  })
}

async function readJson(req) {
  const chunks = []
  let size = 0
  for await (const chunk of req) {
    size += chunk.length
    if (size > MAX_JSON_BODY_BYTES) {
      const error = new Error(`JSON body exceeds ${MAX_JSON_BODY_BYTES} bytes`)
      error.statusCode = 413
      throw error
    }
    chunks.push(chunk)
  }
  const text = Buffer.concat(chunks).toString('utf8')
  return text ? JSON.parse(text) : {}
}

function sendJson(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' })
  res.end(JSON.stringify(body))
}

function problem(title, detail = null) {
  return { error: title, detail: detail ? String(detail) : null }
}

function cleanDb(value) {
  const db = String(value || DEFAULT_DB).trim()
  if (!/^[A-Za-z0-9_-]+$/.test(db)) throw new Error('Invalid database name')
  return db
}

function isReadOnlySql(sql) {
  const candidate = String(sql || '').trim()
  if (!candidate) return false
  const normalized = candidate.replace(/'(?:''|[^'])*'|"(?:\"\"|[^"])*"/g, "''")
  if (/;|--|\/\*|\*\/|#/.test(normalized)) return false
  return /^(select|match|traverse|explain)\b/i.test(normalized)
    && !/\b(insert|update|delete|create|drop|alter|truncate|upsert|move|grant|revoke|begin|commit|rollback)\b/i.test(normalized)
}

function fieldInventory(rows) {
  const fields = new Set()
  for (const row of rows) {
    for (const key of Object.keys(row || {})) fields.add(key)
  }
  return [...fields].sort()
}

function shortText(value, length) {
  const text = String(value).replace(/\s+/g, ' ').trim()
  return text.length > length ? `${text.slice(0, length - 1)}...` : text
}

function pushLimited(list, item) {
  list.push(item)
  while (list.length > RECENT_LIMIT) list.shift()
}

function loadEnv(filePath) {
  if (!existsSync(filePath)) return
  const text = readFileSync(filePath, 'utf8')
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const index = trimmed.indexOf('=')
    if (index < 1) continue
    const key = trimmed.slice(0, index).trim()
    const value = trimmed.slice(index + 1).trim().replace(/^["']|["']$/g, '')
    if (!process.env[key]) process.env[key] = value
  }
}

function readArcadeDbPassword(env) {
  const filePath = String(env.ARCADEDB_PASSWORD_FILE || '').trim()
  if (filePath) {
    try {
      return {
        value: readFileSync(filePath, 'utf8').trim(),
        source: 'ARCADEDB_PASSWORD_FILE',
        error: null,
      }
    } catch (error) {
      return {
        value: '',
        source: 'ARCADEDB_PASSWORD_FILE',
        error: error.message,
      }
    }
  }

  const value = env.ARCADEDB_PASSWORD || ''
  return {
    value,
    source: value ? 'ARCADEDB_PASSWORD' : 'unset',
    error: null,
  }
}
