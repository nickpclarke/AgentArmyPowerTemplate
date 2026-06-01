#!/usr/bin/env node
// tools/acronyms.mjs — the glossary reconciler (terms + system modules).
//
// Scans markdown docs for three kinds of jargon, cross-references
// docs/glossary.md, and reports what's USED but NOT DEFINED, ranked by
// frequency. Catches more than ALL-CAPS — it also finds CamelCase product
// names and hyphenated fleet module names, which are the bulk of "system
// modules" a plain acronym regex misses.
//
//   node tools/acronyms.mjs                scan docs/ → coverage report, grouped gaps
//   node tools/acronyms.mjs --root         scan the whole repo (broader, noisier)
//   node tools/acronyms.mjs --missing      print only undefined terms, one per line
//   node tools/acronyms.mjs --ci           exit 1 if any undefined term is found
//   node tools/acronyms.mjs find SHACL     print the glossary definition for a term
//
// Zero dependencies (Node stdlib only).

import fs from 'node:fs';
import path from 'node:path';

const GLOSSARY = path.join('docs', 'glossary.md');

// Upper-case tokens that are English/markup noise, not acronyms.
const STOP = new Set(
  `A I AN AS AT BE BY DO GO IF IN IS IT MY NO OF OK ON OR SO TO UP US WE AND ANY ALL ARE
   BUT HOW NEW NOT NOW OFF ONE OUR OUT RUN SEE SET THE USE VIA WHO WHY YES YOU TODO FIXME
   NOTE NOTES WARN WARNING ERROR ERRORS INFO DEBUG SUCCESS FAIL FAILED PASS START STOP STEP
   DONE TRUE FALSE NULL OKAY CAN MAY WILL WITH FROM INTO THAN THEN THIS THAT THESE`.split(/\s+/)
);

// Project-specific noise: ID prefixes / filename stems that read as acronyms but aren't terms.
const PROJECT_STOP = new Set([
  'ARC', 'CLAUDE', 'TBD', 'WIP', 'AKA', 'EG', 'IE', 'ETC', 'NNN', 'YYYY',
  // product / brand names (not acronyms)
  'ANTIGRAVITY', 'CEREBRAS', 'CODEX', 'COPILOT', 'VERTEX', 'ENSO', 'UNTOOL', 'UNU', 'FOUNDRY', 'KEYSTONE',
  // project feature/check IDs (documented as identifiers, not acronyms)
  'CIDX', 'GPM', 'HGA', 'IKW', 'MCR', 'PIN', 'UDA',
  // version/identifier stems & env/error tokens
  'END', 'END2', 'END3', 'ES2023', 'FS0025', 'LIB2', 'OWL2', 'SCD2', 'SHA256', 'LDTS', 'RSRC',
  'ENOENT', 'PATHEXT', 'PYTHONUTF8', 'USERPROFILE', 'GHRUNNERPAT', 'NOTUNIQUE', 'OCCURRENT', 'CLIF',
]);

// SQL / query / HTTP-verb keywords — not acronyms.
const SQL = new Set(
  `SELECT INSERT UPDATE DELETE WHERE FROM INTO VALUES CREATE ALTER DROP TABLE INDEX JOIN INNER
   LEFT RIGHT OUTER GROUP ORDER HAVING LIMIT OFFSET DISTINCT COUNT SUM MAX MIN AVG OVER PARTITION
   RETURN RETURNING UNIQUE PRIMARY FOREIGN CONSTRAINT EXISTS BEGIN COMMIT ROLLBACK USING CASE WHEN
   THEN ELSE UNION ASC DESC QUALIFY UPSERT MERGE TRUNCATE GREATEST NVL COALESCE CAST STRUCT ARRAY
   TEXT STRING NUMERIC BOOLEAN ROW PATCH POST PUT HEAD CONSTRUCT READ WRITE LIST CALL DISPOSE STORE
   SINK SINKS SOURCE STAGE NULL`.split(/\s+/)
);

// Common English / enum / status words that appear upper-cased for emphasis — not acronyms.
const ENGLISH = new Set(
  `ACTION ADD ADMIN ADMISSION AFTER AMBIGUOUS ART AUDIT AUTOMATION AVAILABLE BAD BATCH BEFORE BOTH
   BUILD BUSINESS BUY CANDIDACY CANON CANONICAL CATALOG CATEGORY CHANGES CHOSEN CLARIFY CLASSIFY CODE
   COMPLETED CRITICAL CURRENT DECIDED DECISION DESIGN DISCOVERED DOCUMENT DON DOWN DRAFT DRY DUPLICATE
   EDGE EDIT EFFORT ENFORCER ENV EPIC EVIDENCE EXAMPLE EXCELLENT FAST FIX FLAG FLEET FORK FRAME FRONTIER
   FULL GATE GOOD GRAPH HAND HEADLESS HIGH HOLOGRAPHIC HOOKS IMPACT INBOX INFORMATION INTERFACE ISSUE
   ITEM KEY LEDGER LET LEVEL LIVE LOCAL LOW MAP MARTS MEDIUM MID NAME NEVER NOMINATE NON NOTED OPERATIONAL
   OPTION OWNER PARALLEL PATH PENDING PLACED PLAN PLANE PLATFORM PLUMBING PRIVATE PRODUCT PROJECTION PROMPT
   PROPERTY PROPOSE PROVEN QUICK RAW README READY RECOMMENDED RELATION REPAIR REPO REPORT RESOLVED RESOURCE
   REVIEW ROBOT ROLE ROUTING RULE RUNNER SCRIPTS SECRET SECRETS SEMANTIC SERVERS SHIPPED SIFT SINGLE SLOW
   SNAP SORTER SPIKE SPOKE STAGING STARTING STATUS STEREOTYPE STRATEGIC STRUCTURED SUBSCRIPTION SUCCESSFUL
   SYNC SYNCS SYSTEMS TAXONOMY TEMPORAL TERM TEST TIER TOOL TOPIC TOTAL TRACK TRIAGE TRUTH TYPE USER USERNAME
   VAULT VECTOR VERIFIED VERY VOICE WAR WAS WINS WONDER WORK WORKLOAD YET YOUR AGENT AGENTS ARMY BACKLOG BETS
   FOUNDRY KEYSTONE ROBOT SUGOI WD AG AA
   CANNOT MUST AUTH OPS ARCH ATOMIC HUB SKILL FEAT DOL EN EL DD CM CP CU DS EP FD FP HD ICE IDX LM LR
   LS MDL MM MS PC PMC PP SA SYN TD TL TSL XC OQ NFC CB CC CE IR UK VS WS GET
   AGE CSI GPS IO PM SDL XL XS`.split(/\s+/)
);

// Detection patterns, each tagged with a category.
const PATTERNS = [
  // ALL-CAPS acronyms: NATS, HMAC, JWT, SHACL, WSL2, G1GC, JAVA_OPTS
  ['acronym', /\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*\b/g],
  // CamelCase product / module names: ArcadeDB, JetStream, CloudEvents, OntoUML, DuckDB, MkDocs
  ['product', /\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+\b/g],
  // lower-then-caps products: gUFO, dbt-style — start lowercase, then 2+ caps
  ['product', /\b[a-z][A-Z]{2,}[A-Za-z0-9]*\b/g],
  // hyphenated fleet modules: event-bridge, middle-core, llm-gateway, runbook-orchestrator
  ['module', /\b[a-z][a-z0-9]*(?:-[a-z0-9]+)*-(?:core|bridge|stack|broker|gateway|orchestrator|image|collector|monitor|sync|runner|engine|embedder|introspect|verify|migrator|mcp|analyzer|generator|ontology|cockpit|manager|heartbeat|loop)\b/g],
];

function isNoise(tok, cat) {
  if (cat === 'acronym') {
    if (tok.length < 2) return true;
    if (tok.includes('_')) return true; // ENV/config keys (AZURE_*, ARCADEDB_PASSWORD) are not acronyms
    if (STOP.has(tok) || PROJECT_STOP.has(tok) || SQL.has(tok) || ENGLISH.has(tok)) return true;
    if (/^\d/.test(tok)) return true;
    if (/^[A-Z]{1,2}\d{1,2}$/.test(tok)) return true; // ID-ish: D1, F4, RT5, RT7, PI3 (keeps WSL2 — 3 letters)
    return false;
  }
  if (cat === 'product') return tok.length < 3;
  return false; // module
}

function* extract(text) {
  for (const [cat, re] of PATTERNS) {
    for (const m of text.matchAll(re)) {
      const tok = m[0];
      if (!isNoise(tok, cat)) yield { tok, cat };
    }
  }
}

// Terms the glossary already defines — run the same detectors over every **bold term**.
function definedTerms() {
  const defined = new Set();
  let text = '';
  try { text = fs.readFileSync(GLOSSARY, 'utf8'); } catch { return defined; }
  for (const m of text.matchAll(/\*\*(.+?)\*\*/g)) {
    for (const { tok } of extract(m[1])) defined.add(tok.toLowerCase());
  }
  return defined;
}

function walk(dir) {
  const out = [];
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return out; }
  for (const e of entries) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      // skip auto-generated/vendored dirs — agents-glossary is the generated agent roster, not glossary source
      if (/^(node_modules|\.git|site|\.claude|\.codex|dist|build|obj|bin|coverage|agents-glossary|includes)$/.test(e.name)) continue;
      out.push(...walk(p));
    } else if (/\.md$/.test(e.name)) out.push(p);
  }
  return out;
}

const args = process.argv.slice(2);

if (args[0] === 'find') {
  const q = args[1];
  if (!q) { console.error('usage: acronyms.mjs find <TERM>'); process.exit(2); }
  let text = '';
  try { text = fs.readFileSync(GLOSSARY, 'utf8'); } catch { console.error(`cannot read ${GLOSSARY}`); process.exit(2); }
  const re = new RegExp(`\\b${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
  // Entries are `**TERM** — def`, sometimes many per line joined by ` · `. Print only the
  // matching entry: prefer a hit on the bold TERM; fall back to a hit anywhere in the entry.
  const termHits = [], otherHits = [];
  for (const line of text.split('\n')) {
    for (const seg of line.split(' · ')) {
      const m = seg.match(/\*\*([^*]+)\*\*/);
      if (!m) continue;
      if (re.test(m[1])) termHits.push(seg.trim());
      else if (re.test(seg)) otherHits.push(seg.trim());
    }
  }
  const hits = [...new Set(termHits.length ? termHits : otherHits)];
  if (!hits.length) console.log(`No glossary entry for "${q}".`);
  else hits.forEach(h => console.log(h));
  process.exit(0);
}

if (args[0] === 'abbr') {
  // Generate MkDocs abbreviation definitions (`*[X]: expansion`) from glossary.md so
  // every acronym in the rendered docs gets a hover tooltip. Glossary is the source of
  // truth; this file is generated (documents-as-code, like docs/agents-glossary/).
  let text = '';
  try { text = fs.readFileSync(GLOSSARY, 'utf8'); } catch { console.error(`cannot read ${GLOSSARY}`); process.exit(2); }
  const looksAbbr = (s) => /^[.]?[A-Za-z0-9][A-Za-z0-9./+]{1,11}$/.test(s) && /[A-Z]/.test(s) && !s.includes(' ');
  const out = new Map();
  const add = (k, v) => {
    k = k.trim();
    v = v.split(/\.\s/)[0]                              // first sentence only — tooltips stay short
         .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')       // [text](url) → text
         .replace(/[*`"]/g, '')                         // strip markdown emphasis/code/quotes
         .replace(/\s+/g, ' ').trim().replace(/[.,;:]+$/, '');
    if (k && v && !out.has(k)) out.set(k, v);
  };
  for (const m of text.matchAll(/\*\*([^*]+?)\*\*\s*—\s*([^·\n]+)/g)) {
    const term = m[1].trim(), def = m[2].trim();
    // pass 1: bare acronym term(s), e.g. **HMAC**, **HTTP / HTTPS**, **GC / G1GC**
    for (const alias of term.split(' / ')) {
      if (/^[.]?[A-Z0-9][A-Z0-9./+]{1,11}$/.test(alias) && /[A-Z]/.test(alias)) add(alias, def);
    }
    // pass 2: parenthetical pairing — "Full Name (ACR)" or "ACR (Full Name)"
    const pm = term.match(/^(.*?)\s*\(([^)]+)\)\s*$/);
    if (pm) {
      const x = pm[1].trim(), y = pm[2].trim();
      if (looksAbbr(x) && !looksAbbr(y)) add(x, y);       // ACR (Full Name)  — e.g. PR (Pull Request)
      else if (looksAbbr(y) && !looksAbbr(x)) add(y, x);  // Full Name (ACR)  — e.g. Architecture Decision Record (ADR)
    }
  }
  const keys = [...out.keys()].sort();
  const body = ['<!-- GENERATED by `node tools/acronyms.mjs abbr` — do not edit by hand. Source: docs/glossary.md -->',
    ...keys.map(k => `*[${k}]: ${out.get(k)}`)].join('\n') + '\n';
  const dest = path.join('docs', 'includes', 'abbreviations.md');
  fs.writeFileSync(dest, body);
  console.log(`wrote ${keys.length} abbreviation(s) → ${dest}`);
  process.exit(0);
}

const acronymsOnly = args.includes('--acronyms'); // CI scope: gate on acronyms, not product/module names
const scanRoot = args.includes('--root');
// CI "no new debt" scope: explicit .md file args → scan only those (skip generated includes/agents-glossary).
const fileArgs = args.filter((a) => /\.md$/i.test(a) && !/(^|[\\/])(includes|agents-glossary)[\\/]/.test(a));
const missingOnly = args.includes('--missing');
const ciMode = args.includes('--ci');

const files = fileArgs.length
  ? fileArgs.filter((f) => { try { return fs.statSync(f).isFile(); } catch { return false; } })
  : (scanRoot ? walk('.') : walk('docs'));
const defined = definedTerms();
const rec = new Map(); // key=lowercased token -> {tok, cat, count, sample}

for (const f of files) {
  if (path.resolve(f) === path.resolve(GLOSSARY)) continue;
  let text = '';
  try { text = fs.readFileSync(f, 'utf8'); } catch { continue; }
  for (const { tok, cat } of extract(text)) {
    const key = tok.toLowerCase();
    const r = rec.get(key) || { tok, cat, count: 0, sample: f };
    r.count++;
    rec.set(key, r);
  }
}

const undef = [...rec.values()]
  .filter(r => !defined.has(r.tok.toLowerCase()))
  .sort((a, b) => b.count - a.count);

// CI scope: --acronyms gates only the acronym bucket (product/module names are proper nouns, not gaps)
const gated = acronymsOnly ? undef.filter(r => r.cat === 'acronym') : undef;

if (missingOnly) {
  gated.forEach(r => console.log(r.tok));
  process.exit(ciMode && gated.length ? 1 : 0);
}

const byCat = { acronym: [], product: [], module: [] };
for (const r of undef) byCat[r.cat].push(r);

const distinct = rec.size, seen = distinct - undef.length;
console.log(`Acronym & module scan — ${files.length} markdown file(s) under ${scanRoot ? 'repo root' : 'docs/'}`);
console.log(`distinct terms: ${distinct}  |  in glossary: ${seen}  |  undefined: ${undef.length}  |  coverage: ${distinct ? Math.round(seen / distinct * 100) : 100}%`);

const LABELS = { acronym: 'ACRONYMS', product: 'PRODUCTS / CamelCase', module: 'FLEET MODULES (hyphenated)' };
for (const cat of ['module', 'product', 'acronym']) {
  const list = byCat[cat];
  if (!list.length) continue;
  console.log(`\n── undefined ${LABELS[cat]} (${list.length}) ──`);
  for (const r of list.slice(0, 40)) {
    console.log(`  ${r.tok.padEnd(24)} x${String(r.count).padStart(4)}   e.g. ${r.sample}`);
  }
  if (list.length > 40) console.log(`  … and ${list.length - 40} more`);
}
if (acronymsOnly) console.log(`\nacronym-bucket gaps: ${gated.length}`);
process.exit(ciMode && gated.length ? 1 : 0);
