#!/usr/bin/env node
// adr-scaffold.mjs — pre-fill a Data Vault 2.1 ADR.
//
//   node tools/data-vault/adr-scaffold.mjs --topic "raw-vs-business for customer-segment" --category placement
//
// Categories: placement | hash-algo | identity | streaming | materialization | mart-shape | pii | generic
// Auto-numbers as ARC-ADR-NNN by scanning docs/decisions/.

import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, '..', '..');
const DECISIONS_DIR = join(REPO_ROOT, 'docs', 'decisions');

const CATEGORY_BLOCKS = {
  placement: {
    title: 'Data Vault — raw vs business vault placement for',
    drivers: [
      'Is the value source-extracted (raw) or rule-derived (business)?',
      'Does removing the source erase the value? (yes ⇒ raw, no ⇒ business)',
      'Is the audit trail of the rule itself important? (yes ⇒ versioned record_source in business vault)',
      'What is the rebuild cost if the rule changes?',
    ],
    options: [
      ['Place in raw vault', 'Source-extracted; rule applied at staging is acceptable as long as it is mechanical (type coercion, trim).'],
      ['Place in business vault', 'Rule-derived; isolate the rule and its version in record_source.'],
      ['Split: raw for inputs, business for derived', 'Most flexible; double-storage but cleanest audit.'],
    ],
  },
  'hash-algo': {
    title: 'Data Vault — hash key and hash diff configuration for',
    drivers: [
      'Cross-platform reproducibility (must match between dialects)',
      'Case sensitivity per business key (URLs and hashes are case-sensitive; codes are not)',
      'Collision probability budget (SHA-256 is more than enough for any realistic vault scale)',
      'Backwards compatibility cost if changed later',
    ],
    options: [
      ['SHA-256, upper+trim+NFC, `||`, `^^`', 'AgentArmy default. Aligns with docs/data-vault/strategy.md §3.'],
      ['Per-key case sensitivity overrides', 'Mark URLs / opaque hashes case-sensitive; rest stay normalized.'],
      ['Different separator / sentinel', 'Justify with concrete need (e.g. business keys contain `||` literally).'],
    ],
  },
  identity: {
    title: 'Data Vault — identity resolution method for',
    drivers: [
      'Confidence required (regulatory match vs marketing match)',
      'False-positive cost vs false-negative cost',
      'Source-attribute reliability (does the match attribute have a custodian?)',
      'Re-runnability when the rule improves (versioning in record_source)',
    ],
    options: [
      ['Exact business-key match', 'Use when sources truly share a key (national ID, internal employee ID).'],
      ['Normalized-attribute match (email, phone)', 'Document normalization function explicitly. Sensitive to bad data.'],
      ['Probabilistic multi-attribute match', 'Confidence threshold required. Versioned rule.'],
      ['Graph community detection', 'Use when transitive matches matter (A=B, B=C ⇒ A=C).'],
    ],
  },
  streaming: {
    title: 'Data Vault — streaming load pattern for',
    drivers: [
      'Source event rate',
      'Latency SLA',
      'Idempotency under replay',
      'Late-arriving-key tolerance',
    ],
    options: [
      ['Batch (hourly/nightly)', 'Default when SLA allows. Simplest, cheapest, easiest to test.'],
      ['Micro-batch (10–60s buffer)', 'High rate + seconds-to-minutes SLA. Use ghost-hub pattern for late keys.'],
      ['Per-event stream → stage → raw', 'Sub-second SLA only. Costly; justify per spoke.'],
    ],
  },
  materialization: {
    title: 'Data Vault — materialize vs virtualize for business-vault construct',
    drivers: [
      'Query SLA on the consumer',
      'Rebuild cost / time',
      'Storage budget',
      'Non-determinism (must we freeze the value for audit?)',
    ],
    options: [
      ['Virtualize as dbt view', 'Default. Reflects raw immediately; no rebuild needed.'],
      ['Materialize as incremental table', 'When SLA breached, OR non-deterministic, OR audit-frozen.'],
      ['Materialize as snapshotted PIT', 'Always for PIT — the whole point is precomputation.'],
    ],
  },
  'mart-shape': {
    title: 'Data Vault — information mart projection for',
    drivers: [
      'Consumer (BI tool / ML feature store / graph traversal / semantic layer)',
      'Query patterns (ad-hoc analysis vs known dashboards vs multi-hop traversal)',
      'Refresh cadence',
    ],
    options: [
      ['Star schema', 'Tabular BI (Looker, Power BI, Tableau).'],
      ['Snowflake schema', 'BI with deep dimensional hierarchies.'],
      ['OBT (one big table)', 'ML feature store, columnar warehouses, ad-hoc analytics.'],
      ['Graph projection', 'Recommendation, fraud, network analysis, multi-hop traversal.'],
    ],
  },
  pii: {
    title: 'Data Vault — sensitive-data classification and placement for',
    drivers: [
      'Regulatory classification (GDPR / CCPA / HIPAA / sector-specific)',
      'Retention requirements per attribute',
      'Right-to-be-forgotten support (tombstone-link pattern)',
      'ACL granularity (per-row vs per-column vs per-table)',
    ],
    options: [
      ['Separate `_pii` satellite', 'Default. Independent ACL, independent retention. Pairs with tombstone-link RTBF.'],
      ['Column-level masking in shared satellite', 'Use only when ACL surface and retention are identical for all sat attributes.'],
      ['Excluded from vault entirely', 'When regulation forbids storage; data lives only in source.'],
    ],
  },
  generic: {
    title: 'Data Vault — decision on',
    drivers: ['(fill in drivers)'],
    options: [['Option A', '(describe)'], ['Option B', '(describe)']],
  },
};

function parseArgs(argv) {
  const a = { category: 'generic' };
  for (let i = 0; i < argv.length; i++) {
    const x = argv[i];
    if (x === '--topic') a.topic = argv[++i];
    else if (x === '--category') a.category = argv[++i];
    else if (x === '--status') a.status = argv[++i];
    else if (x === '--help' || x === '-h') a.help = true;
  }
  return a;
}

function help() {
  return `data-vault adr-scaffold

Usage:
  --topic "<short phrase>"        e.g. "customer-segment placement"
  --category <key>                placement | hash-algo | identity | streaming
                                  | materialization | mart-shape | pii | generic
  --status <s>                    Proposed (default) | Accepted | Rejected
  --help

Output: writes docs/decisions/ARC-ADR-NNN-<slug>.md and prints the path.
`;
}

function nextAdrNumber() {
  const files = readdirSync(DECISIONS_DIR).filter((f) => /^ARC-ADR-\d+/.test(f));
  let max = 0;
  for (const f of files) {
    const m = f.match(/^ARC-ADR-(\d+)/);
    if (m) max = Math.max(max, parseInt(m[1], 10));
  }
  return String(max + 1).padStart(3, '0');
}

function slugify(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60);
}

function render(num, topic, category, status) {
  const block = CATEGORY_BLOCKS[category] || CATEGORY_BLOCKS.generic;
  const title = `${block.title} ${topic}`;
  const today = new Date().toISOString().slice(0, 10);

  const driversTable = block.drivers.map((d, i) => `| D${i + 1} | ${d} |`).join('\n');
  const optionsList = block.options.map((o, i) => `${i + 1}. **${o[0]}** — ${o[1]}`).join('\n');
  const prosCons = block.options.map((o) => (
    `### Option — ${o[0]}\n\n**Pros:**\n- TODO\n\n**Cons:**\n- TODO\n`
  )).join('\n---\n\n');

  return `# ARC-ADR-${num} — ${title}

| Field      | Value                                          |
|------------|------------------------------------------------|
| ID         | ARC-ADR-${num}                                 |
| Status     | ${status || 'Proposed'}                        |
| Date       | ${today}                                       |
| Deciders   | Architecture Review                            |
| Supersedes | —                                              |
| Superseded by | —                                           |
| Tags       | data-vault, ${category}                        |

---

## Context and Problem Statement

(Describe the situation. What is the source? What is the consumer? What's already decided in [ARC-ADR-026 — Data Vault 2.1](ARC-ADR-026-data-vault-2-1-methodology.md) that constrains this? What gap remains?)

---

## Decision Drivers

| # | Driver |
|---|--------|
${driversTable}

---

## Considered Options

${optionsList}

---

## Decision Outcome

**Option N — (chosen option)** is adopted because (reason).

### Confirmation criteria

- TODO — observable evidence the decision is working as intended.

---

## Pros and Cons of the Options

${prosCons}

---

## Positive Consequences

- TODO

## Negative Consequences

- TODO

## Related decisions

- [ARC-ADR-026 — Data Vault 2.1 Methodology](ARC-ADR-026-data-vault-2-1-methodology.md)
- TODO

## Open questions

- TODO
`;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.topic) {
    process.stdout.write(help());
    return args.help ? 0 : 2;
  }
  if (!CATEGORY_BLOCKS[args.category]) {
    console.error(`Unknown --category "${args.category}". Try one of: ${Object.keys(CATEGORY_BLOCKS).join(', ')}`);
    return 2;
  }
  if (!existsSync(DECISIONS_DIR)) {
    console.error(`Missing ${DECISIONS_DIR} — run from the AgentArmy repo root.`);
    return 2;
  }

  const num = nextAdrNumber();
  const slug = slugify(args.topic);
  const path = join(DECISIONS_DIR, `ARC-ADR-${num}-${slug}.md`);
  if (existsSync(path)) {
    console.error(`Refusing to overwrite ${path}`);
    return 1;
  }
  writeFileSync(path, render(num, args.topic, args.category, args.status));
  console.log(path);
  return 0;
}

try {
  process.exit(main());
} catch (e) {
  console.error('Error:', e.message);
  process.exit(2);
}
