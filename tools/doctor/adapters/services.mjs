import { existsSync } from 'node:fs'
import { join, relative } from 'node:path'
import { findServiceManifest, makeCheck, runCommand, slashPath, strictStatus, timedCheck } from '../core.mjs'

export function serviceChecksFor(kind) {
  return {
    name: kind,
    async run(context) {
      const found = findServiceManifest(context.repoRoot)
      if (!found) {
        return [makeCheck({
          id: `${kind}.manifest`,
          component: kind,
          status: strictStatus(context, 'skip'),
          severity: 'recommended',
          message: 'No service manifest found',
          evidence: {
            expected: ['agentarmy.services.json', '.agent/services.json'],
          },
        })]
      }

      const services = normalizeServices(found.manifest).filter((service) => service.kind === kind)
      if (!services.length) {
        return [makeCheck({
          id: `${kind}.declared`,
          component: kind,
          status: strictStatus(context, 'skip'),
          severity: 'recommended',
          message: `No ${kind} services declared`,
          evidence: { manifest: slashPath(relative(context.repoRoot, found.path)) },
        })]
      }

      const checks = [makeCheck({
        id: `${kind}.manifest`,
        component: kind,
        status: 'pass',
        severity: 'recommended',
        message: `${services.length} ${kind} service declaration(s) found`,
        evidence: { manifest: slashPath(relative(context.repoRoot, found.path)) },
      })]

      for (const service of services) {
        checks.push(...await runServiceChecks(context, service))
      }

      return checks
    },
  }
}

function normalizeServices(manifest) {
  if (Array.isArray(manifest.services)) return manifest.services
  return []
}

async function runServiceChecks(context, service) {
  const checks = []
  const serviceId = safeId(service.name || service.path || service.kind)
  const servicePath = service.path ? join(context.repoRoot, service.path) : context.repoRoot

  checks.push(makeCheck({
    id: `${service.kind}.${serviceId}.path`,
    component: service.kind,
    status: existsSync(servicePath) ? 'pass' : 'fail',
    severity: 'required',
    message: existsSync(servicePath) ? 'Service path exists' : 'Service path missing',
    evidence: { service: service.name, path: service.path || '.' },
  }))

  if (service.build) {
    checks.push(await timedCheck({
      id: `${service.kind}.${serviceId}.build`,
      component: service.kind,
      severity: service.required === false ? 'recommended' : 'required',
    }, async () => runScript(servicePath, service.build, `Build command for ${service.name || serviceId}`)))
  }

  if (service.test) {
    checks.push(await timedCheck({
      id: `${service.kind}.${serviceId}.test`,
      component: service.kind,
      severity: 'recommended',
    }, async () => runScript(servicePath, service.test, `Test command for ${service.name || serviceId}`)))
  }

  if (service.health_url) {
    checks.push(await timedCheck({
      id: `${service.kind}.${serviceId}.health`,
      component: service.kind,
      severity: service.required === false ? 'recommended' : 'required',
    }, async () => {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), context.timeoutMs)
      try {
        const response = await fetch(service.health_url, { signal: controller.signal })
        return {
          status: response.ok ? 'pass' : 'warn',
          message: response.ok ? 'Health URL responded' : `Health URL returned ${response.status}`,
          evidence: { url: service.health_url, http_status: response.status },
        }
      } catch (error) {
        return {
          status: service.required === false ? 'warn' : 'fail',
          message: `Health URL did not respond: ${error.message}`,
          evidence: { url: service.health_url },
        }
      } finally {
        clearTimeout(timeout)
      }
    }))
  }

  if (service.openapi) {
    const openApiPath = join(servicePath, service.openapi)
    checks.push(makeCheck({
      id: `${service.kind}.${serviceId}.openapi`,
      component: service.kind,
      status: existsSync(openApiPath) ? 'pass' : 'warn',
      severity: 'recommended',
      message: existsSync(openApiPath) ? 'OpenAPI contract found' : 'OpenAPI contract not found',
      evidence: { path: service.openapi },
    }))
  }

  return checks
}

function runScript(cwd, script, successMessage) {
  const [command, ...args] = splitCommand(script)
  const result = runCommand(command, args, { cwd, timeoutMs: 120000 })
  return {
    status: result.ok ? 'pass' : 'fail',
    message: result.ok ? successMessage : `Command failed: ${script}`,
    evidence: {
      command: script,
      output: result.output.slice(0, 1200),
    },
  }
}

function splitCommand(value) {
  return String(value).match(/(?:[^\s"]+|"[^"]*")+/g)?.map((part) => part.replace(/^"|"$/g, '')) || []
}

function safeId(value) {
  return String(value || 'service').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}
