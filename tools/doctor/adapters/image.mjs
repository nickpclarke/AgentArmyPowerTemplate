import { existsSync, readFileSync } from 'node:fs'
import { isAbsolute, join, resolve } from 'node:path'
import { fetchJson, makeCheck, strictStatus, timedCheck } from '../core.mjs'

// Factory: `node tools/agentarmy-doctor.mjs image <dir>` builds one of these for
// the image directory holding an image.json (the AgentArmy Image Standard).
// It validates the manifest's load-bearing rules, confirms the declared
// artifacts exist, and probes each service's healthcheck on its host port.
// The heavy "prove the running image" work is the image's own doctor.cmd
// (e.g. scripts/dbos-doctor.sh); this adapter checks conformance + readiness.
export function imageAdapter(dir) {
  const baseDir = resolve(process.cwd(), dir || '.')
  return {
    name: 'image',
    async run(context) {
      const checks = []
      const manifestPath = join(baseDir, 'image.json')

      if (!existsSync(manifestPath)) {
        checks.push(makeCheck({
          id: 'image.manifest',
          component: 'image',
          status: 'fail',
          severity: 'required',
          message: `No image.json found in ${dir}`,
          evidence: { path: manifestPath },
        }))
        return checks
      }

      let manifest
      try {
        manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))
      } catch (error) {
        checks.push(makeCheck({
          id: 'image.manifest',
          component: 'image',
          status: 'fail',
          severity: 'required',
          message: `image.json does not parse: ${error.message}`,
          evidence: { path: manifestPath },
        }))
        return checks
      }

      const name = typeof manifest.name === 'string' ? manifest.name : '(unnamed)'
      checks.push(makeCheck({
        id: 'image.manifest',
        component: 'image',
        status: 'pass',
        severity: 'required',
        message: `Loaded image.json for "${name}"`,
        evidence: { path: manifestPath, kind: manifest.kind },
      }))

      // ---- schema conformance (load-bearing rules; schema is canonical) ----
      const errors = validateManifest(manifest)
      checks.push(makeCheck({
        id: 'image.schema',
        component: 'image',
        status: errors.length ? 'fail' : 'pass',
        severity: 'required',
        message: errors.length
          ? `image.json violates the Image Standard (${errors.length}): ${errors.join('; ')}`
          : 'image.json conforms to the Image Standard',
        evidence: { schema: 'templates/image-schema.json', errors },
      }))

      // ---- declared artifacts exist ------------------------------------------
      const missing = []
      const present = []
      for (const rel of declaredArtifacts(manifest)) {
        const abs = isAbsolute(rel) ? rel : join(baseDir, rel)
        if (existsSync(abs)) present.push(rel)
        else missing.push(rel)
      }
      checks.push(makeCheck({
        id: 'image.artifacts',
        component: 'image',
        status: missing.length ? strictStatus(context, 'warn') : 'pass',
        severity: 'recommended',
        message: missing.length
          ? `Declared artifacts missing: ${missing.join(', ')}`
          : `All ${present.length} declared artifacts present`,
        evidence: { present, missing },
      }))

      // ---- interface contracts (contract-first applied to images) ------------
      const contracts = Array.isArray(manifest.contract) ? manifest.contract : []
      const exposesHttp = (Array.isArray(manifest.services) ? manifest.services : []).filter(
        (s) => s.healthcheck?.http || /\b(api|bff|gateway)\b/.test(String(s.role || '')),
      )
      if (exposesHttp.length && !contracts.length) {
        checks.push(makeCheck({
          id: 'image.contract',
          component: 'image',
          status: strictStatus(context, 'warn'),
          severity: 'recommended',
          message: `Exposes an HTTP interface (${exposesHttp.map((s) => s.name).join(', ')}) but declares no contract[] — contract-first`,
          evidence: { services: exposesHttp.map((s) => s.name), registry: 'docs/contracts.md' },
        }))
      } else if (contracts.length) {
        const missingSpecs = []
        for (const c of contracts) {
          const fileKind = ['openapi', 'asyncapi', 'graphql', 'grpc'].includes(c.type)
          const isPath = c.spec && !/^https?:\/\//.test(c.spec)
          if (fileKind && isPath) {
            const abs = isAbsolute(c.spec) ? c.spec : join(baseDir, c.spec)
            if (!existsSync(abs)) missingSpecs.push(c.spec)
          }
        }
        checks.push(makeCheck({
          id: 'image.contract',
          component: 'image',
          status: missingSpecs.length ? strictStatus(context, 'warn') : 'pass',
          severity: 'recommended',
          message: missingSpecs.length
            ? `Contract spec(s) missing: ${missingSpecs.join(', ')}`
            : `${contracts.length} interface contract(s) declared`,
          evidence: {
            contracts: contracts.map((c) => ({ service: c.service, type: c.type, spec: c.spec, registry: c.registry })),
            missing: missingSpecs,
          },
        }))
      }

      // ---- per-service healthcheck probes (best-effort) ----------------------
      for (const service of Array.isArray(manifest.services) ? manifest.services : []) {
        const hc = service.healthcheck
        if (!hc || !hc.http) continue
        const hostPort = firstHostPort(service.ports)
        const url = toUrl(hc.http, hostPort)
        const expect = Number.isInteger(hc.expect) ? hc.expect : 200
        checks.push(await timedCheck({
          id: `image.health.${service.name}`,
          component: 'image',
          severity: 'recommended',
        }, async () => {
          try {
            const response = await fetchJson(url, { timeoutMs: context.timeoutMs })
            const ok = response.status === expect || (expect === 200 && response.ok)
            return {
              status: ok ? 'pass' : strictStatus(context, 'warn'),
              message: ok
                ? `${service.name} healthy at ${hc.http} (${response.status})`
                : `${service.name} readiness returned ${response.status}, expected ${expect}`,
              evidence: { url, http_status: response.status, expect },
            }
          } catch (error) {
            return {
              status: strictStatus(context, 'skip'),
              message: `${service.name} not reachable (stack down?): ${error.message}`,
              evidence: { url },
            }
          }
        }))
      }

      return checks
    },
  }
}

// Minimal validator for the standard's load-bearing rules. The canonical
// contract is templates/image-schema.json; this enforces the parts the doctor
// depends on without pulling in a JSON-Schema engine.
function validateManifest(m) {
  const errors = []
  for (const key of ['name', 'kind', 'base', 'services', 'doctor']) {
    if (m[key] === undefined) errors.push(`missing required field: ${key}`)
  }
  if (m.kind && !['single', 'app+db', 'multi-service'].includes(m.kind)) {
    errors.push(`kind must be single | app+db | multi-service (got "${m.kind}")`)
  }
  if (m.name && !/^[a-z][a-z0-9-]{1,63}$/.test(m.name)) {
    errors.push(`name must be kebab-case (got "${m.name}")`)
  }
  if (m.services !== undefined) {
    if (!Array.isArray(m.services) || m.services.length === 0) {
      errors.push('services must be a non-empty array')
    } else {
      m.services.forEach((s, i) => {
        if (!s || typeof s !== 'object') { errors.push(`services[${i}] must be an object`); return }
        if (!s.name) errors.push(`services[${i}] missing name`)
        if (!s.image && !s.build) errors.push(`services[${s.name || i}] must set image or build`)
        if (s.image && s.build) errors.push(`services[${s.name || i}] sets both image and build`)
        if (s.healthcheck && !s.healthcheck.http && !s.healthcheck.cmd) {
          errors.push(`services[${s.name || i}].healthcheck needs http or cmd`)
        }
      })
    }
  }
  if (m.doctor !== undefined && !m.doctor.cmd) errors.push('doctor.cmd is required')
  if (Array.isArray(m.secrets)) {
    m.secrets.forEach((s, i) => { if (!s || !s.name) errors.push(`secrets[${i}] missing name`) })
  }
  if (m.deploy && m.deploy.target && !['aca', 'cloud-run', 'k8s', 'none'].includes(m.deploy.target)) {
    errors.push(`deploy.target must be aca | cloud-run | k8s | none (got "${m.deploy.target}")`)
  }
  return errors
}

// Files the manifest claims should exist, resolved relative to the image dir.
function declaredArtifacts(m) {
  const paths = []
  if (m.setup?.sh) paths.push(m.setup.sh)
  if (m.setup?.ps1) paths.push(m.setup.ps1)
  if (m.doctor?.cmd) {
    const token = scriptToken(m.doctor.cmd)
    if (token) paths.push(token)
  }
  if (m.deploy?.bicep) paths.push(m.deploy.bicep)
  for (const s of Array.isArray(m.services) ? m.services : []) {
    if (s.build) paths.push(s.build)
  }
  for (const b of Array.isArray(m.baked) ? m.baked : []) {
    if (b?.path) paths.push(b.path)
  }
  return [...new Set(paths)]
}

// Pull the script path out of a doctor.cmd. Handles "scripts/x.sh ..." and
// "node ../../tools/agentarmy-doctor.mjs arcadedb". Returns null for bare
// interpreter words we can't resolve to a file.
function scriptToken(cmd) {
  const tokens = String(cmd).trim().split(/\s+/)
  if (!tokens.length) return null
  const interpreters = new Set(['node', 'python', 'python3', 'sh', 'bash', 'pwsh'])
  const candidate = interpreters.has(tokens[0]) ? tokens[1] : tokens[0]
  if (!candidate) return null
  return candidate.includes('/') || candidate.includes('\\') || /\.\w+$/.test(candidate) ? candidate : null
}

function firstHostPort(ports) {
  if (!Array.isArray(ports) || !ports.length) return null
  const map = String(ports[0])
  return map.includes(':') ? map.split(':')[0] : map
}

function toUrl(http, hostPort) {
  if (/^https?:\/\//.test(http)) return http
  const port = hostPort || '80'
  const path = http.startsWith('/') ? http : `/${http}`
  return `http://localhost:${port}${path}`
}
