#!/usr/bin/env node
// Data Vault 2.1 — canonical SHA-256 hash key / hash diff library (Node).
//
// Bit-identical to tools/data-vault/hash.py. Shared test vectors live in
// hash.vectors.json. See docs/data-vault/strategy.md §3 for the algorithm.
//
// CLI:
//   node hash.mjs --help
//   node hash.mjs --hub  customer_id --value C-12345
//   node hash.mjs --link customer_id=C-12345 order_id=O-99
//   node hash.mjs --diff first_name=Ada last_name=Lovelace email=null
//   node hash.mjs --test          # run vector tests, exit non-zero on mismatch
//   node hash.mjs --update-vectors # recompute expected hashes and rewrite the file

import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const VECTORS_PATH = resolve(__dirname, 'hash.vectors.json');

const DEFAULTS = {
  hash_algorithm: 'sha256',
  separator: '||',
  null_sentinel: '^^',
  case_fold: 'upper',
  trim: true,
  unicode_form: 'NFC',
};

// ---------- Core ----------------------------------------------------------

export function normalizeBusinessKey(value, opts = DEFAULTS, caseSensitive = false) {
  if (value === null || value === undefined) return opts.null_sentinel;
  let s = String(value);
  if (opts.unicode_form && opts.unicode_form !== 'none') s = s.normalize(opts.unicode_form);
  if (opts.trim) s = s.trim();
  if (!caseSensitive) {
    if (opts.case_fold === 'upper') s = s.toUpperCase();
    else if (opts.case_fold === 'lower') s = s.toLowerCase();
  }
  return s;
}

export function normalizeAttribute(value, opts = DEFAULTS) {
  // Descriptive attributes preserve case; only null → sentinel, NFC, trim if configured.
  if (value === null || value === undefined) return opts.null_sentinel;
  let s = String(value);
  if (opts.unicode_form && opts.unicode_form !== 'none') s = s.normalize(opts.unicode_form);
  // Hash diff DOES NOT trim by default — whitespace IS meaningful for descriptive content.
  return s;
}

export function sha256Hex(s) {
  return createHash('sha256').update(Buffer.from(s, 'utf8')).digest('hex');
}

export function hubHash(values, businessKeys, opts = DEFAULTS, caseSensitiveMap = {}) {
  const keys = Array.isArray(businessKeys) ? businessKeys : Object.keys(values);
  const parts = keys.map((k) => normalizeBusinessKey(values[k], opts, !!caseSensitiveMap[k]));
  return sha256Hex(parts.join(opts.separator));
}

export const linkHash = hubHash; // identical mechanics

export function satHashDiff(attributes, opts = DEFAULTS) {
  const names = Object.keys(attributes).sort(); // alphabetical
  const parts = names.map((n) => normalizeAttribute(attributes[n], opts));
  return sha256Hex(parts.join(opts.separator));
}

// ---------- Test runner ---------------------------------------------------

function readVectors() {
  return JSON.parse(readFileSync(VECTORS_PATH, 'utf8'));
}

function runTests({ updateVectors = false } = {}) {
  const vectors = readVectors();
  const opts = { ...DEFAULTS, ...vectors.config };
  const failures = [];

  for (const v of vectors.hub_keys) {
    const cs = v.case_sensitive || {};
    const normalizedParts = v.business_keys.map((k) =>
      normalizeBusinessKey(v.values[k], opts, !!cs[k]),
    );
    const normalized = normalizedParts.join(opts.separator);
    const hash = sha256Hex(normalized);
    if (normalized !== v.expected_normalized) {
      failures.push(`HUB "${v.name}": normalized="${normalized}" expected="${v.expected_normalized}"`);
    }
    if (updateVectors) {
      v.expected_hash = hash;
    } else if (v.expected_hash !== '_computed_at_runtime' && v.expected_hash !== hash) {
      failures.push(`HUB "${v.name}": hash=${hash} expected=${v.expected_hash}`);
    }
  }

  for (const v of vectors.sat_hash_diffs) {
    const names = Object.keys(v.attributes).sort();
    const normalizedParts = names.map((n) => normalizeAttribute(v.attributes[n], opts));
    const normalized = normalizedParts.join(opts.separator);
    const hash = sha256Hex(normalized);
    if (normalized !== v.expected_normalized) {
      failures.push(`SAT "${v.name}": normalized="${normalized}" expected="${v.expected_normalized}"`);
    }
    if (updateVectors) {
      v.expected_hash = hash;
    } else if (v.expected_hash !== '_computed_at_runtime' && v.expected_hash !== hash) {
      failures.push(`SAT "${v.name}": hash=${hash} expected=${v.expected_hash}`);
    }
  }

  if (updateVectors) {
    writeFileSync(VECTORS_PATH, JSON.stringify(vectors, null, 2) + '\n');
    console.log(`Wrote ${VECTORS_PATH}`);
    return 0;
  }
  if (failures.length) {
    for (const f of failures) console.error('  FAIL: ' + f);
    console.error(`\n${failures.length} test failure(s).`);
    return 1;
  }
  console.log(`OK: ${vectors.hub_keys.length} hub + ${vectors.sat_hash_diffs.length} sat vectors passed.`);
  return 0;
}

// ---------- CLI -----------------------------------------------------------

function parseArgs(argv) {
  const args = { _: [], pairs: [], keys: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') args.help = true;
    else if (a === '--test') args.test = true;
    else if (a === '--update-vectors') args.update = true;
    else if (a === '--hub') args.hub = argv[++i];
    else if (a === '--value') args.value = argv[++i];
    else if (a === '--link') args.link = true;
    else if (a === '--diff') args.diff = true;
    else if (a.includes('=')) args.pairs.push(a);
    else args._.push(a);
  }
  return args;
}

function helpText() {
  return `data-vault hash (Node) — DV 2.1 hash key & hash diff

Usage:
  node hash.mjs --hub  <key> --value <v>           # single-column hub hash
  node hash.mjs --link k1=v1 k2=v2 ...             # link or composite-key hash
  node hash.mjs --diff a1=v1 a2=v2 ...             # sat hash diff (alphabetical order auto-applied)
  node hash.mjs --test                             # run vector tests
  node hash.mjs --update-vectors                   # recompute expected_hash in hash.vectors.json

Notes:
  - "null" or "NULL" as a value is treated as a literal null (→ null sentinel).
  - Business keys are normalized: NFC, trim, upper-case (unless case_sensitive).
  - Sat attributes are normalized: NFC, NO trim, NO case fold (descriptive content).
`;
}

function valueOrNull(v) {
  if (v === undefined) return undefined;
  if (v === 'null' || v === 'NULL') return null;
  return v;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || (!args.hub && !args.link && !args.diff && !args.test && !args.update)) {
    process.stdout.write(helpText());
    return 0;
  }
  if (args.test) return runTests();
  if (args.update) return runTests({ updateVectors: true });

  if (args.hub) {
    const values = { [args.hub]: valueOrNull(args.value) };
    console.log(hubHash(values, [args.hub]));
    return 0;
  }
  if (args.link || args.diff) {
    const values = {};
    for (const p of args.pairs) {
      const idx = p.indexOf('=');
      values[p.slice(0, idx)] = valueOrNull(p.slice(idx + 1));
    }
    if (args.diff) console.log(satHashDiff(values));
    else console.log(hubHash(values, Object.keys(values)));
    return 0;
  }
  console.error('Nothing to do. Try --help.');
  return 2;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  process.exit(main());
}
