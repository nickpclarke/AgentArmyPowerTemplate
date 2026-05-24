#!/usr/bin/env node
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const path = resolve(process.cwd(), process.argv[2] || 'tests/artifacts/doctor/latest.json')
const artifact = JSON.parse(readFileSync(path, 'utf8'))
const errors = []

if (artifact.schema_version !== 'doctor.v1') errors.push('schema_version must be doctor.v1')
for (const key of ['run_id', 'generated_at', 'scope', 'status']) {
  if (typeof artifact[key] !== 'string' || !artifact[key]) errors.push(`${key} must be a non-empty string`)
}
if (!['pass', 'warn', 'fail', 'skip', 'error'].includes(artifact.status)) errors.push('status is invalid')
if (!artifact.summary || typeof artifact.summary !== 'object') errors.push('summary must be an object')
for (const key of ['pass', 'warn', 'fail', 'skip', 'error']) {
  if (!Number.isInteger(artifact.summary?.[key]) || artifact.summary[key] < 0) errors.push(`summary.${key} must be a non-negative integer`)
}
if (!Array.isArray(artifact.checks)) errors.push('checks must be an array')
if (!Array.isArray(artifact.artifacts)) errors.push('artifacts must be an array')

for (const [index, check] of (artifact.checks || []).entries()) {
  const prefix = `checks[${index}]`
  for (const key of ['id', 'component', 'status', 'severity', 'message']) {
    if (typeof check[key] !== 'string') errors.push(`${prefix}.${key} must be a string`)
  }
  if (!['pass', 'warn', 'fail', 'skip', 'error'].includes(check.status)) errors.push(`${prefix}.status is invalid`)
  if (!['required', 'recommended', 'informational'].includes(check.severity)) errors.push(`${prefix}.severity is invalid`)
  if (!Number.isInteger(check.duration_ms) || check.duration_ms < 0) errors.push(`${prefix}.duration_ms must be a non-negative integer`)
  if (!check.evidence || typeof check.evidence !== 'object' || Array.isArray(check.evidence)) errors.push(`${prefix}.evidence must be an object`)
  if (!Array.isArray(check.redactions)) errors.push(`${prefix}.redactions must be an array`)
}

if (errors.length) {
  console.error(`Doctor artifact validation failed for ${path}`)
  for (const error of errors) console.error(`- ${error}`)
  process.exit(1)
}

console.log(`Doctor artifact valid: ${path}`)
