import { STATUS_RANK } from './core.mjs'

export function renderEnvelope(envelope, format = 'table') {
  if (format === 'json') return `${JSON.stringify(envelope, null, 2)}\n`
  if (format === 'markdown') return renderMarkdown(envelope)
  return renderTable(envelope)
}

export function renderTable(envelope) {
  const lines = []
  lines.push(`AgentArmy doctor ${envelope.status.toUpperCase()} (${envelope.generated_at})`)
  lines.push(`pass=${envelope.summary.pass} warn=${envelope.summary.warn} fail=${envelope.summary.fail} error=${envelope.summary.error} skip=${envelope.summary.skip}`)
  lines.push('')
  lines.push(`${pad('Status', 8)} ${pad('Severity', 13)} ${pad('Component', 12)} Check`)
  lines.push(`${'-'.repeat(8)} ${'-'.repeat(13)} ${'-'.repeat(12)} ${'-'.repeat(48)}`)
  for (const check of [...envelope.checks].sort(compareChecks)) {
    lines.push(`${pad(check.status, 8)} ${pad(check.severity, 13)} ${pad(check.component, 12)} ${check.id} - ${check.message}`)
  }
  lines.push('')
  if (envelope.artifacts.length) {
    lines.push('Artifacts:')
    for (const artifact of envelope.artifacts) lines.push(`- ${artifact.kind}: ${artifact.path}`)
  }
  return `${lines.join('\n')}\n`
}

export function renderMarkdown(envelope) {
  const lines = []
  lines.push('# AgentArmy Doctor Report')
  lines.push('')
  lines.push(`- Status: \`${envelope.status}\``)
  lines.push(`- Generated: \`${envelope.generated_at}\``)
  lines.push(`- Run: \`${envelope.run_id}\``)
  lines.push(`- Summary: pass ${envelope.summary.pass}, warn ${envelope.summary.warn}, fail ${envelope.summary.fail}, error ${envelope.summary.error}, skip ${envelope.summary.skip}`)
  lines.push('')
  lines.push('| Status | Severity | Component | Check | Message |')
  lines.push('|---|---|---|---|---|')
  for (const check of [...envelope.checks].sort(compareChecks)) {
    lines.push(`| ${escapePipe(check.status)} | ${escapePipe(check.severity)} | ${escapePipe(check.component)} | \`${escapePipe(check.id)}\` | ${escapePipe(check.message)} |`)
  }
  lines.push('')
  return `${lines.join('\n')}\n`
}

function compareChecks(a, b) {
  return STATUS_RANK[b.status] - STATUS_RANK[a.status] || a.component.localeCompare(b.component) || a.id.localeCompare(b.id)
}

function pad(value, size) {
  return String(value).padEnd(size).slice(0, size)
}

function escapePipe(value) {
  return String(value ?? '').replace(/\|/g, '\\|')
}
