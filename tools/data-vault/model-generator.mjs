#!/usr/bin/env node
// model-generator.mjs — Data Vault 2.1 model spec → DDL + dbt stubs.
//
//   node tools/data-vault/model-generator.mjs --spec <file> --validate
//   node tools/data-vault/model-generator.mjs --spec <file> --out <dir> --target dbt
//   node tools/data-vault/model-generator.mjs --spec <file> --out <dir> --target ddl-postgres
//   node tools/data-vault/model-generator.mjs --spec <file> --out <dir> --target all
//
// Spec schema:  tools/data-vault/model.schema.json
// Strategy:     docs/data-vault/strategy.md

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname, basename, extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseYaml } from './yaml-mini.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCHEMA_PATH = resolve(__dirname, 'model.schema.json');

const DIALECT_TYPES = {
  snowflake: { hash: 'BINARY(32)',     ts: 'TIMESTAMP_NTZ', stringMax: 'STRING'    },
  postgres:  { hash: 'BYTEA',          ts: 'TIMESTAMP',     stringMax: 'TEXT'      },
  bigquery:  { hash: 'BYTES',          ts: 'TIMESTAMP',     stringMax: 'STRING'    },
  databricks:{ hash: 'BINARY',         ts: 'TIMESTAMP',     stringMax: 'STRING'    },
};

// ---------------- CLI ----------------

function parseArgs(argv) {
  const a = { target: 'dbt' };
  for (let i = 0; i < argv.length; i++) {
    const x = argv[i];
    if (x === '--help' || x === '-h') a.help = true;
    else if (x === '--spec')    a.spec    = argv[++i];
    else if (x === '--out')     a.out     = argv[++i];
    else if (x === '--target')  a.target  = argv[++i];
    else if (x === '--validate') a.validate = true;
  }
  return a;
}

function help() {
  return `data-vault model-generator

Usage:
  --spec <file>          path to .yaml | .yml | .json model spec
  --validate             validate only, no output
  --out <dir>            output directory (required if not --validate)
  --target <t>           dbt | ddl-snowflake | ddl-postgres | ddl-bigquery | ddl-databricks | all
                         (default: dbt)
  --help                 show this

Examples:
  node tools/data-vault/model-generator.mjs --spec model.yaml --validate
  node tools/data-vault/model-generator.mjs --spec model.yaml --out build --target dbt
  node tools/data-vault/model-generator.mjs --spec model.yaml --out build --target all
`;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.spec) {
    process.stdout.write(help());
    return args.help ? 0 : 2;
  }

  const spec = loadSpec(args.spec);
  const errors = validate(spec);
  if (errors.length) {
    console.error(`Validation failed (${errors.length}):`);
    for (const e of errors) console.error('  - ' + e);
    return 1;
  }
  if (args.validate) {
    console.log(`OK  ${args.spec}: ${spec.hubs.length} hubs · ${(spec.links || []).length} links · ${(spec.satellites || []).length} sats · ${(spec.references || []).length} refs`);
    return 0;
  }
  if (!args.out) {
    console.error('--out required for generation (or use --validate)');
    return 2;
  }

  const targets = expandTargets(args.target);
  const stats = { files: 0 };
  for (const t of targets) {
    if (t === 'dbt') generateDbt(spec, args.out, stats);
    else generateDdl(spec, args.out, t.replace('ddl-', ''), stats);
  }
  console.log(`Wrote ${stats.files} file(s) to ${args.out}`);
  return 0;
}

function expandTargets(t) {
  if (t === 'all') return ['dbt', 'ddl-snowflake', 'ddl-postgres', 'ddl-bigquery', 'ddl-databricks'];
  if (t === 'dbt' || t.startsWith('ddl-')) return [t];
  throw new Error(`Unknown --target ${t}`);
}

// ---------------- Spec loading ----------------

function loadSpec(p) {
  const text = readFileSync(p, 'utf8');
  const ext = extname(p).toLowerCase();
  if (ext === '.json') return JSON.parse(text);
  return parseYaml(text);
}

// ---------------- Validation (structural, lightweight) ----------------

function validate(spec) {
  const errors = [];
  if (!spec || typeof spec !== 'object') return ['spec must be an object'];
  if (!spec.model || typeof spec.model !== 'object') errors.push('model: required object');
  if (!spec.hubs || !Array.isArray(spec.hubs) || spec.hubs.length === 0) errors.push('hubs: required non-empty array');
  spec.links ||= [];
  spec.satellites ||= [];
  spec.references ||= [];

  const m = spec.model || {};
  if (!m.name || !/^[a-z][a-z0-9_]*$/.test(m.name)) errors.push(`model.name must be snake_case (got: ${m.name})`);
  if (!m.dialect || !DIALECT_TYPES[m.dialect]) errors.push(`model.dialect must be one of ${Object.keys(DIALECT_TYPES).join(', ')}`);
  if (typeof m.version !== 'number') errors.push('model.version: required number');

  const hubNames = new Set();
  for (const h of spec.hubs || []) {
    if (!h.name || !/^hub_[a-z][a-z0-9_]*$/.test(h.name)) errors.push(`hub name "${h.name}" must match ^hub_[a-z][a-z0-9_]*$`);
    if (!h.business_keys || h.business_keys.length === 0) errors.push(`hub ${h.name}: business_keys required`);
    if (!h.record_source) errors.push(`hub ${h.name}: record_source required`);
    if (hubNames.has(h.name)) errors.push(`duplicate hub name: ${h.name}`);
    hubNames.add(h.name);
  }
  const linkNames = new Set();
  for (const l of spec.links || []) {
    if (!l.name || !/^lnk_[a-z][a-z0-9_]*$/.test(l.name)) errors.push(`link name "${l.name}" must match ^lnk_[a-z][a-z0-9_]*$`);
    if (!l.hubs || l.hubs.length < 2) errors.push(`link ${l.name}: at least 2 hubs required`);
    for (const ref of l.hubs || []) {
      const hubName = typeof ref === 'string' ? ref : ref.hub;
      if (!hubNames.has(hubName)) errors.push(`link ${l.name}: unknown hub "${hubName}"`);
    }
    if (linkNames.has(l.name)) errors.push(`duplicate link name: ${l.name}`);
    linkNames.add(l.name);
  }
  for (const s of spec.satellites || []) {
    if (!s.name || !/^(sat|eff_sat)_[a-z][a-z0-9_]*$/.test(s.name)) errors.push(`sat name "${s.name}" must match ^(sat|eff_sat)_[a-z][a-z0-9_]*$`);
    if (!hubNames.has(s.parent) && !linkNames.has(s.parent)) errors.push(`sat ${s.name}: parent "${s.parent}" not found among hubs/links`);
    if (!s.attributes || s.attributes.length === 0) errors.push(`sat ${s.name}: attributes required`);
    if (s.effectivity && !linkNames.has(s.parent)) errors.push(`sat ${s.name}: effectivity sats must hang off a link, not a hub`);
  }
  for (const r of spec.references || []) {
    if (!r.name || !/^ref_[a-z][a-z0-9_]*$/.test(r.name)) errors.push(`ref name "${r.name}" must match ^ref_[a-z][a-z0-9_]*$`);
  }
  return errors;
}

// ---------------- DDL generation ----------------

function generateDdl(spec, outDir, dialect, stats) {
  if (!DIALECT_TYPES[dialect]) throw new Error(`Unknown dialect: ${dialect}`);
  const t = DIALECT_TYPES[dialect];
  const m = spec.model;
  const lddl = m.load_date_column || 'load_date';
  const rsrc = m.record_source_column || 'record_source';
  const hk = m.hk_suffix || '_hk';
  const hd = m.hd_suffix || '_hd';

  const ddl = [];
  ddl.push(`-- Generated by tools/data-vault/model-generator.mjs`);
  ddl.push(`-- model: ${m.name} v${m.version} · dialect: ${dialect}`);
  ddl.push(`-- DO NOT EDIT BY HAND. Regenerate from the spec.`);
  ddl.push('');

  for (const h of spec.hubs) {
    const entity = h.name.replace(/^hub_/, '');
    const cols = [
      `  ${entity}${hk}       ${t.hash}      NOT NULL`,
      ...h.business_keys.map((bk) => `  ${bkName(bk)}     ${bkType(bk, t)} NOT NULL`),
      `  ${lddl}      ${t.ts}      NOT NULL`,
      `  ${rsrc}      ${t.stringMax} NOT NULL`,
      `  PRIMARY KEY (${entity}${hk})`,
    ];
    ddl.push(`CREATE TABLE IF NOT EXISTS ${h.name} (`);
    ddl.push(cols.join(',\n'));
    ddl.push(`);`);
    if (h.description) ddl.push(`-- ${h.description}`);
    ddl.push('');
  }

  for (const l of spec.links) {
    const entity = l.name.replace(/^lnk_/, '');
    const refs = l.hubs.map((r) => (typeof r === 'string' ? { hub: r, role: null } : r));
    const fkCols = refs.map((r) => {
      const hubEntity = r.hub.replace(/^hub_/, '');
      const colName = r.role ? `${r.role}${hk}` : `${hubEntity}${hk}`;
      return `  ${colName}      ${t.hash}      NOT NULL`;
    });
    ddl.push(`CREATE TABLE IF NOT EXISTS ${l.name} (`);
    ddl.push([
      `  ${entity}${hk}       ${t.hash}      NOT NULL`,
      ...fkCols,
      `  ${lddl}      ${t.ts}      NOT NULL`,
      `  ${rsrc}      ${t.stringMax} NOT NULL`,
      `  PRIMARY KEY (${entity}${hk})`,
    ].join(',\n'));
    ddl.push(`);`);
    if (l.description) ddl.push(`-- ${l.description}`);
    ddl.push('');
  }

  for (const s of spec.satellites) {
    const parentEntity = s.parent.replace(/^(hub|lnk)_/, '');
    const parentCol = `${parentEntity}${hk}`;
    const cols = [
      `  ${parentCol}        ${t.hash}      NOT NULL`,
      `  ${lddl}              ${t.ts}        NOT NULL`,
      `  ${rsrc}              ${t.stringMax} NOT NULL`,
      `  ${s.name.replace(/^sat_/, '').replace(/^eff_sat_/, 'eff_')}${hd}   ${t.hash}      NOT NULL`,
    ];
    if (s.multi_active) {
      cols.push(`  ${s.sub_sequence_column || 'sub_seq'}             INTEGER NOT NULL`);
    }
    for (const a of s.attributes) {
      cols.push(`  ${a.name.padEnd(20)} ${a.type}${a.nullable === false ? ' NOT NULL' : ''}`);
    }
    const pk = s.multi_active
      ? `(${parentCol}, ${lddl}, ${s.sub_sequence_column || 'sub_seq'})`
      : `(${parentCol}, ${lddl})`;
    cols.push(`  PRIMARY KEY ${pk}`);

    ddl.push(`CREATE TABLE IF NOT EXISTS ${s.name} (`);
    ddl.push(cols.join(',\n'));
    ddl.push(`);`);
    if (s.description) ddl.push(`-- ${s.description}`);
    if (s.sensitivity && s.sensitivity !== 'internal') ddl.push(`-- sensitivity: ${s.sensitivity}`);
    ddl.push('');
  }

  for (const r of spec.references) {
    ddl.push(`CREATE TABLE IF NOT EXISTS ${r.name} (`);
    const cols = [
      ...r.business_keys.map((bk) => `  ${bkName(bk)}    ${bkType(bk, t)} NOT NULL`),
      ...(r.attributes || []).map((a) => `  ${a.name.padEnd(20)} ${a.type}`),
      `  PRIMARY KEY (${r.business_keys.map(bkName).join(', ')})`,
    ];
    ddl.push(cols.join(',\n'));
    ddl.push(`);`);
    ddl.push('');
  }

  const path = join(outDir, 'ddl', dialect, `${m.name}.sql`);
  ensureDir(dirname(path));
  writeFileSync(path, ddl.join('\n'));
  stats.files++;
}

function bkName(bk) { return typeof bk === 'string' ? bk : bk.name; }
function bkType(bk, t) { return typeof bk === 'string' ? 'VARCHAR(255)' : (bk.type || 'VARCHAR(255)'); }

// ---------------- dbt generation ----------------

function generateDbt(spec, outDir, stats) {
  const m = spec.model;
  const lddl = m.load_date_column || 'load_date';
  const rsrc = m.record_source_column || 'record_source';
  const hk = m.hk_suffix || '_hk';
  const hd = m.hd_suffix || '_hd';
  const root = join(outDir, 'dbt');

  // dbt_project.yml stub
  const projYml = `# Generated by tools/data-vault/model-generator.mjs
# Vendored skeleton — merge into your existing dbt_project.yml.
name: '${m.name}'
version: '${m.version}.0.0'
config-version: 2
profile: '${m.name}'
model-paths: ["models"]
models:
  ${m.name}:
    staging:       { +materialized: view,        +tags: ['staging'] }
    raw_vault:
      hubs:        { +materialized: incremental, +tags: ['raw_vault', 'hub']  }
      links:       { +materialized: incremental, +tags: ['raw_vault', 'link'] }
      satellites:  { +materialized: incremental, +tags: ['raw_vault', 'sat']  }
      references:  { +materialized: table,       +tags: ['raw_vault', 'ref']  }
    business_vault: { +materialized: view, +tags: ['business_vault'] }
    marts:          { +materialized: table, +tags: ['marts'] }
`;
  writeOnce(join(root, 'dbt_project.yml'), projYml, stats);

  // For each hub: a stage stub + a hub model + a _schema.yml entry
  for (const h of spec.hubs) {
    const entity = h.name.replace(/^hub_/, '');
    const bkCols = h.business_keys.map(bkName);

    const stageSql = `-- staging/stg_${entity}.sql — review and replace 'src_${entity}' with your real source.
{{ config(materialized='view') }}

{{ datavault4dbt.stage(
    include_source_columns=true,
    source_model='src_${entity}',
    hashed_columns={
      '${entity}${hk}': ${formatList(bkCols)}
    },
    derived_columns={
      '${lddl}':     'CURRENT_TIMESTAMP()',
      '${rsrc}':     "'${h.record_source.replace(/'/g, "''")}'"
    }
) }}
`;
    writeOnce(join(root, 'models', 'staging', `stg_${entity}.sql`), stageSql, stats);

    const hubSql = `-- raw_vault/hubs/${h.name}.sql
{{ config(materialized='incremental') }}

{{ datavault4dbt.hub(
    hashkey='${entity}${hk}',
    business_keys=${formatList(bkCols)},
    source_models=['stg_${entity}']
) }}
`;
    writeOnce(join(root, 'models', 'raw_vault', 'hubs', `${h.name}.sql`), hubSql, stats);
  }

  for (const l of spec.links) {
    const entity = l.name.replace(/^lnk_/, '');
    const fkRefs = l.hubs.map((r) => {
      const hubName = typeof r === 'string' ? r : r.hub;
      const hubEntity = hubName.replace(/^hub_/, '');
      return (typeof r === 'string' || !r.role) ? `${hubEntity}${hk}` : `${r.role}${hk}`;
    });
    const linkSql = `-- raw_vault/links/${l.name}.sql
{{ config(materialized='incremental') }}

{{ datavault4dbt.link(
    link_hashkey='${entity}${hk}',
    foreign_hashkeys=${formatList(fkRefs)},
    source_models=['stg_${entity}']
) }}
`;
    writeOnce(join(root, 'models', 'raw_vault', 'links', `${l.name}.sql`), linkSql, stats);
  }

  for (const s of spec.satellites) {
    const parentEntity = s.parent.replace(/^(hub|lnk)_/, '');
    const parentCol = `${parentEntity}${hk}`;
    const sourceModelGuess = `stg_${parentEntity}`;
    const attrNames = s.attributes.map((a) => a.name).sort();
    const hdName = `${s.name.replace(/^sat_/, '').replace(/^eff_sat_/, 'eff_')}${hd}`;

    let macro;
    if (s.effectivity) {
      macro = `{{ datavault4dbt.eff_sat(
    parent_hashkey='${parentCol}',
    src_driving_key='${s.driving_key || 'TODO_set_driving_key'}',
    source_model='${sourceModelGuess}'
) }}`;
    } else if (s.multi_active) {
      macro = `{{ datavault4dbt.ma_sat_v0(
    parent_hashkey='${parentCol}',
    src_hashdiff='${hdName}',
    src_payload=${formatList(attrNames)},
    sub_sequence='${s.sub_sequence_column || 'sub_seq'}',
    source_model='${sourceModelGuess}'
) }}`;
    } else {
      macro = `{{ datavault4dbt.sat_v0(
    parent_hashkey='${parentCol}',
    src_hashdiff='${hdName}',
    src_payload=${formatList(attrNames)},
    source_model='${sourceModelGuess}'
) }}`;
    }
    const sensitivityTag = s.sensitivity && s.sensitivity !== 'internal' ? `,\n  tags=['raw_vault', 'sat', 'sensitivity:${s.sensitivity}']` : '';
    const satSql = `-- raw_vault/satellites/${s.name}.sql
{{ config(materialized='incremental'${sensitivityTag}) }}

${macro}
`;
    writeOnce(join(root, 'models', 'raw_vault', 'satellites', `${s.name}.sql`), satSql, stats);
  }

  for (const r of spec.references) {
    const refSql = `-- raw_vault/references/${r.name}.sql
{{ config(materialized='table') }}

-- Replace src_${r.name} with your reference data source.
SELECT * FROM {{ ref('src_${r.name}') }}
`;
    writeOnce(join(root, 'models', 'raw_vault', 'references', `${r.name}.sql`), refSql, stats);
  }

  // _schema.yml
  const schemaLines = ['version: 2', 'models:'];
  for (const h of spec.hubs) {
    const entity = h.name.replace(/^hub_/, '');
    schemaLines.push(`  - name: ${h.name}`);
    schemaLines.push(`    description: "${(h.description || '').replace(/"/g, "'")}"`);
    schemaLines.push(`    columns:`);
    schemaLines.push(`      - name: ${entity}${hk}`);
    schemaLines.push(`        tests: [not_null, unique]`);
    for (const bk of h.business_keys) {
      schemaLines.push(`      - name: ${bkName(bk)}`);
      schemaLines.push(`        tests: [not_null]`);
    }
    schemaLines.push(`      - name: ${lddl}`);
    schemaLines.push(`        tests: [not_null]`);
    schemaLines.push(`      - name: ${rsrc}`);
    schemaLines.push(`        tests: [not_null]`);
  }
  for (const s of spec.satellites) {
    const parentEntity = s.parent.replace(/^(hub|lnk)_/, '');
    schemaLines.push(`  - name: ${s.name}`);
    schemaLines.push(`    description: "${(s.description || '').replace(/"/g, "'")}"`);
    if (!s.multi_active && !s.effectivity) {
      schemaLines.push(`    tests:`);
      schemaLines.push(`      - dbt_utils.unique_combination_of_columns:`);
      schemaLines.push(`          combination_of_columns: [${parentEntity}${hk}, ${lddl}]`);
    }
    schemaLines.push(`    columns:`);
    schemaLines.push(`      - name: ${parentEntity}${hk}`);
    schemaLines.push(`        tests: [not_null]`);
    schemaLines.push(`      - name: ${lddl}`);
    schemaLines.push(`        tests: [not_null]`);
  }
  writeOnce(join(root, 'models', '_schema.yml'), schemaLines.join('\n') + '\n', stats);
}

function formatList(items) {
  if (items.length === 1) return JSON.stringify(items[0]);
  return '[' + items.map((s) => JSON.stringify(s)).join(', ') + ']';
}

// ---------------- IO helpers ----------------

function ensureDir(d) { mkdirSync(d, { recursive: true }); }

function writeOnce(path, content, stats) {
  ensureDir(dirname(path));
  writeFileSync(path, content);
  stats.files++;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    process.exit(main());
  } catch (e) {
    console.error('Error:', e.message);
    process.exit(2);
  }
}
