#!/usr/bin/env node
/**
 * audit-agents.mjs
 *
 * Scans all agent .md files in .claude/agents/categories/, parses their
 * YAML frontmatter, validates against the schema in .claude/agent-schema.json,
 * and reports compliance issues.
 *
 * Usage:
 *   node tools/audit-agents.mjs [--json] [--summary-only] [--category <cat>]
 *
 * Options:
 *   --json           Output machine-readable JSON instead of table
 *   --summary-only   Print only the summary, not per-agent rows
 *   --category <c>   Filter to a specific category (e.g. 01-core-development)
 *
 * Exit codes:
 *   0  All agents pass required-field validation
 *   1  One or more agents are missing required fields
 */

import { readFileSync, readdirSync, statSync, existsSync } from 'fs';
import { join, dirname, basename, relative } from 'path';
import { fileURLToPath } from 'url';

// ── Path resolution ───────────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = join(__dirname, '..');

const AGENTS_DIR = join(REPO_ROOT, '.claude', 'agents', 'categories');
const SCHEMA_PATH = join(REPO_ROOT, '.claude', 'agent-schema.json');

// ── CLI args ──────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const JSON_OUTPUT = args.includes('--json');
const SUMMARY_ONLY = args.includes('--summary-only');
const CATEGORY_FILTER = (() => {
  const idx = args.indexOf('--category');
  if (idx === -1) return null;
  const val = args[idx + 1];
  if (!val || val.startsWith('--')) {
    console.error('ERROR: --category requires a value');
    process.exit(1);
  }
  return val;
})();

// ── Schema loading ────────────────────────────────────────────────────────────

let schema;
try {
  schema = JSON.parse(readFileSync(SCHEMA_PATH, 'utf8'));
} catch (e) {
  console.error(`ERROR: Cannot load schema from ${SCHEMA_PATH}: ${e.message}`);
  process.exit(2);
}

const REQUIRED_FIELDS = schema.required ?? ['name', 'description', 'tools', 'model'];
const OPTIONAL_FIELDS = Object.keys(schema.properties ?? {}).filter(
  (k) => !REQUIRED_FIELDS.includes(k)
);
const ALL_KNOWN_FIELDS = [...REQUIRED_FIELDS, ...OPTIONAL_FIELDS];

const VALID_MODELS = schema.properties?.model?.enum ?? ['sonnet', 'opus', 'haiku'];
const VALID_CATEGORIES = schema.properties?.category?.enum ?? [];

// ── Frontmatter parser ────────────────────────────────────────────────────────

/**
 * Minimal YAML frontmatter parser.
 * Handles: string scalars, inline arrays (foo: a, b, c), block arrays (- item).
 * Does NOT require js-yaml — uses regex for the simple AgentArmy frontmatter shape.
 */
function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return null;

  const yaml = match[1];
  const result = {};
  const lines = yaml.split(/\r?\n/);
  let currentKey = null;
  let inBlockArray = false;

  for (const line of lines) {
    // Block array item
    if (/^\s+-\s+/.test(line)) {
      if (currentKey && inBlockArray) {
        if (!Array.isArray(result[currentKey])) result[currentKey] = [];
        result[currentKey].push(line.replace(/^\s+-\s+/, '').trim().replace(/^["']|["']$/g, ''));
      }
      continue;
    }

    // Key: value line
    const kvMatch = line.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)/);
    if (kvMatch) {
      currentKey = kvMatch[1];
      const rawVal = kvMatch[2].trim();

      if (rawVal === '' || rawVal === null) {
        // Will be populated by block array lines
        result[currentKey] = null;
        inBlockArray = true;
      } else if (rawVal.startsWith('[')) {
        // Inline array: [a, b, c]
        const inner = rawVal.replace(/^\[|\]$/g, '');
        result[currentKey] = inner.split(',').map((s) => s.trim().replace(/^["']|["']$/g, ''));
        inBlockArray = false;
      } else {
        // Scalar (strip surrounding quotes and trailing inline comments)
        result[currentKey] = rawVal.replace(/^["']|["']$/g, '').replace(/\s+#.*$/, '');
        inBlockArray = false;
      }
    } else {
      // Not a key line — reset block array tracking for indented continuation
      inBlockArray = currentKey !== null;
    }
  }

  // Clean up null arrays (keys declared but no block items found)
  for (const [k, v] of Object.entries(result)) {
    if (v === null) result[k] = [];
  }

  return result;
}

// ── File discovery ────────────────────────────────────────────────────────────

function walk(dir) {
  const results = [];
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    const stat = statSync(fullPath);
    if (stat.isDirectory()) {
      results.push(...walk(fullPath));
    } else if (entry.endsWith('.md') && entry !== 'README.md' && entry !== 'TAXONOMY.md') {
      results.push(fullPath);
    }
  }
  return results;
}

// ── Validation logic ──────────────────────────────────────────────────────────

const KNOWN_TOOLS = schema.definitions?.known_tools?.enum ?? [
  'Read', 'Write', 'Edit', 'Bash', 'Glob', 'Grep',
  'WebFetch', 'WebSearch', 'computer-use', 'Task',
];

function validateAgent(filePath, frontmatter) {
  const issues = [];
  const warnings = [];

  // Required fields
  for (const field of REQUIRED_FIELDS) {
    const val = frontmatter[field];
    if (val === undefined || val === null || val === '' || (Array.isArray(val) && val.length === 0)) {
      issues.push(`Missing required field: ${field}`);
    }
  }

  // model enum check
  if (frontmatter.model && !VALID_MODELS.includes(frontmatter.model)) {
    issues.push(`Invalid model "${frontmatter.model}" — must be one of: ${VALID_MODELS.join(', ')}`);
  }

  // category enum check
  if (frontmatter.category && !VALID_CATEGORIES.includes(frontmatter.category)) {
    warnings.push(`Unknown category "${frontmatter.category}" — not in schema enum`);
  }

  // description convention
  if (frontmatter.description) {
    const desc = frontmatter.description;
    if (!desc.startsWith('Use this agent when') && !desc.startsWith('Use when')) {
      warnings.push('description should start with "Use this agent when" or "Use when"');
    }
    if (desc.length < 40) {
      warnings.push('description is very short (<40 chars) — consider more context');
    }
  }

  // tools: check for unknown tools
  if (frontmatter.tools) {
    const rawTools = Array.isArray(frontmatter.tools)
      ? frontmatter.tools.join(', ')
      : String(frontmatter.tools);
    const toolList = rawTools.split(',').map((t) => t.trim());
    for (const tool of toolList) {
      if (tool && !KNOWN_TOOLS.includes(tool)) {
        warnings.push(`Unknown tool: "${tool}" (not in known-tools list)`);
      }
    }

    // model tier × tool count heuristic
    const toolCount = toolList.filter(Boolean).length;
    if (frontmatter.model === 'haiku' && toolCount > 5) {
      warnings.push(`Haiku agent has ${toolCount} tools — consider sonnet for broad scope`);
    }
    if (frontmatter.model === 'opus' && toolCount <= 2) {
      warnings.push(`Opus agent has only ${toolCount} tools — consider sonnet for lighter tasks`);
    }
  }

  // Unknown/deprecated fields
  const unknownFields = Object.keys(frontmatter).filter((k) => !ALL_KNOWN_FIELDS.includes(k));
  if (unknownFields.length > 0) {
    warnings.push(`Unknown/deprecated fields: ${unknownFields.join(', ')}`);
  }

  // Optional coverage
  const missingOptional = OPTIONAL_FIELDS.filter((f) => {
    const v = frontmatter[f];
    return v === undefined || v === null || (Array.isArray(v) && v.length === 0);
  });

  return { issues, warnings, missingOptional };
}

// ── Category inferred from path ───────────────────────────────────────────────

function inferCategory(filePath) {
  const rel = relative(AGENTS_DIR, filePath);
  const parts = rel.split('/');
  return parts[0] ?? 'unknown';
}

// ── Main ──────────────────────────────────────────────────────────────────────

if (!existsSync(AGENTS_DIR)) {
  console.error(`ERROR: Agents directory not found: ${AGENTS_DIR}`);
  process.exit(2);
}

const agentFiles = walk(AGENTS_DIR).filter((f) => {
  if (!CATEGORY_FILTER) return true;
  return inferCategory(f).startsWith(CATEGORY_FILTER);
});

const results = [];
const namesSeen = new Map(); // name → first filePath

for (const filePath of agentFiles) {
  let content;
  try {
    content = readFileSync(filePath, 'utf8');
  } catch (e) {
    results.push({
      file: relative(REPO_ROOT, filePath),
      name: basename(filePath, '.md'),
      category: inferCategory(filePath),
      status: 'ERROR',
      issues: [`Cannot read file: ${e.message}`],
      warnings: [],
      missingOptional: OPTIONAL_FIELDS,
      frontmatter: null,
    });
    continue;
  }

  const frontmatter = parseFrontmatter(content);
  if (!frontmatter) {
    results.push({
      file: relative(REPO_ROOT, filePath),
      name: basename(filePath, '.md'),
      category: inferCategory(filePath),
      status: 'NO_FRONTMATTER',
      issues: ['No YAML frontmatter block found'],
      warnings: [],
      missingOptional: OPTIONAL_FIELDS,
      frontmatter: null,
    });
    continue;
  }

  const { issues, warnings, missingOptional } = validateAgent(filePath, frontmatter);

  // Duplicate name check
  const agentName = frontmatter.name ?? basename(filePath, '.md');
  if (namesSeen.has(agentName)) {
    issues.push(`Duplicate name "${agentName}" — also defined in ${namesSeen.get(agentName)}`);
  } else {
    namesSeen.set(agentName, relative(REPO_ROOT, filePath));
  }

  const status = issues.length > 0 ? 'FAIL' : warnings.length > 0 ? 'WARN' : 'PASS';

  results.push({
    file: relative(REPO_ROOT, filePath),
    name: agentName,
    category: inferCategory(filePath),
    status,
    issues,
    warnings,
    missingOptional,
    frontmatter,
  });
}

// ── MECE overlap detection ────────────────────────────────────────────────────

// Flag agents whose descriptions share the same high-frequency keyword phrases
const OVERLAP_KEYWORDS = [
  'optimize', 'performance', 'monitoring', 'orchestrat', 'design', 'implement',
  'deploy', 'security', 'data pipeline', 'machine learning',
];

const descriptionGroups = new Map();
for (const r of results) {
  if (!r.frontmatter?.description) continue;
  const desc = r.frontmatter.description.toLowerCase();
  for (const kw of OVERLAP_KEYWORDS) {
    if (desc.includes(kw)) {
      if (!descriptionGroups.has(kw)) descriptionGroups.set(kw, []);
      descriptionGroups.get(kw).push(r.name);
    }
  }
}

const meceWarnings = [];
for (const [kw, agents] of descriptionGroups.entries()) {
  if (agents.length >= 4) {
    meceWarnings.push({
      keyword: kw,
      agents,
      note: `${agents.length} agents share keyword "${kw}" — verify boundary rules are present`,
    });
  }
}

// ── Coverage gaps ─────────────────────────────────────────────────────────────

const categoryCount = new Map();
for (const r of results) {
  const cat = r.category;
  categoryCount.set(cat, (categoryCount.get(cat) ?? 0) + 1);
}
const coverageGaps = [...categoryCount.entries()]
  .filter(([, count]) => count < 3)
  .map(([cat, count]) => ({ category: cat, count }));

// ── Summary stats ─────────────────────────────────────────────────────────────

const totals = {
  total: results.length,
  pass: results.filter((r) => r.status === 'PASS').length,
  warn: results.filter((r) => r.status === 'WARN').length,
  fail: results.filter((r) => r.status === 'FAIL').length,
  noFrontmatter: results.filter((r) => r.status === 'NO_FRONTMATTER').length,
  error: results.filter((r) => r.status === 'ERROR').length,
};

const hasRequiredFieldFailures = totals.fail > 0 || totals.noFrontmatter > 0 || totals.error > 0;

// ── Output ────────────────────────────────────────────────────────────────────

if (JSON_OUTPUT) {
  process.stdout.write(
    JSON.stringify({ results, meceWarnings, coverageGaps, totals }, null, 2) + '\n'
  );
} else {
  // Table header
  const COL = { file: 55, name: 32, category: 24, status: 6 };
  const pad = (s, n) => String(s ?? '').padEnd(n).slice(0, n);
  const hr = '─'.repeat(140);

  if (!SUMMARY_ONLY) {
    console.log('\nAgentArmy Agent Audit Report');
    console.log(hr);
    console.log(
      `${pad('File', COL.file)} ${pad('Name', COL.name)} ${pad('Category', COL.category)} ${pad('Status', COL.status)}  Issues / Warnings`
    );
    console.log(hr);

    for (const r of results) {
      const statusSymbol =
        r.status === 'PASS' ? '✓' :
        r.status === 'WARN' ? '⚠' :
        r.status === 'FAIL' ? '✗' : '?';

      const issueStr = [
        ...r.issues.map((i) => `[FAIL] ${i}`),
        ...r.warnings.map((w) => `[WARN] ${w}`),
      ].join(' | ');

      console.log(
        `${pad(r.file, COL.file)} ${pad(r.name, COL.name)} ${pad(r.category, COL.category)} ${statusSymbol.padEnd(COL.status)}  ${issueStr}`
      );
    }

    console.log(hr);
  }

  // Summary
  console.log('\nSummary');
  console.log(`  Total agents scanned : ${totals.total}`);
  console.log(`  PASS                 : ${totals.pass}`);
  console.log(`  WARN (optional)      : ${totals.warn}`);
  console.log(`  FAIL (required)      : ${totals.fail}`);
  console.log(`  No frontmatter       : ${totals.noFrontmatter}`);
  console.log(`  Read errors          : ${totals.error}`);

  if (meceWarnings.length > 0) {
    console.log('\nPotential MECE Overlaps (4+ agents share a keyword in description)');
    for (const m of meceWarnings) {
      console.log(`  "${m.keyword}": ${m.agents.join(', ')}`);
    }
  }

  if (coverageGaps.length > 0) {
    console.log('\nCoverage Gaps (categories with <3 agents)');
    for (const g of coverageGaps) {
      console.log(`  ${g.category}: ${g.count} agent(s)`);
    }
  }

  // Optional field coverage
  const optionalCoverage = {};
  for (const f of OPTIONAL_FIELDS) {
    const withField = results.filter(
      (r) => r.frontmatter?.[f] !== undefined &&
              r.frontmatter?.[f] !== null &&
              !(Array.isArray(r.frontmatter?.[f]) && r.frontmatter[f].length === 0)
    ).length;
    optionalCoverage[f] = withField;
  }

  console.log('\nOptional Field Coverage (current → target 100% for new agents)');
  for (const [field, count] of Object.entries(optionalCoverage)) {
    const pct = totals.total > 0 ? Math.round((count / totals.total) * 100) : 0;
    console.log(`  ${field.padEnd(24)} ${String(count).padStart(3)} / ${totals.total}  (${pct}%)`);
  }

  console.log('\nValidation command: node tools/audit-agents.mjs');
  console.log('Schema: .claude/agent-schema.json');
  console.log('Template: templates/agent-spec-template.md\n');
}

process.exit(hasRequiredFieldFailures ? 1 : 0);
