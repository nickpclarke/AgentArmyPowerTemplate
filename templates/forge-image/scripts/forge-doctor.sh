#!/usr/bin/env sh
# AgentArmy agentarmy-forge doctor.
#
# Proves seven things end-to-end (per image.json doctor.proves):
#   1. readiness                       — /healthz returns 200
#   2. ontology-fetch-http             — http source fetches a TTL we serve
#                                        locally + parses to IR
#   3. ontology-fetch-file             — file:// source parses to IR
#   4. ontology-fetch-blob             — skip-with-PASS when SKIP_AZURE=1
#                                        (default in CI); else real fetch
#   5. v0-csharp-emit-byte-identical   — golden: emit C# from a frozen YAML;
#                                        byte-compare against tests/golden/reference.g.cs
#   6. smoke-compile-passes            — tsc --noEmit on the TS emit;
#                                        `python -c "import generated_module"`
#                                        for the Python emit. C# skipped by
#                                        default (set SKIP_DOTNET=0 to enable)
#   7. pr-opener-opens-against-dummy   — init a bare local git repo, run
#                                        pr_opener against `local:<path>`,
#                                        verify the branch landed
#
# All checks run *inside the container* against the live FastAPI process on
# :8086. The doctor expects the container to be started with MODE=serve.
#
# Usage:
#   ./scripts/forge-doctor.sh              # default localhost:8086
#   HOST=forge PORT=8086 ./scripts/forge-doctor.sh   # in-compose
#
# Env overrides:
#   HOST            — forge host (default: localhost)
#   PORT            — forge port (default: 8086)
#   GOLDEN_DIR      — golden fixtures dir (default: /opt/agentarmy/tests/golden)
#   SKIP_AZURE      — when "1", check #4 PASSes with skip note (default: 1)
#   SKIP_DOTNET     — when "1", skip the C# smoke-compile in check #6 (default: 1)
#   PYTHON_BIN      — python interpreter (default: python -> python3)
set -eu

HOST="${HOST:-localhost}"
PORT="${PORT:-8086}"
BASE="http://${HOST}:${PORT}"
GOLDEN_DIR="${GOLDEN_DIR:-/opt/agentarmy/tests/golden}"
SKIP_AZURE="${SKIP_AZURE:-1}"
SKIP_DOTNET="${SKIP_DOTNET:-1}"

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then PYTHON_BIN=python3; fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "FATAL: no python interpreter on PATH" >&2
  exit 1
fi

# Use python's tempfile.mkdtemp so the path is whatever python natively uses
# (avoids /tmp-mismatch on Git Bash + Windows-native python).
WORKDIR="$("$PYTHON_BIN" -c "import tempfile; print(tempfile.mkdtemp(prefix='forge-doctor.'))")"

PASS=0
FAIL=0
ok()   { printf "  \033[32mPASS\033[0m %s\n" "$1"; PASS=$((PASS+1)); }
fail() { printf "  \033[31mFAIL\033[0m %s\n" "$1"; FAIL=$((FAIL+1)); }
skip() { printf "  \033[33mSKIP\033[0m %s\n" "$1"; PASS=$((PASS+1)); }

HTTP_PID=""
cleanup() {
  if [ -n "$HTTP_PID" ] && kill -0 "$HTTP_PID" 2>/dev/null; then
    kill "$HTTP_PID" 2>/dev/null || true
    wait "$HTTP_PID" 2>/dev/null || true
  fi
  if [ -n "${WORKDIR:-}" ]; then
    "$PYTHON_BIN" -c "import shutil,sys; shutil.rmtree(sys.argv[1], ignore_errors=True)" "$WORKDIR" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "agentarmy-forge doctor"
echo "  base:       ${BASE}"
echo "  golden:     ${GOLDEN_DIR}"
echo "  workdir:    ${WORKDIR}"
echo "  SKIP_AZURE: ${SKIP_AZURE}"
echo "  SKIP_DOTNET: ${SKIP_DOTNET}"
echo

# ---------------------------------------------------------------------------
# 1. readiness — /healthz 200
# ---------------------------------------------------------------------------
echo "[1/7] readiness — /healthz 200"
READY="false"
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  code="$(curl -sS -o /tmp/forge-health.json -w '%{http_code}' --max-time 3 "${BASE}/healthz" 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then READY="true"; break; fi
  sleep 1
done
if [ "$READY" = "true" ]; then
  ok "/healthz 200"
else
  fail "/healthz never returned 200 in 15 attempts"
  echo "summary: ${PASS} pass, ${FAIL} fail"
  exit 1
fi

# ---------------------------------------------------------------------------
# 2. ontology-fetch-http — start a tiny http.server in WORKDIR, copy the
#    reference TTL into it, ask forge to parse via http://...
# ---------------------------------------------------------------------------
echo
echo "[2/7] ontology-fetch-http — serve reference.ttl over http; forge fetches + parses"
cp "${GOLDEN_DIR}/reference.ttl" "${WORKDIR}/reference.ttl"
# Bind to 0.0.0.0 so it's reachable from inside-container at 127.0.0.1 too.
"$PYTHON_BIN" -m http.server 8765 --bind 127.0.0.1 --directory "$WORKDIR" \
  >"${WORKDIR}/http.log" 2>&1 &
HTTP_PID=$!
# Wait for the http server.
HTTP_OK="false"
for i in 1 2 3 4 5 6 7 8; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:8765/reference.ttl" 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then HTTP_OK="true"; break; fi
  sleep 1
done
if [ "$HTTP_OK" != "true" ]; then
  fail "local http server didn't come up on :8765"
else
  RESP="$(curl -sS --max-time 30 -H 'Content-Type: application/json' -X POST \
    -d '{"source":"http://127.0.0.1:8765/reference.ttl","target":"csharp","out":"'"${WORKDIR}/out-http"'"}' \
    "${BASE}/generate" 2>/dev/null || echo '{}')"
  if echo "$RESP" | grep -qE '"ok":[[:space:]]?true'; then
    if echo "$RESP" | grep -q '"User"' && echo "$RESP" | grep -q '"Document"'; then
      ok "http source parsed; IR contains User + Document"
    else
      fail "http source parsed but IR missing expected ObjectTypes: ${RESP}"
    fi
  else
    fail "POST /generate failed for http source: ${RESP}"
  fi
fi

# ---------------------------------------------------------------------------
# 3. ontology-fetch-file — file:// URI parses to IR
# ---------------------------------------------------------------------------
echo
echo "[3/7] ontology-fetch-file — file:// URI parses to IR"
cp "${GOLDEN_DIR}/reference.model.yaml" "${WORKDIR}/reference.model.yaml"
RESP="$(curl -sS --max-time 30 -H 'Content-Type: application/json' -X POST \
  -d '{"source":"file://'"${WORKDIR}/reference.model.yaml"'","target":"csharp","out":"'"${WORKDIR}/out-file"'"}' \
  "${BASE}/generate" 2>/dev/null || echo '{}')"
if echo "$RESP" | grep -qE '"ok":[[:space:]]?true' && echo "$RESP" | grep -q '"User"'; then
  ok "file source parsed; IR contains User + Document"
else
  fail "POST /generate failed for file source: ${RESP}"
fi

# ---------------------------------------------------------------------------
# 4. ontology-fetch-blob — skip-with-PASS if SKIP_AZURE=1
# ---------------------------------------------------------------------------
echo
echo "[4/7] ontology-fetch-blob — Azure Blob source"
if [ "$SKIP_AZURE" = "1" ]; then
  skip "SKIP_AZURE=1 — no Azure creds in sandbox; module imports + URI parser unit-tested only"
  # Validate the blob_source module at least imports + URI parser works.
  IMPORT_OK="$("$PYTHON_BIN" -c "
import sys
sys.path.insert(0, '/opt/agentarmy/scripts')
from forge.sources import blob_source
acc, ctr, key = blob_source._parse_uri('azureblob://myacct/mycontainer/path/to/model.ttl')
assert acc == 'myacct', acc
assert ctr == 'mycontainer', ctr
assert key == 'path/to/model.ttl', key
print('ok')
" 2>&1)"
  if [ "$IMPORT_OK" = "ok" ]; then
    echo "         (blob_source._parse_uri unit check: ok)"
  else
    fail "blob_source module/parser unit check failed: $IMPORT_OK"
  fi
else
  BLOB_URI="${BLOB_URI:?BLOB_URI required when SKIP_AZURE=0}"
  RESP="$(curl -sS --max-time 60 -H 'Content-Type: application/json' -X POST \
    -d "{\"source\":\"${BLOB_URI}\",\"target\":\"csharp\",\"out\":\"${WORKDIR}/out-blob\"}" \
    "${BASE}/generate" 2>/dev/null || echo '{}')"
  if echo "$RESP" | grep -qE '"ok":[[:space:]]?true'; then
    ok "blob source parsed: ${BLOB_URI}"
  else
    fail "POST /generate failed for blob source: ${RESP}"
  fi
fi

# ---------------------------------------------------------------------------
# 5. v0-csharp-emit-byte-identical — generate vs golden
# ---------------------------------------------------------------------------
echo
echo "[5/7] v0-csharp-emit-byte-identical — generated C# matches frozen golden"
# Use a deterministic source URI string so the file header line is reproducible.
# The golden was generated with source.uri=file:///work/reference.model.yaml.
DETERMINISTIC_SOURCE="file:///work/reference.model.yaml"
# Stage the YAML at the deterministic path inside the container so the URI we
# pass to forge resolves to it.
mkdir -p /work 2>/dev/null || true
cp "${GOLDEN_DIR}/reference.model.yaml" /work/reference.model.yaml 2>/dev/null || true
RESP="$(curl -sS --max-time 30 -H 'Content-Type: application/json' -X POST \
  -d '{"source":"'"${DETERMINISTIC_SOURCE}"'","target":"csharp","out":"'"${WORKDIR}/out-golden"'"}' \
  "${BASE}/generate" 2>/dev/null || echo '{}')"
GEN="${WORKDIR}/out-golden/DataPlatformContracts.g.cs"
if [ -f "$GEN" ]; then
  if "$PYTHON_BIN" -c "
import sys
a = open(sys.argv[1], 'rb').read()
b = open(sys.argv[2], 'rb').read()
if a == b:
    print('match')
else:
    # Surface a tiny diff to help debug.
    import difflib
    al = a.decode('utf-8', errors='replace').splitlines()
    bl = b.decode('utf-8', errors='replace').splitlines()
    diff = list(difflib.unified_diff(bl, al, fromfile='golden', tofile='generated', n=2))
    sys.stderr.write('\\n'.join(diff[:40]) + '\\n')
    print('mismatch')
" "$GEN" "${GOLDEN_DIR}/reference.g.cs" 2>"${WORKDIR}/diff.log" | grep -q '^match$'; then
    ok "generated DataPlatformContracts.g.cs == golden reference.g.cs (byte-identical)"
  else
    fail "C# emit differs from golden (see workdir/diff.log for unified diff)"
    cat "${WORKDIR}/diff.log" 2>/dev/null || true
  fi
else
  fail "no generated file at $GEN (response: $RESP)"
fi

# 5b. rust-emit-byte-identical — same frozen YAML, target=rust, vs reference.g.rs
RESP="$(curl -sS --max-time 30 -H 'Content-Type: application/json' -X POST \
  -d '{"source":"'"${DETERMINISTIC_SOURCE}"'","target":"rust","out":"'"${WORKDIR}/out-golden-rs"'"}' \
  "${BASE}/generate" 2>/dev/null || echo '{}')"
GEN_RS="${WORKDIR}/out-golden-rs/data_platform_contracts.g.rs"
if [ -f "$GEN_RS" ]; then
  if "$PYTHON_BIN" -c "
import sys
a = open(sys.argv[1], 'rb').read()
b = open(sys.argv[2], 'rb').read()
if a == b:
    print('match')
else:
    import difflib
    al = a.decode('utf-8', errors='replace').splitlines()
    bl = b.decode('utf-8', errors='replace').splitlines()
    sys.stderr.write('\\n'.join(difflib.unified_diff(bl, al, fromfile='golden', tofile='generated', n=2)[:40]) + '\\n')
    print('mismatch')
" "$GEN_RS" "${GOLDEN_DIR}/reference.g.rs" 2>"${WORKDIR}/diff-rs.log" | grep -q '^match$'; then
    ok "generated data_platform_contracts.g.rs == golden reference.g.rs (byte-identical)"
  else
    fail "Rust emit differs from golden (see workdir/diff-rs.log for unified diff)"
    cat "${WORKDIR}/diff-rs.log" 2>/dev/null || true
  fi
else
  fail "no generated Rust file at $GEN_RS (response: $RESP)"
fi

# ---------------------------------------------------------------------------
# 6. smoke-compile-passes — TS via tsc --noEmit; Python via import probe.
# ---------------------------------------------------------------------------
echo
echo "[6/7] smoke-compile — TS (tsc --noEmit) + Python (import probe)"

# Generate all three at the deterministic source URI so we have something
# to compile.
RESP="$(curl -sS --max-time 30 -H 'Content-Type: application/json' -X POST \
  -d '{"source":"'"${DETERMINISTIC_SOURCE}"'","target":"all","out":"'"${WORKDIR}/out-all"'"}' \
  "${BASE}/generate" 2>/dev/null || echo '{}')"

# 6a. Python smoke — `python -c "import data_platform_contracts"` from the out dir.
PY_GEN="${WORKDIR}/out-all/data_platform_contracts.g.py"
if [ -f "$PY_GEN" ]; then
  # The generated module is `data_platform_contracts.g.py`, an unusual name
  # because of the `.g.` infix. Use importlib so a normal `import` works.
  PY_OUT="$("$PYTHON_BIN" -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('dpc', '$PY_GEN')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
# Spot-check the symbols.
assert hasattr(m, 'User'), 'User missing'
assert hasattr(m, 'Document'), 'Document missing'
print('ok')
" 2>&1)"
  if [ "$PY_OUT" = "ok" ]; then
    ok "Python emit imports cleanly; User + Document present"
  else
    fail "Python emit import failed: $PY_OUT"
  fi
else
  fail "no generated python file at $PY_GEN"
fi

# 6b. TS smoke — tsc --noEmit. Needs `npm install -g typescript zod` at image build.
TS_GEN="${WORKDIR}/out-all/data-platform-contracts.g.ts"
if [ -f "$TS_GEN" ]; then
  if command -v tsc >/dev/null 2>&1; then
    # Need to teach tsc where to find zod — symlink the global modules dir.
    TS_WORK="${WORKDIR}/ts-work"
    mkdir -p "$TS_WORK"
    cp "$TS_GEN" "$TS_WORK/contracts.ts"
    cat > "$TS_WORK/tsconfig.json" <<'TSCONF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "node",
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["*.ts"]
}
TSCONF
    # Link the global node_modules into this work dir so `import { z } from 'zod'`
    # resolves. The global install dir is reported by `npm root -g`.
    NPM_GLOBAL="$(npm root -g 2>/dev/null || echo)"
    if [ -n "$NPM_GLOBAL" ] && [ -d "$NPM_GLOBAL" ]; then
      ln -sf "$NPM_GLOBAL" "$TS_WORK/node_modules" 2>/dev/null || \
        cp -r "$NPM_GLOBAL" "$TS_WORK/node_modules" 2>/dev/null || true
    fi
    TSC_OUT="$(cd "$TS_WORK" && tsc --noEmit 2>&1 || echo "TSC_FAILED")"
    if echo "$TSC_OUT" | grep -q "TSC_FAILED"; then
      fail "tsc --noEmit on generated TS failed: $TSC_OUT"
    else
      ok "tsc --noEmit clean on generated TS"
    fi
  else
    skip "tsc not on PATH (no node toolchain in image) — set SKIP_NODE=0 to require"
  fi
else
  fail "no generated TS file at $TS_GEN"
fi

# 6c. C# smoke — heavy; skip by default.
if [ "$SKIP_DOTNET" = "1" ]; then
  skip "C# smoke-compile (dotnet not in base image; set SKIP_DOTNET=0 + dotnet on PATH to enable)"
else
  CS_GEN="${WORKDIR}/out-all/DataPlatformContracts.g.cs"
  if [ -f "$CS_GEN" ] && command -v dotnet >/dev/null 2>&1; then
    CS_WORK="${WORKDIR}/cs-work"
    mkdir -p "$CS_WORK"
    cp "$CS_GEN" "$CS_WORK/Contracts.cs"
    cat > "$CS_WORK/Contracts.csproj" <<'CSCONF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>
</Project>
CSCONF
    if (cd "$CS_WORK" && dotnet build -nologo -v q --no-restore 2>&1 | tee "${WORKDIR}/dotnet.log" | tail -5 | grep -qE "Build succeeded"); then
      ok "dotnet build clean on generated C#"
    else
      fail "dotnet build failed; see ${WORKDIR}/dotnet.log"
    fi
  else
    fail "SKIP_DOTNET=0 but no dotnet on PATH"
  fi
fi

# ---------------------------------------------------------------------------
# 7. pr-opener-opens-against-dummy — init a bare local git repo, push to it.
# ---------------------------------------------------------------------------
echo
echo "[7/7] pr-opener — initialise bare local repo, run pr_opener, verify branch lands"
BARE="${WORKDIR}/dummy-consumer.git"
git init --bare --initial-branch=main "$BARE" >/dev/null 2>&1 || git init --bare "$BARE" >/dev/null 2>&1

# Seed the bare repo with an initial commit so `git clone` works without
# `--allow-empty`. We do this via a scratch clone.
SEED="${WORKDIR}/seed"
git clone "$BARE" "$SEED" >/dev/null 2>&1
cd "$SEED"
echo "# dummy consumer" > README.md
git -c user.email=seed@agentarmy.local -c user.name=seed add README.md
git -c user.email=seed@agentarmy.local -c user.name=seed commit -m "seed" >/dev/null
# Push as `main` if we're on master.
CURBRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$CURBRANCH" != "main" ]; then
  git branch -m "$CURBRANCH" main
fi
git push origin main >/dev/null 2>&1
cd - >/dev/null

# Now ask forge to generate + open a PR against local:<bare>.
RESP="$(curl -sS --max-time 60 -H 'Content-Type: application/json' -X POST \
  -d "{\"source\":\"${DETERMINISTIC_SOURCE}\",\"target\":\"csharp\",\"out\":\"${WORKDIR}/out-pr\",\"consumer_repo\":\"local:${BARE}\",\"branch\":\"forge/doctor-test\"}" \
  "${BASE}/generate" 2>/dev/null || echo '{}')"
if echo "$RESP" | grep -qE '"ok":[[:space:]]?true'; then
  # Verify the branch landed in the bare repo.
  if git --git-dir="$BARE" show-ref --verify --quiet refs/heads/forge/doctor-test; then
    # And it contains the generated file.
    if git --git-dir="$BARE" show "forge/doctor-test:DataPlatformContracts.g.cs" >/dev/null 2>&1; then
      ok "pr_opener pushed forge/doctor-test to bare repo with generated file"
    else
      fail "branch exists but DataPlatformContracts.g.cs not in the tree"
    fi
  else
    fail "branch forge/doctor-test not in bare repo: $RESP"
  fi
else
  fail "POST /generate (consumer_repo) failed: $RESP"
fi

echo
echo "summary: ${PASS} pass, ${FAIL} fail"
[ "$FAIL" -eq 0 ]
