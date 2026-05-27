#!/usr/bin/env sh
# AgentArmy local-embedder doctor.
#
# Proves three things against a running container (per image.json):
#   1. readiness         — /healthz returns 200 + model loaded after warmup
#   2. embed-endpoint-ok — POST /v1/embeddings returns a vector
#   3. vector-dim-matches-model — vector has the declared dimension and a
#      finite, non-zero L2 norm
#
# Usage:
#   ./scripts/embedder-doctor.sh           # default localhost:8082
#   HOST=embedder PORT=8082 ./scripts/embedder-doctor.sh   # in-compose
set -eu

HOST="${HOST:-localhost}"
PORT="${PORT:-8082}"
BASE="http://${HOST}:${PORT}"

PASS=0
FAIL=0
ok()   { printf "  \033[32mPASS\033[0m %s\n" "$1"; PASS=$((PASS+1)); }
fail() { printf "  \033[31mFAIL\033[0m %s\n" "$1"; FAIL=$((FAIL+1)); }

echo "agentarmy local-embedder doctor"
echo "  base: ${BASE}"
echo

# 1. readiness — first call triggers lazy model load. Give it up to 90s. ----
echo "[1/3] readiness — waiting for model to load (POST /v1/embeddings warmup)"
WARMUP_OK="false"
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18; do
  http_code="$(curl -sS -o /tmp/embedder-warm.json -w '%{http_code}' --max-time 30 -H 'Content-Type: application/json' -X POST -d '{"model":"warmup","input":"hello"}' "${BASE}/v1/embeddings" 2>/dev/null || echo 000)"
  if [ "$http_code" = "200" ]; then
    WARMUP_OK="true"
    break
  fi
  echo "  attempt $i: HTTP ${http_code} — retrying in 5s"
  sleep 5
done
if [ "$WARMUP_OK" = "true" ]; then
  ok "model loaded; warmup embed succeeded"
else
  fail "warmup never returned 200 in 18 attempts (~90s)"
  echo "summary: ${PASS} pass, ${FAIL} fail"
  exit 1
fi

# Check /healthz also surfaces the loaded model.
hc="$(curl -sS --max-time 5 "${BASE}/healthz" 2>/dev/null || echo '{}')"
if echo "$hc" | grep -qE '"model_loaded"[[:space:]]*:[[:space:]]*true' 2>/dev/null; then
  ok "/healthz reports model_loaded=true"
else
  fail "/healthz does not report model_loaded=true (got: ${hc})"
fi

# 2. embed endpoint — single string input -----------------------------------
echo
echo "[2/3] embed endpoint — POST /v1/embeddings with a known sentence"
PAYLOAD='{"model":"BAAI/bge-small-en-v1.5","input":"AgentArmy local embedder smoke test."}'
RESP="$(curl -sS --max-time 30 -H 'Content-Type: application/json' -X POST -d "$PAYLOAD" "${BASE}/v1/embeddings" 2>/dev/null || echo '{}')"
if echo "$RESP" | grep -q '"embedding"'; then
  ok "response contains an embedding vector"
else
  fail "response missing embedding field: ${RESP}"
fi

# 3. vector dimension + L2 norm finite + nonzero ----------------------------
echo
echo "[3/3] vector dim matches model + L2 norm finite/nonzero"
# Use python for the math — it's already in the image and a hard dep.
PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then PYTHON_BIN=python3; fi
EXPECTED_DIM="$(echo "$hc" | "$PYTHON_BIN" -c "import sys,json; print(json.load(sys.stdin).get('embedding_dim',0))" 2>/dev/null || echo 0)"
RESULT="$(echo "$RESP" | "$PYTHON_BIN" -c "
import json, sys, math
d = json.load(sys.stdin)
vec = d['data'][0]['embedding']
dim = len(vec)
norm = math.sqrt(sum(x*x for x in vec))
finite = all(math.isfinite(x) for x in vec)
print(f'{dim} {norm:.6f} {finite}')
" 2>/dev/null || echo 'FAIL')"

if [ "$RESULT" = "FAIL" ]; then
  fail "could not parse embedding response"
else
  DIM="$(echo "$RESULT" | awk '{print $1}')"
  NORM="$(echo "$RESULT" | awk '{print $2}')"
  FINITE="$(echo "$RESULT" | awk '{print $3}')"
  if [ "$DIM" = "$EXPECTED_DIM" ] && [ "$EXPECTED_DIM" != "0" ]; then
    ok "dim=${DIM} matches model's declared embedding_dim=${EXPECTED_DIM}"
  else
    fail "dim=${DIM} != declared embedding_dim=${EXPECTED_DIM}"
  fi
  if [ "$FINITE" = "True" ] && [ "$NORM" != "0.000000" ]; then
    ok "L2 norm=${NORM} is finite + non-zero"
  else
    fail "L2 norm=${NORM} finite=${FINITE} — degenerate vector"
  fi
fi

echo
echo "summary: ${PASS} pass, ${FAIL} fail"
[ "$FAIL" -eq 0 ]
