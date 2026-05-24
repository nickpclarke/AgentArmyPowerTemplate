import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { commandExists, makeCheck, runCommand, timedCheck } from '../core.mjs'

export const repoAdapter = {
  name: 'repo',
  async run(context) {
    const checks = []

    checks.push(makeCheck({
      id: 'repo.root',
      component: 'repo',
      status: existsSync(join(context.repoRoot, 'AGENTS.md')) ? 'pass' : 'fail',
      severity: 'required',
      message: existsSync(join(context.repoRoot, 'AGENTS.md'))
        ? 'Repository guidance found'
        : 'AGENTS.md is missing',
      evidence: { path: 'AGENTS.md' },
    }))

    checks.push(await timedCheck({
      id: 'repo.git',
      component: 'repo',
      severity: 'recommended',
    }, async () => {
      const result = runCommand('git', ['status', '--short'], { cwd: context.repoRoot, timeoutMs: context.timeoutMs })
      return {
        status: result.ok ? 'pass' : 'warn',
        message: result.ok ? 'Git worktree inspected' : 'Git status could not run',
        evidence: {
          dirty_lines: result.ok && result.output ? result.output.split(/\r?\n/).length : 0,
        },
      }
    }))

    for (const [id, command, args] of [
      ['repo.node', 'node', ['--version']],
      ['repo.python', 'python', ['--version']],
      ['repo.gh', 'gh', ['--version']],
    ]) {
      checks.push(await timedCheck({
        id,
        component: 'repo',
        severity: id === 'repo.node' ? 'required' : 'recommended',
      }, async () => {
        const result = commandExists(command, args)
        return {
          status: result.ok ? 'pass' : 'warn',
          message: result.ok ? `${command} is available` : `${command} is not available on PATH`,
          evidence: { version: result.output.split(/\r?\n/)[0] || null },
        }
      }))
    }

    checks.push(makeCheck({
      id: 'repo.docs-config',
      component: 'repo',
      status: existsSync(join(context.repoRoot, 'mkdocs.yml')) ? 'pass' : 'skip',
      severity: 'recommended',
      message: existsSync(join(context.repoRoot, 'mkdocs.yml'))
        ? 'MkDocs configuration found'
        : 'No MkDocs configuration found',
      evidence: { path: 'mkdocs.yml' },
    }))

    checks.push(makeCheck({
      id: 'repo.agent-sync',
      component: 'repo',
      status: existsSync(join(context.repoRoot, 'scripts', 'orchestrate_agent_sync.py')) ? 'pass' : 'warn',
      severity: 'recommended',
      message: 'Agent sync orchestrator check complete',
      evidence: { path: 'scripts/orchestrate_agent_sync.py' },
    }))

    return checks
  },
}
