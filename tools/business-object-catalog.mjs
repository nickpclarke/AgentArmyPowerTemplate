#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const repoRoot = resolve(__dirname, '..')
const defaultCatalogPath = 'templates/business-object-catalog.example.json'

try {
  main()
} catch (error) {
  console.error(`Business object catalog failed: ${error.message || error}`)
  process.exit(2)
}

function main() {
  const options = parseArgs(process.argv.slice(2))
  if (options.help) {
    console.log(helpText())
    return
  }

  const catalog = readCatalog(options.catalogPath)
  const diagnostics = validateCatalog(catalog)
  const hasErrors = diagnostics.some((item) => item.level === 'error')

  if (options.command === 'validate') {
    const output = renderValidation(catalog, diagnostics, options.format)
    writeOrPrint(options.output, output)
    if (hasErrors) process.exit(1)
    return
  }

  if (hasErrors && !options.allowInvalid) {
    writeOrPrint(options.output, renderValidation(catalog, diagnostics, 'table'))
    process.exit(1)
  }

  const output = renderCatalog(catalog, options.format)
  writeOrPrint(options.output, output)
}

function parseArgs(args) {
  const options = {
    command: 'render',
    catalogPath: defaultCatalogPath,
    format: 'table',
    output: null,
    help: false,
    allowInvalid: false,
  }

  if (args[0] && !args[0].startsWith('--')) options.command = args.shift()
  if (!['validate', 'render'].includes(options.command)) {
    throw new Error('command must be validate or render')
  }

  if (args[0] && !args[0].startsWith('--')) options.catalogPath = args.shift()

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i]
    if (arg === '--help' || arg === '-h') options.help = true
    else if (arg === '--allow-invalid') options.allowInvalid = true
    else if (arg === '--format') options.format = takeValue(args, ++i, '--format')
    else if (arg === '--output' || arg === '-o') options.output = takeValue(args, ++i, '--output')
    else throw new Error(`unknown option: ${arg}`)
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

function readCatalog(path) {
  return JSON.parse(readFileSync(resolve(repoRoot, path), 'utf8'))
}

function validateCatalog(catalog) {
  const diagnostics = []
  const objectIds = new Set()
  const scenarioIds = new Set()
  const capabilityIds = new Set()
  const layerIds = new Set()

  if (catalog.schema_version !== 'business-object-catalog.v1') {
    diagnostics.push(error('schema.version', 'schema_version must be business-object-catalog.v1'))
  }
  if (!isKebab(catalog.catalog_id)) diagnostics.push(error('catalog.id', 'catalog_id must be kebab-case'))

  for (const [index, layer] of entries(catalog.service_layers)) {
    const prefix = `service_layers[${index}]`
    if (!['arcadedb-capability-services', 'platform-operational-services', 'meta-services'].includes(layer.id)) {
      diagnostics.push(error(`${prefix}.id`, 'layer must be one of the three middle-core service families'))
    }
    if (layerIds.has(layer.id)) diagnostics.push(error(`${prefix}.id`, `duplicate layer id: ${layer.id}`))
    layerIds.add(layer.id)
    requireString(diagnostics, prefix, layer, 'display_name')
    requireString(diagnostics, prefix, layer, 'purpose')
  }

  for (const requiredLayer of ['arcadedb-capability-services', 'platform-operational-services', 'meta-services']) {
    if (!layerIds.has(requiredLayer)) diagnostics.push(error('service_layers', `missing required layer: ${requiredLayer}`))
  }

  for (const [index, object] of entries(catalog.object_types)) {
    const prefix = `object_types[${index}]`
    if (!isKebab(object.id)) diagnostics.push(error(`${prefix}.id`, 'object id must be kebab-case'))
    if (objectIds.has(object.id)) diagnostics.push(error(`${prefix}.id`, `duplicate object id: ${object.id}`))
    objectIds.add(object.id)
    requireString(diagnostics, prefix, object, 'display_name')
    requireString(diagnostics, prefix, object, 'description')
    if (!layerIds.has(object.owned_by_layer)) diagnostics.push(error(`${prefix}.owned_by_layer`, `unknown layer: ${object.owned_by_layer}`))
    requireNonEmptyArray(diagnostics, prefix, object, 'states')
    requireNonEmptyArray(diagnostics, prefix, object, 'provider_mappings')
    requireNonEmptyArray(diagnostics, prefix, object, 'redaction_policy')
    if (!['none', 'read-only', 'guarded-mutation'].includes(object.mcp_eligibility)) {
      diagnostics.push(error(`${prefix}.mcp_eligibility`, 'mcp_eligibility must be none, read-only, or guarded-mutation'))
    }
    for (const [mappingIndex, mapping] of entries(object.provider_mappings)) {
      const mappingPrefix = `${prefix}.provider_mappings[${mappingIndex}]`
      requireString(diagnostics, mappingPrefix, mapping, 'provider')
      requireNonEmptyArray(diagnostics, mappingPrefix, mapping, 'records')
      requireNonEmptyArray(diagnostics, mappingPrefix, mapping, 'capabilities')
      for (const capability of mapping.capabilities || []) capabilityIds.add(capability)
    }
  }

  for (const [index, scenario] of entries(catalog.scenarios)) {
    const prefix = `scenarios[${index}]`
    if (!isKebab(scenario.id)) diagnostics.push(error(`${prefix}.id`, 'scenario id must be kebab-case'))
    if (scenarioIds.has(scenario.id)) diagnostics.push(error(`${prefix}.id`, `duplicate scenario id: ${scenario.id}`))
    scenarioIds.add(scenario.id)
    requireString(diagnostics, prefix, scenario, 'display_name')
    requireString(diagnostics, prefix, scenario, 'description')
    requireNonEmptyArray(diagnostics, prefix, scenario, 'service_layers')
    requireNonEmptyArray(diagnostics, prefix, scenario, 'outputs')
    requireNonEmptyArray(diagnostics, prefix, scenario, 'capabilities')
    requireNonEmptyArray(diagnostics, prefix, scenario, 'safety_policy')
    for (const layer of scenario.service_layers || []) {
      if (!layerIds.has(layer)) diagnostics.push(error(`${prefix}.service_layers`, `unknown layer: ${layer}`))
    }
    for (const objectId of [...(scenario.inputs || []), ...(scenario.outputs || [])]) {
      if (!objectIds.has(objectId)) diagnostics.push(error(`${prefix}.objects`, `unknown object reference: ${objectId}`))
    }
    for (const capability of scenario.capabilities || []) {
      if (!capabilityIds.has(capability)) diagnostics.push(error(`${prefix}.capabilities`, `unknown capability reference: ${capability}`))
    }
    if (scenario.mcp_eligible && (!scenario.input_schema || !scenario.output_schema)) {
      diagnostics.push(error(`${prefix}.mcp`, 'mcp_eligible scenarios require input_schema and output_schema'))
    }
  }

  for (const [index, object] of entries(catalog.object_types)) {
    const prefix = `object_types[${index}]`
    for (const relation of object.relationships || []) {
      if (!objectIds.has(relation.target)) diagnostics.push(error(`${prefix}.relationships`, `unknown relationship target: ${relation.target}`))
    }
    for (const scenarioId of object.scenario_mappings || []) {
      if (!scenarioIds.has(scenarioId)) diagnostics.push(error(`${prefix}.scenario_mappings`, `unknown scenario reference: ${scenarioId}`))
    }
  }

  if (!diagnostics.length) diagnostics.push(info('catalog.valid', 'catalog is valid'))
  return diagnostics
}

function entries(value) {
  return Array.isArray(value) ? value.entries() : []
}

function requireString(diagnostics, prefix, object, key) {
  if (typeof object?.[key] !== 'string' || !object[key].trim()) {
    diagnostics.push(error(`${prefix}.${key}`, `${key} must be a non-empty string`))
  }
}

function requireNonEmptyArray(diagnostics, prefix, object, key) {
  if (!Array.isArray(object?.[key]) || object[key].length === 0) {
    diagnostics.push(error(`${prefix}.${key}`, `${key} must be a non-empty array`))
  }
}

function isKebab(value) {
  return typeof value === 'string' && /^[a-z0-9][a-z0-9-]*$/.test(value)
}

function error(id, message) {
  return { level: 'error', id, message }
}

function info(id, message) {
  return { level: 'info', id, message }
}

function renderValidation(catalog, diagnostics, format) {
  if (format === 'json') return `${JSON.stringify({ catalog_id: catalog.catalog_id, diagnostics }, null, 2)}\n`
  if (format === 'markdown') {
    const lines = ['# Business Object Catalog Validation', '']
    lines.push(`- Catalog: \`${catalog.catalog_id || 'unknown'}\``)
    lines.push(`- Status: \`${diagnostics.some((item) => item.level === 'error') ? 'fail' : 'pass'}\``)
    lines.push('')
    lines.push('| Level | Check | Message |')
    lines.push('|---|---|---|')
    for (const item of diagnostics) lines.push(`| ${item.level} | \`${item.id}\` | ${escapePipe(item.message)} |`)
    return `${lines.join('\n')}\n`
  }
  const lines = [`Business object catalog ${diagnostics.some((item) => item.level === 'error') ? 'FAIL' : 'PASS'} (${catalog.catalog_id || 'unknown'})`, '']
  for (const item of diagnostics) lines.push(`${item.level.toUpperCase().padEnd(5)} ${item.id} - ${item.message}`)
  return `${lines.join('\n')}\n`
}

function renderCatalog(catalog, format) {
  const summary = buildSummary(catalog)
  if (format === 'json') return `${JSON.stringify(summary, null, 2)}\n`
  if (format === 'markdown') return renderMarkdown(summary)
  return renderTable(summary)
}

function buildSummary(catalog) {
  const layerCoverage = {}
  for (const layer of catalog.service_layers) {
    layerCoverage[layer.id] = {
      display_name: layer.display_name,
      object_count: 0,
      scenario_count: 0,
    }
  }
  for (const object of catalog.object_types) layerCoverage[object.owned_by_layer].object_count += 1
  for (const scenario of catalog.scenarios) {
    for (const layer of scenario.service_layers) layerCoverage[layer].scenario_count += 1
  }
  return {
    schema_version: catalog.schema_version,
    catalog_id: catalog.catalog_id,
    service_name: 'middle-core',
    service_role: 'Business object, scenario, and MCP-readiness tier between backend-core ArcadeDB services and platform operational APIs.',
    layerCoverage,
    object_types: catalog.object_types.map((object) => ({
      id: object.id,
      display_name: object.display_name,
      owned_by_layer: object.owned_by_layer,
      states: object.states.length,
      providers: [...new Set(object.provider_mappings.map((mapping) => mapping.provider))],
      mcp_eligibility: object.mcp_eligibility,
    })),
    scenarios: catalog.scenarios.map((scenario) => ({
      id: scenario.id,
      display_name: scenario.display_name,
      service_layers: scenario.service_layers,
      outputs: scenario.outputs,
      capability_count: scenario.capabilities.length,
      mcp_eligible: scenario.mcp_eligible,
    })),
  }
}

function renderTable(summary) {
  const lines = []
  lines.push(`Business Object Catalog: ${summary.catalog_id}`)
  lines.push(`Deployable service: ${summary.service_name}`)
  lines.push(summary.service_role)
  lines.push('')
  lines.push('Layer coverage:')
  for (const [id, layer] of Object.entries(summary.layerCoverage)) {
    lines.push(`- ${id}: ${layer.object_count} objects, ${layer.scenario_count} scenarios`)
  }
  lines.push('')
  lines.push(`${pad('Object', 28)} ${pad('Layer', 34)} ${pad('MCP', 16)} Providers`)
  lines.push(`${'-'.repeat(28)} ${'-'.repeat(34)} ${'-'.repeat(16)} ${'-'.repeat(24)}`)
  for (const object of summary.object_types) {
    lines.push(`${pad(object.id, 28)} ${pad(object.owned_by_layer, 34)} ${pad(object.mcp_eligibility, 16)} ${object.providers.join(', ')}`)
  }
  lines.push('')
  lines.push(`${pad('Scenario', 28)} ${pad('MCP', 8)} ${pad('Capabilities', 12)} Outputs`)
  lines.push(`${'-'.repeat(28)} ${'-'.repeat(8)} ${'-'.repeat(12)} ${'-'.repeat(24)}`)
  for (const scenario of summary.scenarios) {
    lines.push(`${pad(scenario.id, 28)} ${pad(String(scenario.mcp_eligible), 8)} ${pad(scenario.capability_count, 12)} ${scenario.outputs.join(', ')}`)
  }
  return `${lines.join('\n')}\n`
}

function renderMarkdown(summary) {
  const lines = ['# Business Object Catalog', '']
  lines.push(`- Catalog: \`${summary.catalog_id}\``)
  lines.push(`- Deployable service: \`${summary.service_name}\``)
  lines.push(`- Role: ${summary.service_role}`)
  lines.push('')
  lines.push('## Layer Coverage')
  lines.push('')
  lines.push('| Layer | Objects | Scenarios |')
  lines.push('|---|---:|---:|')
  for (const [id, layer] of Object.entries(summary.layerCoverage)) {
    lines.push(`| \`${id}\` | ${layer.object_count} | ${layer.scenario_count} |`)
  }
  lines.push('')
  lines.push('## Object Types')
  lines.push('')
  lines.push('| Object | Layer | MCP | Providers |')
  lines.push('|---|---|---|---|')
  for (const object of summary.object_types) {
    lines.push(`| \`${object.id}\` | \`${object.owned_by_layer}\` | ${object.mcp_eligibility} | ${object.providers.join(', ')} |`)
  }
  lines.push('')
  lines.push('## Scenarios')
  lines.push('')
  lines.push('| Scenario | MCP eligible | Capability count | Outputs |')
  lines.push('|---|---:|---:|---|')
  for (const scenario of summary.scenarios) {
    lines.push(`| \`${scenario.id}\` | ${scenario.mcp_eligible} | ${scenario.capability_count} | ${scenario.outputs.map((output) => `\`${output}\``).join(', ')} |`)
  }
  return `${lines.join('\n')}\n`
}

function writeOrPrint(output, contents) {
  if (!output) {
    process.stdout.write(contents)
    return
  }
  const outputPath = resolve(repoRoot, output)
  mkdirSync(dirname(outputPath), { recursive: true })
  writeFileSync(outputPath, contents, 'utf8')
}

function pad(value, size) {
  return String(value ?? '').padEnd(size).slice(0, size)
}

function escapePipe(value) {
  return String(value ?? '').replace(/\|/g, '\\|')
}

function helpText() {
  return `AgentArmy business object catalog

Usage:
  node tools/business-object-catalog.mjs validate [catalog] [options]
  node tools/business-object-catalog.mjs render [catalog] [options]

Options:
  --format <fmt>     table, json, or markdown (default: table)
  --output <path>    Write rendered output to a path
  --allow-invalid    Render even when validation has errors
  --help             Show this help

Examples:
  node tools/business-object-catalog.mjs validate
  node tools/business-object-catalog.mjs render --format markdown
`
}
