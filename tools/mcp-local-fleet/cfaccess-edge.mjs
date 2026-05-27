// Cloudflare Access *Self-Hosted Application* edge-enforcement support.
//
// We sit BEHIND a CF Access Application configured for mcp.untool.ai/*.
// CF Access authenticates the principal at the edge — user (email PIN or
// Managed OAuth via claude.ai Connector), service token (header-based for
// cloud microVMs), or `cloudflared access curl` — then injects a
// `Cf-Access-Jwt-Assertion` header on every forwarded request. We verify
// that JWT here (the only auth path that fires on mcp.untool.ai).
//
// Why bother verifying if CF Access already did? Defense in depth:
//   - If cloudflared / CF edge is ever bypassed (e.g. someone exposes our
//     :8765 some other way), the JWT verification prevents accidental
//     ungated access.
//   - The JWT carries the verified identity (email for user auth,
//     common_name for service tokens). We need that for audit attribution.
//
// JWT shape (CF Access Self-Hosted JWT, distinct from SaaS-app OIDC):
//   iss: https://<team-domain>.cloudflareaccess.com
//   aud: the application's AUD tag (from CF Access app config)
//   email: <user-email>  (only for user-auth requests)
//   common_name: <service-token-id>  (only for service-token requests)
//   sub: identity hash
//
// JWKS lives at: https://<team-domain>.cloudflareaccess.com/cdn-cgi/access/certs

import { createPublicKey, createVerify } from "node:crypto";

import {
  CF_ACCESS_EDGE_TEAM_DOMAIN,
  CF_ACCESS_EDGE_APP_AUD,
  CF_ACCESS_EMAIL_ALLOWLIST,
} from "./config.mjs";

const JWKS_TTL_MS = 60 * 60 * 1000; // 1h
let jwksCache = null;
let jwksFetchedAt = 0;

function teamJwksUrl() {
  return `https://${CF_ACCESS_EDGE_TEAM_DOMAIN}/cdn-cgi/access/certs`;
}
function expectedIssuer() {
  return `https://${CF_ACCESS_EDGE_TEAM_DOMAIN}`;
}

async function fetchJwks() {
  const url = teamJwksUrl();
  const res = await fetch(url, { headers: { accept: "application/json" } });
  if (!res.ok) throw new Error(`Edge JWKS fetch ${url} failed: ${res.status}`);
  const body = await res.json();
  if (!Array.isArray(body.keys)) throw new Error("Edge JWKS missing 'keys' array");
  return body.keys;
}
async function jwks() {
  if (!jwksCache || Date.now() - jwksFetchedAt > JWKS_TTL_MS) {
    jwksCache = await fetchJwks();
    jwksFetchedAt = Date.now();
  }
  return jwksCache;
}

function b64urlDecode(s) {
  return Buffer.from(s.replace(/-/g, "+").replace(/_/g, "/"), "base64");
}
function b64urlDecodeJson(s) {
  return JSON.parse(b64urlDecode(s).toString("utf8"));
}
function jwkToPublicKey(jwk) {
  return createPublicKey({ key: jwk, format: "jwk" });
}

/**
 * Verify a CF Access Self-Hosted JWT (from the Cf-Access-Jwt-Assertion
 * header) and return its claims.
 *
 * Throws on malformed token, unknown kid, bad signature, wrong issuer,
 * wrong audience (must match configured CF_ACCESS_EDGE_APP_AUD), or
 * expired. Authorization (email allowlist, service-token allowlist) is
 * the caller's responsibility — separated for clear logging.
 */
export async function verifyEdgeJwt(token, { refreshIfMiss = true } = {}) {
  if (typeof token !== "string" || token.split(".").length !== 3) {
    throw new Error("malformed CF Access edge JWT");
  }
  const [headerB64, payloadB64, signatureB64] = token.split(".");
  const header = b64urlDecodeJson(headerB64);
  if (header.alg !== "RS256") throw new Error(`unsupported alg ${header.alg}`);
  if (!header.kid) throw new Error("Edge JWT header missing kid");

  let keys = await jwks();
  let jwk = keys.find((k) => k.kid === header.kid);
  if (!jwk && refreshIfMiss) {
    jwksCache = null;
    keys = await jwks();
    jwk = keys.find((k) => k.kid === header.kid);
  }
  if (!jwk) throw new Error(`no edge JWK matches kid ${header.kid}`);

  const pubKey = jwkToPublicKey(jwk);
  const signingInput = `${headerB64}.${payloadB64}`;
  const signature = b64urlDecode(signatureB64);
  const ok = createVerify("RSA-SHA256").update(signingInput).verify(pubKey, signature);
  if (!ok) throw new Error("Edge JWT signature invalid");

  const claims = b64urlDecodeJson(payloadB64);

  // CF Access Self-Hosted JWT issuer is the team domain root.
  if (claims.iss !== expectedIssuer()) {
    throw new Error(`bad iss: ${claims.iss}`);
  }

  // Audience MUST match the configured app AUD tag. Without this any CF
  // Access user on the team domain could call us — broken multi-tenancy.
  if (!CF_ACCESS_EDGE_APP_AUD) {
    throw new Error("CF_ACCESS_EDGE_APP_AUD not configured — refusing to accept any audience");
  }
  const auds = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  if (!auds.includes(CF_ACCESS_EDGE_APP_AUD)) {
    throw new Error(`bad aud: ${JSON.stringify(claims.aud)} (expected ${CF_ACCESS_EDGE_APP_AUD})`);
  }

  const now = Math.floor(Date.now() / 1000);
  if (typeof claims.exp === "number" && now >= claims.exp) {
    throw new Error("Edge JWT expired");
  }
  if (typeof claims.iat === "number" && now < claims.iat - 30) {
    throw new Error("Edge JWT issued in the future (clock skew?)");
  }

  return claims;
}

/**
 * Resolve the principal for an authenticated edge JWT.
 *
 * Returns one of:
 *   - { ok: true, principal: "cfaccess-edge:user:<email>" } — user auth
 *   - { ok: true, principal: "cfaccess-edge:service:<common-name>" } — service token
 *   - { ok: false, reason: "<message>" } — claims missing both identities
 *
 * For user auth, email must be in the allowlist (same allowlist the SaaS-app
 * OIDC path uses). Service tokens are accepted on common_name presence
 * alone — CF Access's policy gating already restricts which service tokens
 * can reach our app, so no app-side allowlist is needed (you control which
 * tokens exist via the CF dashboard).
 */
export function resolveEdgePrincipal(claims) {
  // Service token: common_name is set, email is empty.
  if (claims.common_name && !claims.email) {
    return { ok: true, principal: `cfaccess-edge:service:${claims.common_name}` };
  }
  // User auth: email is set. Re-check the email allowlist as defense in
  // depth (CF Access policy should have already gated it).
  if (claims.email) {
    const email = claims.email.toLowerCase();
    const allowed = CF_ACCESS_EMAIL_ALLOWLIST.map((e) => e.toLowerCase());
    if (!allowed.includes(email)) {
      return { ok: false, reason: `email '${email}' not in allowlist` };
    }
    return { ok: true, principal: `cfaccess-edge:user:${email}` };
  }
  return { ok: false, reason: "edge JWT has neither email nor common_name claim" };
}

export function isEdgeConfigured() {
  return Boolean(CF_ACCESS_EDGE_TEAM_DOMAIN && CF_ACCESS_EDGE_APP_AUD);
}
