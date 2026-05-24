import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { commandExists, makeCheck, runCommand, strictStatus, timedCheck } from '../core.mjs'

export const containersAdapter = {
  name: 'containers',
  async run(context) {
    const checks = []
    const docker = commandExists('docker', ['--version'])
    checks.push(makeCheck({
      id: 'containers.docker-cli',
      component: 'containers',
      status: docker.ok ? 'pass' : strictStatus(context, 'skip'),
      severity: 'recommended',
      message: docker.ok ? 'Docker CLI is available' : 'Docker CLI is not available',
      evidence: { version: docker.output.split(/\r?\n/)[0] || null },
    }))

    if (!docker.ok) return checks

    checks.push(await timedCheck({
      id: 'containers.docker-engine',
      component: 'containers',
      severity: 'recommended',
    }, async () => {
      const result = runCommand('docker', ['info', '--format', '{{json .ServerVersion}}'], { timeoutMs: context.timeoutMs })
      return {
        status: result.ok ? 'pass' : strictStatus(context, 'warn'),
        message: result.ok ? 'Docker engine responded' : 'Docker engine is not reachable',
        evidence: { server_version: result.output.replace(/^"|"$/g, '') || null },
      }
    }))

    const composeFiles = ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']
      .filter((file) => existsSync(join(context.repoRoot, file)))

    checks.push(makeCheck({
      id: 'containers.compose-file',
      component: 'containers',
      status: composeFiles.length ? 'pass' : 'skip',
      severity: 'recommended',
      message: composeFiles.length ? 'Compose file found' : 'No compose file found',
      evidence: { files: composeFiles },
    }))

    if (composeFiles.length) {
      checks.push(await timedCheck({
        id: 'containers.compose-ps',
        component: 'containers',
        severity: 'recommended',
      }, async () => {
        const result = runCommand('docker', ['compose', 'ps', '--format', 'json'], {
          cwd: context.repoRoot,
          timeoutMs: context.timeoutMs,
        })
        const lines = result.output ? result.output.split(/\r?\n/).filter(Boolean) : []
        return {
          status: result.ok ? 'pass' : 'warn',
          message: result.ok ? 'Compose project inspected' : 'Compose status unavailable',
          evidence: { services_seen: lines.length, output: result.output.slice(0, 1200) },
        }
      }))
    }

    return checks
  },
}
