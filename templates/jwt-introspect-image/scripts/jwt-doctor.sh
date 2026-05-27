#!/usr/bin/env sh
# AgentArmy jwt-introspect doctor.
#
# Proves five things end-to-end (per image.json doctor.proves):
#   1. readiness                  — /healthz returns 200 with jwks_reachable=true
#   2. valid-token-returns-claims — POST /introspect of a freshly-minted JWT
#                                   returns {active:true, claims:{sub:...}}
#   3. tampered-rejected          — POST a sig-mutated JWT -> 401
#   4. expired-rejected           — POST a 60s-stale JWT (leeway=0) -> 401
#   5. leeway-honored             — restart container with leeway=60, POST a
#                                   30s-stale JWT -> 200
#
# The doctor mints its own RSA keypair + JWKS + JWTs so we don't depend on
# an external IdP. The JWKS is served by a tiny python http.server bound to
# the docker bridge so the introspect container can fetch it via host.docker.internal.
#
# Usage:
#   ./scripts/jwt-doctor.sh
#
# Env overrides:
#   HOST       — introspect host (default: localhost)
#   PORT       — introspect port (default: 8084)
#   JWKS_PORT  — local JWKS http.server port (default: 8085)
#   PYTHON_BIN — python interpreter (default: python -> python3)
set -eu

HOST="${HOST:-localhost}"
PORT="${PORT:-8084}"
JWKS_PORT="${JWKS_PORT:-8085}"
BASE="http://${HOST}:${PORT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then PYTHON_BIN=python3; fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "FATAL: no python interpreter on PATH" >&2
  exit 1
fi

# Use python's tempfile.mkdtemp so the path is whatever python natively uses
# (avoids the /tmp-mismatch on Git Bash + Windows-native python where Bash's
# /tmp != python's /tmp). All subsequent python calls use the same path.
if [ -z "${WORKDIR:-}" ]; then
  WORKDIR="$("$PYTHON_BIN" -c "import tempfile; print(tempfile.mkdtemp(prefix='jwt-doctor.'))")"
fi

PASS=0
FAIL=0
ok()   { printf "  \033[32mPASS\033[0m %s\n" "$1"; PASS=$((PASS+1)); }
fail() { printf "  \033[31mFAIL\033[0m %s\n" "$1"; FAIL=$((FAIL+1)); }

# Track child PIDs + temp resources to clean up on exit.
JWKS_PID=""
cleanup() {
  if [ -n "$JWKS_PID" ] && kill -0 "$JWKS_PID" 2>/dev/null; then
    kill "$JWKS_PID" 2>/dev/null || true
    wait "$JWKS_PID" 2>/dev/null || true
  fi
  # Use python's shutil to handle both POSIX + Win paths uniformly.
  if [ -n "${WORKDIR:-}" ]; then
    "$PYTHON_BIN" -c "import shutil,sys; shutil.rmtree(sys.argv[1], ignore_errors=True)" "$WORKDIR" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "agentarmy jwt-introspect doctor"
echo "  base:      ${BASE}"
echo "  jwks:      http://localhost:${JWKS_PORT}/jwks.json"
echo "  workdir:   ${WORKDIR}"
echo

# ---------------------------------------------------------------------------
# Step 0: mint an RSA keypair + JWKS + 3 JWTs (valid, expired, tampered).
# Done in one python invocation so we share the RSA key in-process.
# ---------------------------------------------------------------------------
echo "[0/5] minting test RSA keypair + JWKS + JWTs"
"$PYTHON_BIN" - "$WORKDIR" <<'PYEOF'
import base64
import json
import sys
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt

workdir = sys.argv[1]

# Generate an RSA-2048 keypair. Same kty/use/alg the introspect sidecar will
# verify against (RS256 is in JWT_ALGORITHMS default).
priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
pub = priv.public_key()

# Build a JWKS doc with one key. PyJWT can read JWKS by kid.
nums = pub.public_numbers()
def _b64u(i: int) -> str:
    b = i.to_bytes((i.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

kid = "doctor-key-1"
jwks = {
    "keys": [
        {
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": kid,
            "n": _b64u(nums.n),
            "e": _b64u(nums.e),
        }
    ]
}
with open(f"{workdir}/jwks.json", "w") as f:
    json.dump(jwks, f)

priv_pem = priv.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)
with open(f"{workdir}/priv.pem", "wb") as f:
    f.write(priv_pem)

# Common claims.
now = int(time.time())
issuer = "https://doctor.agentarmy.local/"
audience = "agentarmy-spokes"
sub = "user-doctor-001"

def mint(claims):
    return jwt.encode(
        claims, priv_pem, algorithm="RS256", headers={"kid": kid}
    )

valid = mint({"iss": issuer, "aud": audience, "sub": sub, "iat": now, "exp": now + 600})
# Expired 60s ago — outside any leeway < 60.
expired = mint({"iss": issuer, "aud": audience, "sub": sub, "iat": now - 700, "exp": now - 60})
# Expired only 30s ago — INSIDE a leeway=60 window, OUTSIDE leeway=0.
slightly_expired = mint(
    {"iss": issuer, "aud": audience, "sub": sub, "iat": now - 60, "exp": now - 30}
)

# Tamper the signature: flip a char in the MIDDLE of the signature segment.
# (Last-char tampering doesn't always change the decoded bytes because the
# trailing base64url char may carry only padding bits that PyJWT ignores.)
# JWT format: header.payload.signature — mutate one char of the signature.
parts = valid.split(".")
sig = parts[2]
mid = len(sig) // 2
alt = "A" if sig[mid] != "A" else "B"
tampered_sig = sig[:mid] + alt + sig[mid + 1 :]
tampered = ".".join([parts[0], parts[1], tampered_sig])

bundle = {
    "issuer": issuer,
    "audience": audience,
    "sub": sub,
    "valid": valid,
    "expired": expired,
    "slightly_expired": slightly_expired,
    "tampered": tampered,
}
with open(f"{workdir}/tokens.json", "w") as f:
    json.dump(bundle, f)

print(f"  minted JWKS + 4 tokens (sub={sub})")
PYEOF

# Read the issuer/audience/sub/tokens back. WORKDIR may be a Win32 path with
# backslashes that are illegal in inline python string literals — so pass it
# as argv[1] (raw) instead of interpolating into the source. A single python
# call extracts everything; shell parses the key=value lines.
TOKENS_OUT="$("$PYTHON_BIN" - "$WORKDIR/tokens.json" <<'PYEOF'
import json, sys
b = json.load(open(sys.argv[1]))
for k in ("issuer", "audience", "sub", "valid", "expired", "slightly_expired", "tampered"):
    print(f"{k}\t{b[k]}")
PYEOF
)"
# Tab-separated so JWTs (no tabs inside) round-trip cleanly.
ISSUER="$(printf '%s\n' "$TOKENS_OUT" | awk -F'\t' '$1=="issuer"{print $2}')"
AUDIENCE="$(printf '%s\n' "$TOKENS_OUT" | awk -F'\t' '$1=="audience"{print $2}')"
EXPECTED_SUB="$(printf '%s\n' "$TOKENS_OUT" | awk -F'\t' '$1=="sub"{print $2}')"
TOKEN_VALID="$(printf '%s\n' "$TOKENS_OUT" | awk -F'\t' '$1=="valid"{print $2}')"
TOKEN_EXPIRED="$(printf '%s\n' "$TOKENS_OUT" | awk -F'\t' '$1=="expired"{print $2}')"
TOKEN_SLIGHTLY_EXPIRED="$(printf '%s\n' "$TOKENS_OUT" | awk -F'\t' '$1=="slightly_expired"{print $2}')"
TOKEN_TAMPERED="$(printf '%s\n' "$TOKENS_OUT" | awk -F'\t' '$1=="tampered"{print $2}')"

# ---------------------------------------------------------------------------
# Step 0b: serve JWKS on JWKS_PORT bound to 0.0.0.0 so docker can reach it
# via host.docker.internal (Docker Desktop) / host-gateway (Linux).
# ---------------------------------------------------------------------------
echo "[0/5] starting JWKS server on :${JWKS_PORT}"
# --directory points the server at WORKDIR without changing the shell's CWD;
# important on Windows where WORKDIR may be a Win32 path that confuses `cd`.
"$PYTHON_BIN" -m http.server "$JWKS_PORT" --bind 0.0.0.0 --directory "$WORKDIR" \
  >"$WORKDIR/jwks.log" 2>&1 &
JWKS_PID=$!

# Wait for the JWKS server to start.
JWKS_OK="false"
for i in 1 2 3 4 5 6 7 8 9 10; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 "http://localhost:${JWKS_PORT}/jwks.json" 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then JWKS_OK="true"; break; fi
  sleep 1
done
if [ "$JWKS_OK" != "true" ]; then
  echo "FATAL: local JWKS server didn't come up on :${JWKS_PORT}" >&2
  cat "$WORKDIR/jwks.log" >&2 || true
  exit 1
fi

# The introspect container needs to reach the host's JWKS port. Containers
# started with --add-host=host.docker.internal:host-gateway resolve it on Linux,
# and Docker Desktop sets it natively on Mac/Windows.
JWKS_URL_FOR_CONTAINER="http://host.docker.internal:${JWKS_PORT}/jwks.json"

# ---------------------------------------------------------------------------
# Helper: wait for introspect /healthz with given env, retry until ready.
# ---------------------------------------------------------------------------
wait_for_healthz() {
  expected_jwks_reachable="$1"
  for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    body="$(curl -sS --max-time 3 "${BASE}/healthz" 2>/dev/null || echo '{}')"
    if [ "$expected_jwks_reachable" = "true" ]; then
      if echo "$body" | grep -qE '"jwks_reachable"[[:space:]]*:[[:space:]]*true' 2>/dev/null; then
        return 0
      fi
    else
      if echo "$body" | grep -q '"ok"' 2>/dev/null; then
        return 0
      fi
    fi
    sleep 1
  done
  return 1
}

# ---------------------------------------------------------------------------
# 1. readiness — /healthz 200 + jwks_reachable=true
# ---------------------------------------------------------------------------
echo
echo "[1/5] readiness — /healthz 200 with jwks_reachable=true"
if wait_for_healthz "true"; then
  ok "/healthz reports jwks_reachable=true within 15s"
else
  fail "/healthz never reported jwks_reachable=true"
  body="$(curl -sS --max-time 3 "${BASE}/healthz" 2>/dev/null || echo '{}')"
  echo "  last /healthz body: $body"
fi

# ---------------------------------------------------------------------------
# Helper: POST a token, capture HTTP status + body.
# Sets globals INT_CODE and INT_BODY (avoids subshell variable scoping).
# ---------------------------------------------------------------------------
post_introspect() {
  payload_token="$1"
  # Build JSON safely via python to avoid shell-escaping the JWT.
  payload="$("$PYTHON_BIN" -c "import json,sys; print(json.dumps({'token': sys.argv[1]}))" "$payload_token")"
  INT_CODE="$(curl -sS -o "$WORKDIR/resp.json" -w '%{http_code}' --max-time 10 \
    -H 'Content-Type: application/json' \
    -X POST -d "$payload" \
    "${BASE}/introspect" 2>/dev/null || echo 000)"
  INT_BODY="$(cat "$WORKDIR/resp.json" 2>/dev/null || echo '{}')"
}

# ---------------------------------------------------------------------------
# 2. valid-token-returns-claims
# ---------------------------------------------------------------------------
echo
echo "[2/5] valid-token-returns-claims — POST /introspect with fresh JWT"
post_introspect "$TOKEN_VALID"
if [ "$INT_CODE" = "200" ]; then
  if echo "$INT_BODY" | grep -qE '"active"[[:space:]]*:[[:space:]]*true' && \
     echo "$INT_BODY" | grep -q "\"sub\":[[:space:]]*\"${EXPECTED_SUB}\""; then
    ok "200 + active:true + sub=${EXPECTED_SUB}"
  else
    fail "200 but body missing active:true / sub=${EXPECTED_SUB}: ${INT_BODY}"
  fi
else
  fail "expected 200 got ${INT_CODE}: ${INT_BODY}"
fi

# ---------------------------------------------------------------------------
# 3. tampered-rejected
# ---------------------------------------------------------------------------
echo
echo "[3/5] tampered-rejected — POST /introspect with mutated signature"
post_introspect "$TOKEN_TAMPERED"
if [ "$INT_CODE" = "401" ]; then
  if echo "$INT_BODY" | grep -qE '"active"[[:space:]]*:[[:space:]]*false'; then
    ok "401 + active:false on signature mismatch"
  else
    fail "401 but body missing active:false: ${INT_BODY}"
  fi
else
  fail "expected 401 got ${INT_CODE}: ${INT_BODY}"
fi

# ---------------------------------------------------------------------------
# 4. expired-rejected (leeway=0)
# ---------------------------------------------------------------------------
echo
echo "[4/5] expired-rejected — POST /introspect with 60s-stale JWT (leeway=0)"
post_introspect "$TOKEN_EXPIRED"
if [ "$INT_CODE" = "401" ]; then
  if echo "$INT_BODY" | grep -iq "expired"; then
    ok "401 + error mentions 'expired'"
  else
    fail "401 but error doesn't mention 'expired': ${INT_BODY}"
  fi
else
  fail "expected 401 got ${INT_CODE}: ${INT_BODY}"
fi

# ---------------------------------------------------------------------------
# 5. leeway-honored — restart container with JWT_LEEWAY_SECONDS=60, retry the
# slightly-expired token (30s past exp).
# ---------------------------------------------------------------------------
echo
echo "[5/5] leeway-honored — restart with JWT_LEEWAY_SECONDS=60; 30s-stale JWT -> 200"
# Restart the compose service with overridden env. The wrapping setup.sh
# brings the stack up via compose; we re-run compose with the override env
# vars so the same service is recreated.
COMPOSE_FILE="${COMPOSE_FILE:-examples/compose.jwt-introspect.example.yml}"
# Resolve to absolute path relative to script dir if not absolute.
case "$COMPOSE_FILE" in
  /*) ;;
  *)
    SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
    IMAGE_DIR="$(dirname "$SCRIPT_DIR")"
    COMPOSE_FILE="${IMAGE_DIR}/${COMPOSE_FILE}"
    ;;
esac

if [ -f "$COMPOSE_FILE" ]; then
  echo "  restarting jwt-introspect with leeway=60 (compose: $(basename "$COMPOSE_FILE"))"
  JWT_LEEWAY_SECONDS=60 docker compose -f "$COMPOSE_FILE" up -d --no-deps --force-recreate jwt-introspect >/dev/null 2>&1 || {
    fail "compose restart with leeway=60 failed"
  }
  if wait_for_healthz "true"; then
    post_introspect "$TOKEN_SLIGHTLY_EXPIRED"
    if [ "$INT_CODE" = "200" ]; then
      if echo "$INT_BODY" | grep -qE '"active"[[:space:]]*:[[:space:]]*true'; then
        ok "200 + active:true — leeway honored (30s stale, leeway=60)"
      else
        fail "200 but body missing active:true: ${INT_BODY}"
      fi
    else
      fail "expected 200 got ${INT_CODE}: ${INT_BODY}"
    fi
    # Restore leeway=0 for hygiene (next doctor run sees the default).
    JWT_LEEWAY_SECONDS=0 docker compose -f "$COMPOSE_FILE" up -d --no-deps --force-recreate jwt-introspect >/dev/null 2>&1 || true
  else
    fail "introspect didn't come back healthy after leeway=60 restart"
  fi
else
  fail "compose file not found at $COMPOSE_FILE — can't restart with new leeway"
fi

echo
echo "summary: ${PASS} pass, ${FAIL} fail"
[ "$FAIL" -eq 0 ]
