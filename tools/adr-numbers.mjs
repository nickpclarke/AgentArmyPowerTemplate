#!/usr/bin/env node
/**
 * adr-numbers.mjs — ADR number governance (so nobody hand-picks a number).
 *
 *   node tools/adr-numbers.mjs check    # CI guard: fail on duplicate ARC-ADR-NNN
 *   node tools/adr-numbers.mjs assign   # merge-time: number ARC-ADR-DRAFT-*.md files
 *
 * Why this exists: choosing "highest existing number + 1" at authoring time is a
 * read-modify-write race. Two parallel sessions both read NNN as the max and both
 * write ARC-ADR-(NNN+1)-*.md; git does not flag it (the filenames differ), so the
 * collision only surfaces after both merge. It bit ARC-ADR-038/040 twice.
 *
 * The fix (see docs/decisions/README.md):
 *   - Author new ADRs as docs/decisions/ARC-ADR-DRAFT-<slug>.md, using the literal
 *     token `ARC-ADR-DRAFT` wherever the number would go.
 *   - `assign` (run by .github/workflows/adr-assign-numbers.yml on push to main,
 *     serialized one-at-a-time) allocates the next integer, renames the file, and
 *     rewrites the token + cross-references. Serial allocation => no collisions.
 *   - `check` (run by .github/workflows/adr-number-guard.yml on PRs) is the
 *     backstop for accidental hand-numbering.
 */
import { readdirSync, readFileSync, writeFileSync, renameSync, statSync } from 'node:fs';
import { join, extname } from 'node:path';

const DIR = 'docs/decisions';
const NUMBERED = /^ARC-ADR-(\d+)-.+\.md$/;
const DRAFT = /^ARC-ADR-DRAFT-(.+)\.md$/;
const TEXT_EXT = new Set([
  '.md', '.mjs', '.js', '.cjs', '.ts', '.tsx', '.py', '.json',
  '.yml', '.yaml', '.ttl', '.txt', '.toml',
]);
const SKIP_DIR = new Set([
  '.git', 'node_modules', '.next', 'dist', 'build', 'coverage', '.venv', '__pycache__',
]);

const pad = (n) => String(n).padStart(3, '0');
const entries = () => readdirSync(DIR);

function numbered() {
  return entries().flatMap((f) => {
    const m = f.match(NUMBERED);
    return m ? [{ file: f, num: Number(m[1]) }] : [];
  });
}

function drafts() {
  return entries()
    .flatMap((f) => {
      const m = f.match(DRAFT);
      return m ? [{ file: f, slug: m[1] }] : [];
    })
    .sort((a, b) => a.slug.localeCompare(b.slug)); // deterministic assignment order
}

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    if (SKIP_DIR.has(name)) continue;
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else if (TEXT_EXT.has(extname(name))) yield p;
  }
}

/** Apply literal global string replacements across every text file in the repo. */
function replaceEverywhere(replacements) {
  let touched = 0;
  for (const p of walk('.')) {
    let body;
    try { body = readFileSync(p, 'utf8'); } catch { continue; }
    let out = body;
    for (const [from, to] of replacements) out = out.split(from).join(to);
    if (out !== body) { writeFileSync(p, out); touched += 1; }
  }
  return touched;
}

function check() {
  const seen = new Map();
  for (const { file, num } of numbered()) {
    const k = pad(num);
    if (!seen.has(k)) seen.set(k, []);
    seen.get(k).push(file);
  }
  const pending = drafts();
  if (pending.length) {
    console.log(`ℹ ${pending.length} draft ADR(s) awaiting merge-time numbering: ${pending.map((d) => d.file).join(', ')}`);
  }
  const dups = [...seen].filter(([, fs]) => fs.length > 1);
  if (dups.length) {
    console.error('✗ Duplicate ARC-ADR numbers detected:');
    for (const [k, fs] of dups) console.error(`    ARC-ADR-${k}  →  ${fs.join('  ·  ')}`);
    console.error('\nEvery ARC-ADR-NNN must be unique. Do not hand-pick numbers — name new');
    console.error('ADRs ARC-ADR-DRAFT-<slug>.md and let the merge-time assigner number them.');
    console.error('See docs/decisions/README.md.');
    process.exit(1);
  }
  console.log(`✓ ${numbered().length} ADR(s); no duplicate numbers.`);
}

function assign() {
  const pending = drafts();
  if (!pending.length) {
    console.log('No draft ADRs (ARC-ADR-DRAFT-*.md) to number.');
    return;
  }
  let next = numbered().reduce((m, x) => Math.max(m, x.num), 0) + 1;
  const plan = pending.map(({ file, slug }) => {
    const num = pad(next);
    next += 1;
    return {
      slug,
      num,
      oldFile: join(DIR, file),
      newFile: join(DIR, `ARC-ADR-${num}-${slug}.md`),
      oldStem: `ARC-ADR-DRAFT-${slug}`,
      newStem: `ARC-ADR-${num}-${slug}`,
    };
  });

  // 1. rename the draft files on disk
  for (const a of plan) renameSync(a.oldFile, a.newFile);
  // 2. repo-wide: resolve slugged cross-references and self-links (unique per draft)
  replaceEverywhere(plan.map((a) => [a.oldStem, a.newStem]));
  // 3. per-file: resolve the bare ARC-ADR-DRAFT token (title + ID) to this file's number
  for (const a of plan) {
    const body = readFileSync(a.newFile, 'utf8').split('ARC-ADR-DRAFT').join(`ARC-ADR-${a.num}`);
    writeFileSync(a.newFile, body);
  }

  console.log(`Assigned ${plan.length} ADR number(s):`);
  for (const a of plan) console.log(`    ARC-ADR-${a.num}  ←  ${a.oldFile}`);
}

const cmd = process.argv[2];
if (cmd === 'check') check();
else if (cmd === 'assign') assign();
else {
  console.error('usage: node tools/adr-numbers.mjs <check|assign>');
  process.exit(2);
}
