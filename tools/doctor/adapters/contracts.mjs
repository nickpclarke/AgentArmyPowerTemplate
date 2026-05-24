import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { makeCheck } from '../core.mjs'

export const contractsAdapter = {
  name: 'contracts',
  async run(context) {
    const checks = []
    const schemaPath = join(context.repoRoot, 'tools', 'doctor', 'doctor.v1.schema.json')
    const cockpitContract = join(context.repoRoot, 'extensions', 'arcadedb-cockpit', 'BACKEND_CONTRACT.md')

    checks.push(makeCheck({
      id: 'contracts.doctor-schema',
      component: 'contracts',
      status: existsSync(schemaPath) ? 'pass' : 'fail',
      severity: 'required',
      message: existsSync(schemaPath) ? 'Doctor artifact schema found' : 'Doctor artifact schema missing',
      evidence: { path: 'tools/doctor/doctor.v1.schema.json' },
    }))

    checks.push(makeCheck({
      id: 'contracts.arcadedb-cockpit',
      component: 'contracts',
      status: existsSync(cockpitContract) ? 'pass' : 'warn',
      severity: 'recommended',
      message: existsSync(cockpitContract) ? 'ArcadeDB cockpit contract found' : 'ArcadeDB cockpit contract missing',
      evidence: { path: 'extensions/arcadedb-cockpit/BACKEND_CONTRACT.md' },
    }))

    return checks
  },
}
