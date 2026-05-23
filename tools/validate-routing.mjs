#!/usr/bin/env node
/**
 * Routing Policy Validator
 * Parses .github/routing-policy.yaml (via Python pyyaml), validates schema
 * integrity, checks for duplicate IDs and conflicting rules, and runs a
 * deterministic test harness against known routing scenarios.
 *
 * Requirements: Node.js 18+ (built-ins only), Python 3 with pyyaml installed.
 */

import { readFileSync } from 'fs';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const POLICY_PATH = resolve(__dirname, '../.github/routing-policy.yaml');

// ---------------------------------------------------------------------------
// Load and parse routing-policy.yaml using Python's pyyaml
// ---------------------------------------------------------------------------

function loadPolicy(path) {
  const rawYaml = readFileSync(path, 'utf8');
  const pyScript = 'import yaml,json,sys; print(json.dumps(yaml.safe_load(sys.stdin)))';
  const jsonStr = execSync(`python3 -c "${pyScript}"`, {
    input: rawYaml,
    encoding: 'utf8',
    maxBuffer: 10 * 1024 * 1024,
  });
  return JSON.parse(jsonStr);
}

// ---------------------------------------------------------------------------
// Schema validation
// ---------------------------------------------------------------------------

const REQUIRED_RULE_FIELDS = ['id', 'priority', 'army', 'conditions', 'rationale', 'example'];
const VALID_ARMIES = ['copilot', 'claude_code'];
const VALID_SIZES = ['XS', 'S', 'M', 'L', 'XL'];
const VALID_ISSUE_TYPES = ['epic', 'feature', 'story', 'enabler', 'bug', 'spike', 'decision', 'pull_request'];

function validateSchema(rules) {
  const errors = [];

  for (const rule of rules) {
    const id = rule.id ?? '<unknown>';

    for (const field of REQUIRED_RULE_FIELDS) {
      if (rule[field] === undefined || rule[field] === null) {
        errors.push(`Rule '${id}': missing required field '${field}'`);
      }
    }

    if (rule.army && !VALID_ARMIES.includes(rule.army)) {
      errors.push(`Rule '${id}': invalid army '${rule.army}' (must be one of: ${VALID_ARMIES.join(', ')})`);
    }

    if (rule.priority !== undefined && (!Number.isInteger(rule.priority) || rule.priority < 0)) {
      errors.push(`Rule '${id}': priority must be a non-negative integer`);
    }

    const cond = rule.conditions;
    if (cond) {
      if (cond.size != null && !Array.isArray(cond.size)) {
        errors.push(`Rule '${id}': conditions.size must be an array`);
      } else if (Array.isArray(cond.size)) {
        for (const s of cond.size) {
          if (!VALID_SIZES.includes(s)) {
            errors.push(`Rule '${id}': invalid size '${s}' (valid: ${VALID_SIZES.join(', ')})`);
          }
        }
      }

      if (cond.issue_types != null && !Array.isArray(cond.issue_types)) {
        errors.push(`Rule '${id}': conditions.issue_types must be an array`);
      } else if (Array.isArray(cond.issue_types)) {
        for (const t of cond.issue_types) {
          if (!VALID_ISSUE_TYPES.includes(t)) {
            errors.push(`Rule '${id}': invalid issue_type '${t}' (valid: ${VALID_ISSUE_TYPES.join(', ')})`);
          }
        }
      }

      if (!cond.labels && !cond.keywords && !cond.issue_types && !cond.size && !cond.concern) {
        errors.push(`Rule '${id}': conditions block has no matching criteria`);
      }
    }
  }

  return errors;
}

// ---------------------------------------------------------------------------
// Duplicate ID check
// ---------------------------------------------------------------------------

function checkDuplicateIds(rules) {
  const seen = new Map();
  const duplicates = [];
  for (const rule of rules) {
    const id = rule.id;
    if (seen.has(id)) {
      duplicates.push(`Duplicate rule ID: '${id}'`);
    } else {
      seen.set(id, true);
    }
  }
  return duplicates;
}

// ---------------------------------------------------------------------------
// Conflict detection — two rules at the same priority routing to different armies
// ---------------------------------------------------------------------------

function arraysOverlap(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b)) return true;
  return a.some(x => b.includes(x));
}

function conditionsCanConflict(c1, c2) {
  if (Array.isArray(c1.size) && Array.isArray(c2.size) && !arraysOverlap(c1.size, c2.size)) return false;
  if (Array.isArray(c1.issue_types) && Array.isArray(c2.issue_types) && !arraysOverlap(c1.issue_types, c2.issue_types)) return false;
  if (Array.isArray(c1.labels) && Array.isArray(c2.labels) && !arraysOverlap(c1.labels, c2.labels)) return false;
  return true;
}

function detectConflicts(rules) {
  const conflicts = [];
  const byPriority = new Map();

  for (const rule of rules) {
    const p = rule.priority;
    if (!byPriority.has(p)) byPriority.set(p, []);
    byPriority.get(p).push(rule);
  }

  for (const [priority, group] of byPriority) {
    for (let i = 0; i < group.length; i++) {
      for (let j = i + 1; j < group.length; j++) {
        const r1 = group[i];
        const r2 = group[j];
        if (r1.army !== r2.army && conditionsCanConflict(r1.conditions, r2.conditions)) {
          conflicts.push(
            `Conflict at priority ${priority}: '${r1.id}' (→${r1.army}) and '${r2.id}' (→${r2.army}) ` +
            `may match the same input but route to different armies`
          );
        }
      }
    }
  }

  return conflicts;
}

// ---------------------------------------------------------------------------
// Ambiguity report — rules with same priority routing to the same army
// with overlapping conditions (benign but worth noting)
// ---------------------------------------------------------------------------

function reportAmbiguity(rules) {
  const warnings = [];
  const byPriority = new Map();

  for (const rule of rules) {
    const p = rule.priority;
    if (!byPriority.has(p)) byPriority.set(p, []);
    byPriority.get(p).push(rule);
  }

  let ambiguousCount = 0;
  let totalPairs = 0;

  for (const [priority, group] of byPriority) {
    for (let i = 0; i < group.length; i++) {
      for (let j = i + 1; j < group.length; j++) {
        totalPairs++;
        const r1 = group[i];
        const r2 = group[j];
        if (r1.army === r2.army && conditionsCanConflict(r1.conditions, r2.conditions)) {
          ambiguousCount++;
          warnings.push(
            `Ambiguous at priority ${priority}: '${r1.id}' and '${r2.id}' ` +
            `(same army '${r1.army}', overlapping conditions — first listed wins)`
          );
        }
      }
    }
  }

  const ambiguityRate = totalPairs > 0 ? (ambiguousCount / totalPairs) * 100 : 0;
  return { warnings, ambiguityRate: parseFloat(ambiguityRate.toFixed(1)) };
}

// ---------------------------------------------------------------------------
// Rule matching engine — deterministic: sorts by priority, first match wins
// ---------------------------------------------------------------------------

function textContainsKeyword(input, keywords) {
  if (!keywords || !Array.isArray(keywords)) return false;
  const haystack = ((input.title ?? '') + ' ' + (input.body ?? '')).toLowerCase();
  return keywords.some(kw => haystack.includes(kw.toLowerCase()));
}

function findMatchingRule(input, sortedRules) {
  for (const rule of sortedRules) {
    const cond = rule.conditions;
    if (!cond) continue;

    const checks = [];

    if (Array.isArray(cond.issue_types)) {
      if (!input.issue_type || !cond.issue_types.includes(input.issue_type)) {
        continue;
      }
      checks.push(true);
    }

    if (Array.isArray(cond.size)) {
      if (!input.size || !cond.size.includes(input.size)) {
        continue;
      }
      checks.push(true);
    }

    const hasLabel = Array.isArray(cond.labels) && Array.isArray(input.labels) &&
                     cond.labels.some(l => input.labels.includes(l));
    const hasKeyword = textContainsKeyword(input, cond.keywords);

    if (Array.isArray(cond.labels) || Array.isArray(cond.keywords)) {
      if (!hasLabel && !hasKeyword) {
        if (!Array.isArray(cond.issue_types) && !Array.isArray(cond.size)) {
          continue;
        }
        if (!checks.length) continue;
      } else {
        checks.push(true);
      }
    }

    if (checks.length > 0) {
      return rule;
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Test harness — 30+ cases covering all major routing paths
// ---------------------------------------------------------------------------

const TEST_CASES = [
  {
    description: 'XS bug → Copilot',
    input: { labels: [], issue_type: 'bug', size: 'XS' },
    expected_army: 'copilot',
    expected_agent: null,
  },
  {
    description: 'XS story → Copilot',
    input: { labels: [], issue_type: 'story', size: 'XS' },
    expected_army: 'copilot',
    expected_agent: null,
  },
  {
    description: 'S bug → Copilot',
    input: { labels: [], issue_type: 'bug', size: 'S' },
    expected_army: 'copilot',
    expected_agent: null,
  },
  {
    description: 'S story → Copilot',
    input: { labels: [], issue_type: 'story', size: 'S' },
    expected_army: 'copilot',
    expected_agent: null,
  },
  {
    description: 'copilot-task label → Copilot regardless of size',
    input: { labels: ['copilot-task'], size: 'M' },
    expected_army: 'copilot',
    expected_agent: null,
  },
  {
    description: 'M size fallback → Claude Code',
    input: { labels: [], size: 'M' },
    expected_army: 'claude_code',
    expected_agent: null,
  },
  {
    description: 'L size fallback → Claude Code',
    input: { labels: [], size: 'L' },
    expected_army: 'claude_code',
    expected_agent: null,
  },
  {
    description: 'XL size → architect-reviewer (Epic breakdown)',
    input: { labels: [], size: 'XL' },
    expected_army: 'claude_code',
    expected_agent: 'architect-reviewer',
  },
  {
    description: 'Epic issue type → architect-reviewer',
    input: { labels: [], issue_type: 'epic' },
    expected_army: 'claude_code',
    expected_agent: 'architect-reviewer',
  },
  {
    description: 'Spike type + label → spike-researcher',
    input: { labels: ['spike'], issue_type: 'spike' },
    expected_army: 'claude_code',
    expected_agent: 'spike-researcher',
  },
  {
    description: 'hitl-decision label + Decision type → hitl-coordinator',
    input: { labels: ['hitl-decision'], issue_type: 'decision' },
    expected_army: 'claude_code',
    expected_agent: 'hitl-coordinator',
  },
  {
    description: 'awaiting-human label → hitl-coordinator',
    input: { labels: ['awaiting-human'] },
    expected_army: 'claude_code',
    expected_agent: 'hitl-coordinator',
  },
  {
    description: 'needs-deep-review label → Claude Code /review-pr',
    input: { labels: ['needs-deep-review'] },
    expected_army: 'claude_code',
    expected_agent: null,
  },
  {
    description: 'requirements label + story type → business-analyst',
    input: { labels: ['requirements'], issue_type: 'story', title: 'Refine acceptance criteria for login story' },
    expected_army: 'claude_code',
    expected_agent: 'business-analyst',
  },
  {
    description: 'React optimize keyword → react-specialist',
    input: { labels: ['react', 'frontend'], title: 'Optimize and memoize existing React component tree for performance' },
    expected_army: 'claude_code',
    expected_agent: 'react-specialist',
  },
  {
    description: 'FastAPI keyword → fastapi-developer',
    input: { title: 'Add OAuth2 password flow to FastAPI application with Pydantic models' },
    expected_army: 'claude_code',
    expected_agent: 'fastapi-developer',
  },
  {
    description: 'Kafka keyword → async-messaging-engineer',
    input: { title: 'Design Kafka consumer group with DLQ for the order service' },
    expected_army: 'claude_code',
    expected_agent: 'async-messaging-engineer',
  },
  {
    description: 'Terraform keyword → terraform-engineer',
    input: { title: 'Write a Terraform module for a multi-AZ RDS cluster' },
    expected_army: 'claude_code',
    expected_agent: 'terraform-engineer',
  },
  {
    description: 'SLO keyword → sre-engineer',
    input: { title: 'Define SLOs and error budget for the payments service' },
    expected_army: 'claude_code',
    expected_agent: 'sre-engineer',
  },
  {
    description: 'Wardley label + keyword → wardley-strategist',
    input: { labels: ['wardley'], title: 'Create Wardley map for data platform competitive strategy' },
    expected_army: 'claude_code',
    expected_agent: 'wardley-strategist',
  },
  {
    description: 'enterprise-architecture label + TOGAF keyword → enterprise-architect',
    input: { labels: ['enterprise-architecture'], title: 'TOGAF ADM Phase A Architecture Vision for the platform' },
    expected_army: 'claude_code',
    expected_agent: 'enterprise-architect',
  },
  {
    description: 'OpenTelemetry keyword → observability-engineer',
    input: { title: 'Instrument service with OpenTelemetry traces and Grafana dashboards' },
    expected_army: 'claude_code',
    expected_agent: 'observability-engineer',
  },
  {
    description: 'Flutter keyword → flutter-expert',
    input: { title: 'Implement Flutter BLoC pattern for async data loading with Riverpod' },
    expected_army: 'claude_code',
    expected_agent: 'flutter-expert',
  },
  {
    description: 'dlt + data-pipeline label → dlt-engineer',
    input: { labels: ['data-pipeline'], title: 'Build dlt pipeline from Stripe API to BigQuery with incremental loading' },
    expected_army: 'claude_code',
    expected_agent: 'dlt-engineer',
  },
  {
    description: 'Flyway schema migration keyword → schema-migration-engineer',
    input: { title: 'Zero-downtime Flyway schema migration to rename high-traffic column' },
    expected_army: 'claude_code',
    expected_agent: 'schema-migration-engineer',
  },
  {
    description: 'performance label → performance-engineer',
    input: { labels: ['performance'], title: 'Diagnose latency bottleneck and benchmark checkout flow throughput' },
    expected_army: 'claude_code',
    expected_agent: 'performance-engineer',
  },
  {
    description: 'release-train label → release-manager',
    input: { labels: ['release-train'], title: 'Coordinate RT2 release across UI, API, and worker spokes' },
    expected_army: 'claude_code',
    expected_agent: 'release-manager',
  },
  {
    description: 'security-audit label → security-auditor',
    input: { labels: ['security-audit'], title: 'Audit authentication and session management before production launch' },
    expected_army: 'claude_code',
    expected_agent: 'security-auditor',
  },
  {
    description: 'agent-onboarding + mece-validation labels → agent-distinctiveness-advocate',
    input: { labels: ['agent-onboarding', 'mece-validation'] },
    expected_army: 'claude_code',
    expected_agent: 'agent-distinctiveness-advocate',
  },
  {
    description: 'HIPAA keyword → us-regulatory-architect',
    input: { title: 'HIPAA compliance gap analysis for health data processing platform' },
    expected_army: 'claude_code',
    expected_agent: 'us-regulatory-architect',
  },
  {
    description: 'Pact contract testing keyword → contract-test-engineer',
    input: { title: 'Add Pact consumer tests for the payments to orders service contract' },
    expected_army: 'claude_code',
    expected_agent: 'contract-test-engineer',
  },
  {
    description: 'refactor label + keyword → refactoring-specialist',
    input: { labels: ['refactor'], title: 'Refactor payment processing module to reduce tech debt and clean up code smells' },
    expected_army: 'claude_code',
    expected_agent: 'refactoring-specialist',
  },
  {
    description: 'documentation label → documentation-engineer',
    input: { labels: ['documentation'], title: 'Write API documentation for new payments endpoints' },
    expected_army: 'claude_code',
    expected_agent: 'documentation-engineer',
  },
  {
    description: 'canary deploy keyword → deployment-engineer',
    input: { title: 'Set up canary release with automated rollback for the payments service' },
    expected_army: 'claude_code',
    expected_agent: 'deployment-engineer',
  },
];

// ---------------------------------------------------------------------------
// Main runner
// ---------------------------------------------------------------------------

function main() {
  let exitCode = 0;
  const output = [];

  const log = (msg) => { output.push(msg); process.stdout.write(msg + '\n'); };
  const err = (msg) => {
    const line = '[ERROR] ' + msg;
    output.push(line);
    process.stderr.write(line + '\n');
    exitCode = 1;
  };
  const warn = (msg) => { const line = '[WARN]  ' + msg; output.push(line); process.stdout.write(line + '\n'); };
  const ok = (msg) => { const line = '[OK]    ' + msg; output.push(line); process.stdout.write(line + '\n'); };

  log('');
  log('═══════════════════════════════════════════════════════════════════');
  log('  AgentArmy Routing Policy Validator');
  log('═══════════════════════════════════════════════════════════════════');
  log('');

  log('▶ Loading and parsing routing-policy.yaml ...');
  let policy;
  try {
    policy = loadPolicy(POLICY_PATH);
    ok(`Parsed ${POLICY_PATH}`);
  } catch (e) {
    err(`Failed to load/parse routing policy: ${e.message}`);
    process.exit(1);
  }

  if (!policy.routing_policy) {
    err('Top-level key "routing_policy" not found in YAML');
    process.exit(1);
  }

  const rp = policy.routing_policy;

  if (!rp.version) err('routing_policy.version is missing');
  if (!rp.armies) err('routing_policy.armies is missing');
  if (!rp.rules || !Array.isArray(rp.rules)) {
    err('routing_policy.rules is missing or not a sequence');
    process.exit(1);
  }

  const rules = rp.rules;
  ok(`Found ${rules.length} rules, version ${rp.version}`);

  log('');
  log('▶ Validating rule schema ...');
  const schemaErrors = validateSchema(rules);
  if (schemaErrors.length > 0) {
    for (const e of schemaErrors) err(e);
  } else {
    ok('All rules pass schema validation');
  }

  log('');
  log('▶ Checking for duplicate rule IDs ...');
  const dupes = checkDuplicateIds(rules);
  if (dupes.length > 0) {
    for (const d of dupes) err(d);
  } else {
    ok(`All ${rules.length} rule IDs are unique`);
  }

  log('');
  log('▶ Detecting cross-army conflicts ...');
  const conflicts = detectConflicts(rules);
  if (conflicts.length > 0) {
    for (const c of conflicts) err(c);
  } else {
    ok('No cross-army conflicts at the same priority');
  }

  log('');
  log('▶ Checking routing ambiguity rate ...');
  const { warnings: ambiguityWarnings, ambiguityRate } = reportAmbiguity(rules);
  for (const w of ambiguityWarnings) warn(w);
  if (ambiguityRate > 5) {
    err(`Ambiguity rate ${ambiguityRate}% exceeds the 5% threshold`);
  } else {
    ok(`Ambiguity rate: ${ambiguityRate}% (within 5% threshold)`);
  }

  log('');
  log('▶ Running routing test cases ...');
  const sortedRules = [...rules].sort((a, b) => a.priority - b.priority);

  let passed = 0;
  let failed = 0;

  for (const tc of TEST_CASES) {
    const matched = findMatchingRule(tc.input, sortedRules);

    let testPassed = true;
    const reasons = [];

    if (!matched) {
      testPassed = false;
      reasons.push(`no rule matched (expected army=${tc.expected_army}, agent=${tc.expected_agent ?? 'any'})`);
    } else {
      if (tc.expected_army && matched.army !== tc.expected_army) {
        testPassed = false;
        reasons.push(`army: got '${matched.army}', expected '${tc.expected_army}' (rule: ${matched.id})`);
      }
      if (tc.expected_agent !== undefined && tc.expected_agent !== null && matched.agent !== tc.expected_agent) {
        testPassed = false;
        reasons.push(`agent: got '${matched.agent}', expected '${tc.expected_agent}' (rule: ${matched.id})`);
      }
    }

    if (testPassed) {
      passed++;
      ok(`PASS [${matched?.id ?? 'none'}] ${tc.description}`);
    } else {
      failed++;
      err(`FAIL ${tc.description} — ${reasons.join('; ')}`);
    }
  }

  log('');
  log('═══════════════════════════════════════════════════════════════════');
  log(`  Tests:     ${passed}/${TEST_CASES.length} passed${failed > 0 ? `, ${failed} FAILED` : ''}`);
  log(`  Schema:    ${schemaErrors.length} error(s)`);
  log(`  Dup IDs:   ${dupes.length}`);
  log(`  Conflicts: ${conflicts.length}`);
  log(`  Ambiguity: ${ambiguityRate}%`);
  log(`  Status:    ${(exitCode === 0) ? 'PASS' : 'FAIL'}`);
  log('═══════════════════════════════════════════════════════════════════');
  log('');

  process.exit(exitCode);
}

main();
