// Cloudflare Access OIDC JWT verification.
//
// CF Access (SaaS app mode) acts as an OIDC IdP for claude.ai's MCP custom
// connector. claude.ai runs the Authorization Code flow against CF, gets an
// access token, then includes it as `Authorization: Bearer <jwt>` on every
// MCP call. This module verifies that JWT.
//
// Zero deps. Uses Node's stdlib crypto for RS256 verification + JWKS fetch.
// JWKS is fetched once and cached for an hour (CF rotates keys every ~6h).

import { createPublicKey, createVerify } from "node:crypto";

import { CF_ACCESS_ISSUER, CF_ACCESS_AUDIENCE, CF_ACCESS_EMAIL_ALLOWLIST } from "./config.mjs";

const JWKS_TTL_MS = 60 * 60 * 1000; // 1h
let jwksCache = null;
let jwksFetchedAt = 0;

async function fetchJwks() {
  const url = `${CF_ACCESS_ISSUER}/jwks`;
  const res = await fetch(url, { headers: { accept: "application/json" } });
  if (!res.ok) throw new Error(`JWKS fetch ${url} failed: ${res.status}`);
  const body = await res.json();
  if (!Array.isArray(body.keys)) throw new Error("JWKS response missing 'keys' array");
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

// JWK (RSA) → SPKI PEM via Node's createPublicKey + jwk import.
function jwkToPublicKey(jwk) {
  return createPublicKey({ key: jwk, format: "jwk" });
}

/**
 * Verify a CF Access OIDC JWT and return its claims.
 *
 * Throws on:
 *   - malformed token
 *   - unknown / missing kid (key rotated, cache stale → caller can refresh + retry)
 *   - bad signature
 *   - expired (exp), not-before (nbf), wrong issuer (iss), wrong audience (aud)
 *
 * Caller is responsible for the authorization step (e.g. email allowlist).
 */
export async function verifyAccessJwt(token, { refreshIfMiss = true } = {}) {
  if (typeof token !== "string" || token.split(".").length !== 3) {
    throw new Error("malformed JWT");
  }
  const [headerB64, payloadB64, signatureB64] = token.split(".");
  const header = b64urlDecodeJson(headerB64);
  if (header.alg !== "RS256") throw new Error(`unsupported alg ${header.alg}`);
  if (!header.kid) throw new Error("JWT header missing kid");

  let keys = await jwks();
  let jwk = keys.find((k) => k.kid === header.kid);
  if (!jwk && refreshIfMiss) {
    // Force JWKS refresh and retry once — covers the case where CF rotated keys
    // and our cache is stale.
    jwksCache = null;
    keys = await jwks();
    jwk = keys.find((k) => k.kid === header.kid);
  }
  if (!jwk) throw new Error(`no JWK matches kid ${header.kid}`);

  const pubKey = jwkToPublicKey(jwk);
  const signingInput = `${headerB64}.${payloadB64}`;
  const signature = b64urlDecode(signatureB64);
  const ok = createVerify("RSA-SHA256").update(signingInput).verify(pubKey, signature);
  if (!ok) throw new Error("JWT signature invalid");

  const claims = b64urlDecodeJson(payloadB64);

  // Issuer must match exactly.
  if (claims.iss !== CF_ACCESS_ISSUER) {
    throw new Error(`bad iss: ${claims.iss}`);
  }

  // Audience: if configured, must match. (claude.ai sends the OIDC client_id as aud.)
  if (CF_ACCESS_AUDIENCE) {
    const auds = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
    if (!auds.includes(CF_ACCESS_AUDIENCE)) {
      throw new Error(`bad aud: ${JSON.stringify(claims.aud)}`);
    }
  }

  // Time window.
  const now = Math.floor(Date.now() / 1000);
  if (typeof claims.exp === "number" && now >= claims.exp) {
    throw new Error("JWT expired");
  }
  if (typeof claims.nbf === "number" && now < claims.nbf - 30 /* 30s skew */) {
    throw new Error("JWT not yet valid");
  }

  return claims;
}

/**
 * Authorize a verified JWT against the email allowlist. Returns the matched
 * email on success; throws on no-match. Separated from verify so callers can
 * log "authn ok, authz failed" distinctly.
 */
export function authorizeByEmail(claims) {
  const email = (claims.email || "").toLowerCase();
  if (!email) throw new Error("JWT has no email claim");
  const allowed = CF_ACCESS_EMAIL_ALLOWLIST.map((e) => e.toLowerCase());
  if (!allowed.includes(email)) {
    throw new Error(`email '${email}' not in allowlist`);
  }
  return email;
}

export function isCfAccessConfigured() {
  return Boolean(CF_ACCESS_ISSUER);
}
