#!/usr/bin/env node
// lineage-doc.mjs — Data Vault 2.1 spec → Mermaid + Markdown lineage docs.
//
//   node tools/data-vault/lineage-doc.mjs --spec <file> --out <dir>
//
// Produces:
//   <out>/lineage.md        Markdown overview with hub/link/sat tables
//   <out>/lineage.mmd       Mermaid ER diagram (drop into any .md as ```mermaid)
//   <out>/lineage-flow.mmd  Mermaid flowchart: source → stage → raw → business → mart

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join, extname } from 'node:path';
import { parseYaml } from './yaml-mini.mjs';

function parseArgs(argv) {
  const a = {};
  for (let i = 0; i < argv.length; i++) {
    const x = argv[i];
    if (x === '--spec') a.spec = argv[++i];
    else if (x === '--out') a.out = argv[++i];
    else if (x === '--help' || x === '-h') a.help = true;
  }
  return a;
}

function help() {
  return `data-vault lineage-doc

Usage:
  --spec <file>    YAML or JSON model spec
  --out <dir>      output directory (default: docs/data-vault/lineage)
  --help

Produces lineage.md, lineage.mmd, and lineage-flow.mmd. Commit them so CI can
diff-detect lineage drift on every PR (same pattern as docs/agents-glossary).
`;
}

function loadSpec(p) {
  const text = readFileSync(p, 'utf8');
  return extname(p).toLowerCase() === '.json' ? JSON.parse(text) : parseYaml(text);
}

function generateErd(spec) {
  // Mermaid erDiagram for hubs / links / sats
  const lines = ['erDiagram'];
  for (const h of spec.hubs || []) {
    const cols = [
      `  string ${h.name.replace(/^hub_/, '')}_hk PK`,
      ...(h.business_keys || []).map((bk) => `  string ${typeof bk === 'string' ? bk : bk.name} "BK"`),
      `  timestamp load_date`,
      `  string record_source`,
    ];
    lines.push(`  ${h.name} {`);
    for (const c of cols) lines.push(c);
    lines.push('  }');
  }
  for (const l of spec.links || []) {
    lines.push(`  ${l.name} {`);
    lines.push(`    string ${l.name.replace(/^lnk_/, '')}_hk PK`);
    for (const r of l.hubs || []) {
      const hn = typeof r === 'string' ? r : r.hub;
      const role = typeof r === 'object' && r.role ? r.role : hn.replace(/^hub_/, '');
      lines.push(`    string ${role}_hk FK`);
    }
    lines.push(`    timestamp load_date`);
    lines.push(`    string record_source`);
    lines.push('  }');
  }
  for (const s of spec.satellites || []) {
    lines.push(`  ${s.name} {`);
    const parentEntity = s.parent.replace(/^(hub|lnk)_/, '');
    lines.push(`    string ${parentEntity}_hk FK`);
    lines.push(`    timestamp load_date PK`);
    lines.push(`    string record_source`);
    lines.push(`    string ${s.name.replace(/^sat_/, '').replace(/^eff_sat_/, 'eff_')}_hd`);
    for (const a of s.attributes || []) {
      lines.push(`    ${typeMmd(a.type)} ${a.name}`);
    }
    lines.push('  }');
  }
  // Relationships
  for (const l of spec.links || []) {
    for (const r of l.hubs || []) {
      const hn = typeof r === 'string' ? r : r.hub;
      lines.push(`  ${hn} ||--o{ ${l.name} : "has"`);
    }
  }
  for (const s of spec.satellites || []) {
    lines.push(`  ${s.parent} ||--o{ ${s.name} : "describes"`);
  }
  return lines.join('\n');
}

function typeMmd(sqlType) {
  if (!sqlType) return 'string';
  const t = sqlType.toUpperCase();
  if (t.startsWith('VARCHAR') || t.startsWith('TEXT') || t.startsWith('STRING') || t.startsWith('CHAR')) return 'string';
  if (t.startsWith('INT') || t.startsWith('BIGINT') || t.startsWith('SMALLINT')) return 'int';
  if (t.startsWith('DECIMAL') || t.startsWith('NUMERIC') || t.startsWith('FLOAT') || t.startsWith('DOUBLE') || t.startsWith('REAL')) return 'decimal';
  if (t.startsWith('TIMESTAMP') || t.startsWith('DATETIME')) return 'timestamp';
  if (t.startsWith('DATE')) return 'date';
  if (t.startsWith('BOOL')) return 'boolean';
  return 'string';
}

function generateFlow(spec) {
  const lines = ['flowchart LR'];
  lines.push('  classDef stage fill:#fff2cc,stroke:#d6b656');
  lines.push('  classDef raw fill:#dae8fc,stroke:#6c8ebf');
  lines.push('  classDef biz fill:#d5e8d4,stroke:#82b366');
  lines.push('  classDef mart fill:#f8cecc,stroke:#b85450');

  const sources = new Set();
  for (const h of spec.hubs || []) sources.add(h.record_source);
  for (const s of spec.satellites || []) sources.add(s.record_source);
  for (const l of spec.links || []) if (l.record_source) sources.add(l.record_source);

  for (const src of sources) {
    const id = idSafe(`src_${src}`);
    lines.push(`  ${id}["${src}"]:::stage`);
  }
  for (const h of spec.hubs || []) {
    lines.push(`  ${idSafe(h.name)}["${h.name}"]:::raw`);
    lines.push(`  ${idSafe(`src_${h.record_source}`)} --> ${idSafe(h.name)}`);
  }
  for (const l of spec.links || []) {
    lines.push(`  ${idSafe(l.name)}["${l.name}"]:::raw`);
    if (l.record_source) lines.push(`  ${idSafe(`src_${l.record_source}`)} --> ${idSafe(l.name)}`);
    for (const r of l.hubs || []) {
      const hn = typeof r === 'string' ? r : r.hub;
      lines.push(`  ${idSafe(hn)} -.-> ${idSafe(l.name)}`);
    }
  }
  for (const s of spec.satellites || []) {
    const cls = s.business_vault ? 'biz' : 'raw';
    lines.push(`  ${idSafe(s.name)}["${s.name}"]:::${cls}`);
    if (s.record_source) lines.push(`  ${idSafe(`src_${s.record_source}`)} --> ${idSafe(s.name)}`);
    lines.push(`  ${idSafe(s.parent)} -.-> ${idSafe(s.name)}`);
  }
  return lines.join('\n');
}

function idSafe(s) { return s.replace(/[^a-zA-Z0-9]/g, '_'); }

function generateMarkdown(spec, mmdErd, mmdFlow) {
  const m = spec.model;
  const out = [];
  out.push(`# Data Vault Lineage — \`${m.name}\` v${m.version}`);
  out.push('');
  out.push(`> Auto-generated by \`tools/data-vault/lineage-doc.mjs\`. **Do not edit by hand** — regenerate after every model spec change. CI fails on drift.`);
  out.push('');
  out.push(`- **Dialect:** \`${m.dialect}\``);
  out.push(`- **Hash algorithm:** \`${m.hash_algorithm || 'sha256'}\``);
  out.push(`- **Separator:** \`${m.separator || '||'}\``);
  out.push(`- **Null sentinel:** \`${m.null_sentinel || '^^'}\``);
  if (m.description) {
    out.push('');
    out.push(m.description);
  }

  out.push('');
  out.push('## Entity-relationship diagram');
  out.push('');
  out.push('```mermaid');
  out.push(mmdErd);
  out.push('```');

  out.push('');
  out.push('## Source-to-mart flow');
  out.push('');
  out.push('```mermaid');
  out.push(mmdFlow);
  out.push('```');

  out.push('');
  out.push('## Hubs');
  out.push('');
  out.push('| Name | Business keys | Record source | Notes |');
  out.push('|---|---|---|---|');
  for (const h of spec.hubs || []) {
    const bks = (h.business_keys || []).map((bk) => typeof bk === 'string' ? bk : bk.name).join(', ');
    out.push(`| \`${h.name}\` | ${bks} | \`${h.record_source}\` | ${escapeCell(h.description)} |`);
  }

  out.push('');
  out.push('## Links');
  if ((spec.links || []).length) {
    out.push('');
    out.push('| Name | Hubs | Record source | Notes |');
    out.push('|---|---|---|---|');
    for (const l of spec.links || []) {
      const hs = (l.hubs || []).map((r) => typeof r === 'string' ? `\`${r}\`` : `\`${r.hub}\` (${r.role})`).join(' ↔ ');
      out.push(`| \`${l.name}\` | ${hs} | \`${l.record_source || '—'}\` | ${escapeCell(l.description)} |`);
    }
  } else {
    out.push('');
    out.push('_(none)_');
  }

  out.push('');
  out.push('## Satellites');
  if ((spec.satellites || []).length) {
    out.push('');
    out.push('| Name | Parent | Source | Kind | Sensitivity | Attributes |');
    out.push('|---|---|---|---|---|---|');
    for (const s of spec.satellites || []) {
      const kind = s.effectivity ? 'effectivity' : s.multi_active ? 'multi-active' : s.business_vault ? 'business-vault' : 'standard';
      const attrs = (s.attributes || []).map((a) => `\`${a.name}\``).join(', ');
      out.push(`| \`${s.name}\` | \`${s.parent}\` | \`${s.record_source}\` | ${kind} | ${s.sensitivity || 'internal'} | ${attrs} |`);
    }
  }

  out.push('');
  out.push('## References');
  if ((spec.references || []).length) {
    out.push('');
    out.push('| Name | Kind | Business keys | Attributes |');
    out.push('|---|---|---|---|');
    for (const r of spec.references || []) {
      const bks = (r.business_keys || []).map((bk) => typeof bk === 'string' ? bk : bk.name).join(', ');
      const attrs = (r.attributes || []).map((a) => `\`${a.name}\``).join(', ');
      out.push(`| \`${r.name}\` | ${r.kind || 'flat'} | ${bks} | ${attrs} |`);
    }
  } else {
    out.push('');
    out.push('_(none)_');
  }

  out.push('');
  return out.join('\n');
}

function escapeCell(s) {
  if (!s) return '';
  return String(s).replace(/\|/g, '\\|').replace(/\n/g, ' ');
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.spec) {
    process.stdout.write(help());
    return args.help ? 0 : 2;
  }
  const out = args.out || 'docs/data-vault/lineage';
  mkdirSync(out, { recursive: true });

  const spec = loadSpec(args.spec);
  // Defaults
  spec.links ||= [];
  spec.satellites ||= [];
  spec.references ||= [];

  const erd = generateErd(spec);
  const flow = generateFlow(spec);
  const md = generateMarkdown(spec, erd, flow);

  writeFileSync(join(out, 'lineage.mmd'), erd + '\n');
  writeFileSync(join(out, 'lineage-flow.mmd'), flow + '\n');
  writeFileSync(join(out, 'lineage.md'), md);
  console.log(`Wrote lineage.md, lineage.mmd, lineage-flow.mmd to ${out}/`);
  return 0;
}

try {
  process.exit(main());
} catch (e) {
  console.error('Error:', e.message);
  process.exit(2);
}
