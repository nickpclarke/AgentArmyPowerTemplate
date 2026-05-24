import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { fetchJson, makeCheck, strictStatus, timedCheck } from '../core.mjs'

export const arcadedbAdapter = {
  name: 'arcadedb',
  async run(context) {
    const url = normalizeUrl(context.env.ARCADEDB_URL || 'http://localhost:2480')
    const db = context.env.ARCADEDB_DATABASE || context.env.DB_NAME || 'knowledge'
    const user = context.env.ARCADEDB_USER || 'root'
    const password = context.env.ARCADEDB_PASSWORD || ''
    const authHeader = password
      ? { Authorization: `Basic ${Buffer.from(`${user}:${password}`).toString('base64')}` }
      : {}

    const checks = []

    checks.push(makeCheck({
      id: 'arcadedb.contract',
      component: 'arcadedb',
      status: existsSync(join(context.repoRoot, 'extensions', 'arcadedb-cockpit', 'BACKEND_CONTRACT.md')) ? 'pass' : 'warn',
      severity: 'recommended',
      message: 'ArcadeDB cockpit backend contract checked',
      evidence: { path: 'extensions/arcadedb-cockpit/BACKEND_CONTRACT.md' },
    }))

    checks.push(await timedCheck({
      id: 'arcadedb.health',
      component: 'arcadedb',
      severity: 'recommended',
    }, async () => {
      try {
        const response = await fetchJson(`${url}/api/v1/ready`, { timeoutMs: context.timeoutMs })
        return {
          status: response.ok || response.status === 204 ? 'pass' : strictStatus(context, 'warn'),
          message: response.ok || response.status === 204 ? 'ArcadeDB readiness endpoint responded' : `ArcadeDB readiness returned ${response.status}`,
          evidence: { url, http_status: response.status },
        }
      } catch (error) {
        return {
          status: strictStatus(context, 'skip'),
          message: `ArcadeDB is not reachable: ${error.message}`,
          evidence: { url },
        }
      }
    }))

    if (!password) {
      checks.push(makeCheck({
        id: 'arcadedb.credentials',
        component: 'arcadedb',
        status: strictStatus(context, 'skip'),
        severity: 'recommended',
        message: 'ARCADEDB_PASSWORD is not set; authenticated schema checks skipped',
        evidence: { env: 'ARCADEDB_PASSWORD' },
      }))
      return checks
    }

    checks.push(await timedCheck({
      id: 'arcadedb.databases',
      component: 'arcadedb',
      severity: 'recommended',
    }, async () => {
      const response = await fetchJson(`${url}/api/v1/databases`, {
        timeoutMs: context.timeoutMs,
        headers: authHeader,
      })
      const databases = Array.isArray(response.body?.result) ? response.body.result : []
      return {
        status: response.ok ? 'pass' : 'warn',
        message: response.ok ? 'Database list queried' : `Database list returned ${response.status}`,
        evidence: { url, databases, default_database: db },
      }
    }))

    for (const typeName of ['Chunk', 'StoredObject', 'IngestJob']) {
      checks.push(await timedCheck({
        id: `arcadedb.schema.${typeName.toLowerCase()}`,
        component: 'arcadedb',
        severity: 'informational',
      }, async () => {
        const response = await fetchJson(`${url}/api/v1/command/${encodeURIComponent(db)}`, {
          method: 'POST',
          timeoutMs: context.timeoutMs,
          headers: { ...authHeader, 'Content-Type': 'application/json' },
          body: JSON.stringify({ language: 'sql', command: `SELECT count(*) AS n FROM ${typeName}` }),
        })
        const count = Number(response.body?.result?.[0]?.n || 0)
        return {
          status: response.ok ? 'pass' : 'warn',
          message: response.ok ? `${typeName} count sampled` : `${typeName} sample unavailable`,
          evidence: { database: db, type: typeName, count },
        }
      }))
    }

    return checks
  },
}

function normalizeUrl(value) {
  return String(value).replace(/\/+$/, '')
}
