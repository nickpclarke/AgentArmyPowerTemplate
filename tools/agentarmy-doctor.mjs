#!/usr/bin/env node
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { arcadedbAdapter } from './doctor/adapters/arcadedb.mjs'
import { containersAdapter } from './doctor/adapters/containers.mjs'
import { contractsAdapter } from './doctor/adapters/contracts.mjs'
import { imageAdapter } from './doctor/adapters/image.mjs'
import { repoAdapter } from './doctor/adapters/repo.mjs'
import { serviceChecksFor } from './doctor/adapters/services.mjs'
import { buildEnvelope, createContext, writeArtifact } from './doctor/core.mjs'
import { renderEnvelope, renderMarkdown } from './doctor/renderers.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const repoRoot = resolve(__dirname, '..')

const adapters = [
  repoAdapter,
  serviceChecksFor('frontend'),
  serviceChecksFor('backend'),
  arcadedbAdapter,
  containersAdapter,
  contractsAdapter,
]

main().catch((error) => {
  console.error(`AgentArmy doctor failed: ${error.message || error}`)
  process.exit(2)
})

async function main() {
  const options = parseArgs(process.argv.slice(2))
  if (options.help) {
    console.log(helpText())
    return
  }

  const context = createContext({
    repoRoot,
    strict: options.strict,
    timeoutMs: options.timeoutMs,
  })

  const selected = selectAdapters(options.command, options.components)
  const checks = []
  for (const adapter of selected) {
    checks.push(...await adapter.run(context))
  }

  const artifacts = []
  let envelope = buildEnvelope(context, checks, artifacts)

  if (options.writeDefaultArtifacts) {
    const jsonPath = 'tests/artifacts/doctor/latest.json'
    artifacts.push(writeArtifact(repoRoot, jsonPath, `${JSON.stringify(envelope, null, 2)}\n`))
    envelope = buildEnvelope(context, checks, artifacts)
    writeArtifact(repoRoot, jsonPath, `${JSON.stringify(envelope, null, 2)}\n`)
    artifacts.push(writeArtifact(repoRoot, 'tests/artifacts/doctor/latest.md', renderMarkdown(envelope)))
    envelope = buildEnvelope(context, checks, artifacts)
    writeArtifact(repoRoot, jsonPath, `${JSON.stringify(envelope, null, 2)}\n`)
  }

  const rendered = renderEnvelope(envelope, options.format)
  if (options.output) {
    writeDirect(options.output, rendered)
  } else {
    process.stdout.write(rendered)
  }

  if (envelope.summary.error > 0 || envelope.summary.fail > 0) process.exit(1)
}

function selectAdapters(command, components) {
  const byName = new Map(adapters.map((adapter) => [adapter.name, adapter]))
  if (command === 'image') return [imageAdapter(components[0])]
  if (components.length) {
    return components.map((name) => {
      if (!byName.has(name)) throw new Error(`Unknown component: ${name}`)
      return byName.get(name)
    })
  }
  if (!command || command === 'all' || command === 'doctor') return adapters
  if (command === 'services') return [byName.get('frontend'), byName.get('backend')]
  if (byName.has(command)) return [byName.get(command)]
  if (command === 'export') return adapters
  throw new Error(`Unknown command: ${command}`)
}

function parseArgs(args) {
  const options = {
    command: null,
    components: [],
    format: 'table',
    output: null,
    strict: false,
    help: false,
    timeoutMs: undefined,
    writeDefaultArtifacts: false,
  }

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i]
    if (arg === '--help' || arg === '-h') options.help = true
    else if (arg === '--strict') options.strict = true
    else if (arg === '--write-artifacts') options.writeDefaultArtifacts = true
    else if (arg === '--format') options.format = takeValue(args, ++i, '--format')
    else if (arg === '--output' || arg === '-o') options.output = takeValue(args, ++i, '--output')
    else if (arg === '--component') options.components.push(takeValue(args, ++i, '--component'))
    else if (arg === '--timeout-ms') options.timeoutMs = Number(takeValue(args, ++i, '--timeout-ms'))
    else if (arg.startsWith('--')) throw new Error(`Unknown option: ${arg}`)
    else if (!options.command) options.command = arg
    else options.components.push(arg)
  }

  if (!['table', 'json', 'markdown'].includes(options.format)) {
    throw new Error('--format must be table, json, or markdown')
  }
  return options
}

function takeValue(args, index, flag) {
  const value = args[index]
  if (!value || value.startsWith('--')) throw new Error(`${flag} requires a value`)
  return value
}

function writeDirect(outputPath, contents) {
  const absolutePath = resolve(repoRoot, outputPath)
  mkdirSync(dirname(absolutePath), { recursive: true })
  writeFileSync(absolutePath, contents, 'utf8')
  if (!existsSync(absolutePath)) throw new Error(`Could not write ${outputPath}`)
}

function helpText() {
  return `AgentArmy platform diagnostics

Usage:
  node tools/agentarmy-doctor.mjs [command] [options]

Commands:
  all | doctor       Run all default checks
  services           Run frontend and backend manifest checks
  frontend           Run frontend manifest checks
  backend            Run backend manifest checks
  arcadedb           Run ArcadeDB readiness and schema checks
  containers         Run Docker and compose checks
  contracts          Run contract artifact checks
  image <dir>        Validate an image.json manifest + probe its services (Image Standard)
  export             Run all checks and render output

Options:
  --format <fmt>     table, json, or markdown (default: table)
  --output <path>    Write rendered output to a path
  --component <name> Limit to one component; may be repeated
  --strict           Treat skipped optional live dependencies as failures
  --timeout-ms <n>   Per-probe timeout in milliseconds
  --write-artifacts  Write tests/artifacts/doctor/latest.json and latest.md
  --help             Show this help

Examples:
  node tools/agentarmy-doctor.mjs
  node tools/agentarmy-doctor.mjs arcadedb --format json
  node tools/agentarmy-doctor.mjs --write-artifacts
`
}
