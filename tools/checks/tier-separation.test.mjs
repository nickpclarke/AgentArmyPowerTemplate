// Unit tests for the ARC-ADR-023 tier-separation checker.
// Run: node --test tools/checks/
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  scanTierSeparation,
  checkRepoDir,
  isComposeFile,
  isDockerfile,
  PLATFORM_MARKERS,
} from "./tier-separation.mjs";

test("clean spoke compose (consumes platform via env) passes", () => {
  const files = [{
    path: "docker-compose.yml",
    content: "services:\n  app:\n    build: .\n    environment:\n      - ARCADEDB_URL=${ARCADEDB_URL}\n      - NATS_URL=${NATS_URL}\n",
  }];
  const r = scanTierSeparation({ files, repo: "frontend-core" });
  assert.equal(r.ok, true);
  assert.equal(r.violations.length, 0);
  assert.equal(r.scanned, 1);
});

test("spoke bundling postgres in compose is flagged", () => {
  const files = [{
    path: "docker-compose.yml",
    content: "services:\n  db:\n    image: postgres:16\n  app:\n    build: .\n",
  }];
  const r = scanTierSeparation({ files, repo: "backend-core" });
  assert.equal(r.ok, false);
  assert.equal(r.violations.length, 1);
  assert.equal(r.violations[0].marker, "PostgreSQL");
  assert.equal(r.violations[0].kind, "compose-platform-service");
  assert.equal(r.violations[0].line, 3);
});

test("spoke Dockerfile FROM a platform base is flagged", () => {
  const files = [{ path: "Dockerfile", content: "FROM arcadedata/arcadedb:latest\nCMD [\"server\"]\n" }];
  const r = scanTierSeparation({ files, repo: "middle-core" });
  assert.equal(r.ok, false);
  assert.equal(r.violations[0].marker, "ArcadeDB");
  assert.equal(r.violations[0].kind, "dockerfile-platform-base");
});

test("hub-owned templates/local-stack is never flagged (and not even scanned)", () => {
  const files = [{
    path: "templates/local-stack/docker-compose.yml",
    content: "services:\n  arcadedb:\n    image: arcadedata/arcadedb\n  nats:\n    image: nats:2.10\n",
  }];
  const r = scanTierSeparation({ files, repo: "AgentArmy" });
  assert.equal(r.ok, true);
  assert.equal(r.scanned, 0);
});

test("test fixtures are not flagged (intentionally-bad examples / integration harnesses)", () => {
  // Real false positive caught by the fleet heartbeat: backend-core's own
  // tests/fixtures/tier_separation/bad/docker-compose.yml is a test fixture,
  // not deployable runtime infra.
  const files = [
    { path: "tests/fixtures/tier_separation/bad/docker-compose.yml", content: "services:\n  db:\n    image: arcadedata/arcadedb\n" },
    { path: "backend/test/integration/docker-compose.yml", content: "services:\n  pg:\n    image: postgres:16\n" },
  ];
  const r = scanTierSeparation({ files, repo: "backend-core" });
  assert.equal(r.ok, true, JSON.stringify(r.violations));
  assert.equal(r.scanned, 0);
});

test("isHub:true short-circuits to ok", () => {
  const files = [{ path: "docker-compose.yml", content: "  db:\n    image: postgres\n" }];
  const r = scanTierSeparation({ files, repo: "AgentArmy", isHub: true });
  assert.equal(r.ok, true);
  assert.equal(r.scanned, 0);
});

test("comment-only mentions of platform infra are ignored", () => {
  const files = [{
    path: "docker-compose.yml",
    content: "# do not add a local postgres here — use DATABASE_URL\nservices:\n  app:\n    build: .\n",
  }];
  const r = scanTierSeparation({ files, repo: "frontend-core" });
  assert.equal(r.ok, true);
});

test("env-only NATS reference is not a bundling violation", () => {
  const files = [{
    path: "compose.yaml",
    content: "services:\n  worker:\n    build: .\n    environment:\n      NATS_URL: nats://platform-nats:4222\n",
  }];
  const r = scanTierSeparation({ files, repo: "backend-core" });
  assert.equal(r.ok, true, JSON.stringify(r.violations));
});

test("non-container files are ignored (not scanned)", () => {
  const files = [{ path: "README.md", content: "we run postgres and nats in the platform tier" }];
  const r = scanTierSeparation({ files, repo: "frontend-core" });
  assert.equal(r.ok, true);
  assert.equal(r.scanned, 0);
});

test("unreadable file (empty content) is skipped, not scanned", () => {
  const files = [{ path: "docker-compose.yml", content: "" }];
  const r = scanTierSeparation({ files, repo: "frontend-core" });
  assert.equal(r.ok, true);
  assert.equal(r.scanned, 0);
});

test("file detectors recognise the usual names", () => {
  assert.ok(isComposeFile("docker-compose.yml"));
  assert.ok(isComposeFile("compose.yaml"));
  assert.ok(isComposeFile("deploy/docker-compose.prod.yml"));
  assert.ok(!isComposeFile("config.yml"));
  assert.ok(isDockerfile("Dockerfile"));
  assert.ok(isDockerfile("svc/Dockerfile.api"));
  assert.ok(!isDockerfile("dockerfile-notes.txt"));
});

test("every marker carries a consume-via-env hint", () => {
  for (const m of PLATFORM_MARKERS) {
    assert.ok(m.name && m.env && m.re instanceof RegExp, `marker ${m.name} is well-formed`);
    assert.match(m.env, /_URL$/);
  }
});

// --- checkRepoDir: the local-filesystem path used by the fleet_check_tiers tool ---

test("checkRepoDir flags a violating spoke checkout on disk", () => {
  const dir = mkdtempSync(join(tmpdir(), "tiers-bad-"));
  try {
    writeFileSync(join(dir, "docker-compose.yml"),
      "services:\n  db:\n    image: postgres:16\n  app:\n    build: .\n");
    const r = checkRepoDir(dir, { repo: "fixture-spoke" });
    assert.equal(r.isHub, false);
    assert.equal(r.ok, false);
    assert.equal(r.violations[0].marker, "PostgreSQL");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("checkRepoDir passes a clean spoke checkout on disk", () => {
  const dir = mkdtempSync(join(tmpdir(), "tiers-ok-"));
  try {
    mkdirSync(join(dir, "svc"));
    writeFileSync(join(dir, "svc", "Dockerfile"), "FROM node:22-alpine\nCMD [\"node\"]\n");
    writeFileSync(join(dir, "docker-compose.yml"),
      "services:\n  app:\n    build: ./svc\n    environment:\n      - DATABASE_URL=${DATABASE_URL}\n");
    const r = checkRepoDir(dir, { repo: "fixture-spoke" });
    assert.equal(r.ok, true);
    assert.equal(r.violations.length, 0);
    assert.ok(r.scanned >= 2);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("checkRepoDir auto-detects the hub by templates/local-stack and skips it", () => {
  const dir = mkdtempSync(join(tmpdir(), "tiers-hub-"));
  try {
    mkdirSync(join(dir, "templates", "local-stack"), { recursive: true });
    writeFileSync(join(dir, "templates", "local-stack", "docker-compose.yml"),
      "services:\n  arcadedb:\n    image: arcadedata/arcadedb\n");
    const r = checkRepoDir(dir);
    assert.equal(r.isHub, true);
    assert.equal(r.ok, true);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
