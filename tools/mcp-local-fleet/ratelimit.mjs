// Per-principal rate limiting (in-memory leaky bucket).
//
// Why this exists:
//   - A leaked bearer token shouldn't let an attacker exfiltrate everything
//     before we can rotate. Cap the burst + sustained rate.
//   - Unauthenticated probes/scrapers shouldn't be able to enumerate
//     /healthz or /.well-known unboundedly. Anonymous bucket by IP.
//
// What this is NOT:
//   - Distributed. State lives in this process's RAM. Multiple server
//     instances behind a load balancer would each apply limits independently
//     (good enough for our 1-instance-per-target deployment model).
//   - A WAF. Targeted attackers will rotate IPs/tokens. This stops
//     casual abuse and contains damage during the rotation window.
//
// Algorithm: token bucket. Each principal gets `burst` tokens, refilled
// at `refillPerMs` per ms. Every request consumes 1 token. When empty:
// 429.

const DEFAULT_AUTHED = {
  burst: 30,            // burst capacity (any tool calls)
  refillPerMs: 60 / 60_000, // 60 tokens/min = 1 per second sustained
};
const DEFAULT_ANON = {
  burst: 20,            // /healthz + /.well-known probes
  refillPerMs: 30 / 60_000, // 30/min — generous for monitoring, brutal for scrapers
};

// Anon callers get capped harder when they fail auth: cuts the brute-force
// budget without affecting legit traffic.
const DEFAULT_AUTH_FAIL = {
  burst: 5,
  refillPerMs: 5 / 60_000, // 5/min — anyone trying 30 wrong tokens gets stalled
};

class Bucket {
  constructor({ burst, refillPerMs }) {
    this.cap = burst;
    this.tokens = burst;
    this.refill = refillPerMs;
    this.lastDrip = Date.now();
  }
  take() {
    const now = Date.now();
    const elapsed = now - this.lastDrip;
    if (elapsed > 0) {
      this.tokens = Math.min(this.cap, this.tokens + elapsed * this.refill);
      this.lastDrip = now;
    }
    if (this.tokens >= 1) {
      this.tokens -= 1;
      return { allowed: true, remaining: Math.floor(this.tokens) };
    }
    // ms until next whole token available — useful for Retry-After header.
    const retryAfterMs = Math.ceil((1 - this.tokens) / this.refill);
    return { allowed: false, retryAfterMs };
  }
}

// We carry separate bucket maps for each call class so that authed callers
// don't share a bucket with anonymous abusers from the same IP.
const buckets = {
  authed: new Map(),    // key: principal string
  anon: new Map(),      // key: remote IP
  authFail: new Map(),  // key: remote IP (failed-auth tracking)
};

// Periodically drop idle buckets so memory stays bounded under churn.
const IDLE_SWEEP_MS = 10 * 60_000;
const IDLE_THRESHOLD_MS = 30 * 60_000;
setInterval(() => {
  const now = Date.now();
  for (const map of Object.values(buckets)) {
    for (const [key, bucket] of map) {
      if (now - bucket.lastDrip > IDLE_THRESHOLD_MS) map.delete(key);
    }
  }
}, IDLE_SWEEP_MS).unref();

function takeFromMap(map, key, config) {
  let b = map.get(key);
  if (!b) { b = new Bucket(config); map.set(key, b); }
  return b.take();
}

/**
 * Charge an authenticated principal one token.
 * Returns { allowed, remaining, retryAfterMs }.
 */
export function takeAuthed(principal) {
  return takeFromMap(buckets.authed, principal || "anonymous", DEFAULT_AUTHED);
}

/**
 * Charge an anonymous request one token (by IP).
 */
export function takeAnon(ip) {
  return takeFromMap(buckets.anon, ip || "unknown", DEFAULT_ANON);
}

/**
 * Charge an auth-failure event (by IP). Use this when bearer/JWT verification
 * fails — keeps attackers from racing through token-guessing attempts.
 */
export function takeAuthFail(ip) {
  return takeFromMap(buckets.authFail, ip || "unknown", DEFAULT_AUTH_FAIL);
}

/**
 * Snapshot for diagnostics / heartbeat — counts only, no PII.
 */
export function snapshot() {
  return {
    authed_principals: buckets.authed.size,
    anon_ips: buckets.anon.size,
    auth_fail_ips: buckets.authFail.size,
  };
}
