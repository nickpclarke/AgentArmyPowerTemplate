#!/usr/bin/env node
// local-fleet MCP server (HTTP + JSON-RPC 2.0).
//
// One endpoint: POST /mcp — accepts a JSON-RPC request, returns a JSON-RPC
// response. Authorization: Bearer <token> required on every call. Bound to
// 127.0.0.1 by default — only reachable from the public web when explicitly
// fronted by `tools/tunnel.mjs start --name mcp`.
//
// Supported JSON-RPC methods (subset of MCP):
//   - initialize
//   - tools/list
//   - tools/call
//   - notifications/initialized  (no response)
//
// Run:
//   node tools/mcp-local-fleet/server.mjs                 # port 8765
//   MCP_PORT=8123 node tools/mcp-local-fleet/server.mjs   # override

import { createServer } from "node:http";
// timingSafeEqual is used inside tokens.mjs now; no direct import needed here.

import { PORT, HOST, resolveBearerToken } from "./config.mjs";
import { TOOLS, findTool, INSTANCE, REGISTRY_SUMMARY } from "./registry.mjs";
import { newAuditId, logCall, logSecurityEvent } from "./audit.mjs";
import { verifyEdgeJwt, resolveEdgePrincipal, isEdgeConfigured } from "./cfaccess-edge.mjs";
import { takeAuthed, takeAnon, takeAuthFail } from "./ratelimit.mjs";
import { loadAllTokens, verifyAgainstRegistry } from "./tokens.mjs";

const PROTOCOL_VERSION = "2025-03-26"; // MCP protocol version we advertise
const SERVER_INFO = { name: "agentarmy.local-fleet", version: "0.1.0" };

// Token registry — loaded once at startup. Includes the legacy
// `local-fleet-mcp-key` (as principal "static-legacy") PLUS any per-agent
// tokens stored under the `local-fleet-mcp-token-*` naming convention.
// To rotate: edit the KV secrets and restart this process.
//
// We still call resolveBearerToken() so the legacy bootstrap (generate + print
// on first run) keeps working for fresh installs.
resolveBearerToken();
const TOKEN_REGISTRY = loadAllTokens();

// ---------- auth ------------------------------------------------------------
// Two auth paths, in priority order:
//   1. CF Access EDGE JWT (`Cf-Access-Jwt-Assertion` header) — preferred
//      for ANY request that came through CF Access enforcement. Injected
//      by CF Access after it verified user / service-token / managed-OAuth
//      auth at the edge. Carries identity (email for users, common_name for
//      service tokens). This is the only path that fires on `mcp.untool.ai`.
//   2. Static bearer registry (`Authorization: Bearer <token>`) — local
//      laptop debug + cloud agents using KV-stored tokens. Falling back
//      here means the request did NOT go through CF Access (loopback
//      direct, or a future non-CF deployment target).
//
// The legacy CF Access SaaS-OIDC JWT path was removed once Managed OAuth
// on the Self-Hosted app replaced it (claude.ai web-UI Connector now
// authenticates at the edge → arrives with a `Cf-Access-Jwt-Assertion`
// header verified by path 1). See memory: cf-managed-oauth-for-mcp.
//
// Returns { ok, principal } on success; { ok: false, reason } on failure.
async function checkAuth(req) {
  // 1) CF Access edge JWT — present iff CF Access fronted the request.
  const edgeJwt = req.headers["cf-access-jwt-assertion"];
  if (edgeJwt && isEdgeConfigured()) {
    try {
      const claims = await verifyEdgeJwt(edgeJwt);
      const r = resolveEdgePrincipal(claims);
      if (r.ok) return { ok: true, principal: r.principal };
      return { ok: false, reason: r.reason };
    } catch (e) {
      // Edge JWT was present but failed — refuse outright (we know the
      // request came through CF Access, so it should be valid). Do NOT
      // fall through to bearer; that would let an attacker bypass edge
      // enforcement by sending a malformed edge JWT alongside a valid
      // bearer.
      return { ok: false, reason: `edge JWT failed: ${e.message}` };
    }
  }

  const hdr = req.headers["authorization"];
  if (!hdr) return { ok: false, reason: "no authorization header" };

  // 2) Bearer fallback — try every loaded token (legacy + per-agent).
  // Returns the matched token's principal name so audit captures WHICH
  // cloud-agent identity authenticated. timingSafeEqual is per-compare.
  const tokenMatch = verifyAgainstRegistry(hdr, TOKEN_REGISTRY);
  if (tokenMatch.matched) {
    return { ok: true, principal: tokenMatch.principal };
  }
  return { ok: false, reason: "invalid bearer" };
}

// ---------- JSON-RPC --------------------------------------------------------
function rpcResult(id, result) { return { jsonrpc: "2.0", id, result }; }
function rpcError(id, code, message, data) {
  return { jsonrpc: "2.0", id, error: { code, message, ...(data ? { data } : {}) } };
}
const JSONRPC_PARSE_ERROR     = -32700;
const JSONRPC_INVALID_REQUEST = -32600;
const JSONRPC_METHOD_NOT_FOUND= -32601;
const JSONRPC_INVALID_PARAMS  = -32602;
const JSONRPC_INTERNAL_ERROR  = -32603;

// ---------- request handler --------------------------------------------------
async function handleJsonRpc(msg, remote, principal) {
  // Notifications (no id) get no response per spec.
  const isNotif = msg.id === undefined;

  if (msg.jsonrpc !== "2.0" || typeof msg.method !== "string") {
    return isNotif ? null : rpcError(msg.id ?? null, JSONRPC_INVALID_REQUEST, "invalid JSON-RPC envelope");
  }

  switch (msg.method) {
    case "initialize":
      return rpcResult(msg.id, {
        protocolVersion: PROTOCOL_VERSION,
        capabilities: { tools: { listChanged: false } },
        // _meta.target advertises this server instance's deployment label
        // at initialize too, so cloud agents can route without listing tools.
        serverInfo: { ...SERVER_INFO, _meta: { target: INSTANCE.target } },
      });

    case "notifications/initialized":
      return null; // notification — no response

    case "tools/list":
      return rpcResult(msg.id, {
        tools: TOOLS.map((t) => ({
          name: t.name,
          description: t.description,
          inputSchema: t.inputSchema,
          // MCP-2025-03-26 tool annotations let clients auto-approve safe
          // reads (readOnlyHint:true) and gate writes (destructiveHint:true).
          // claude.ai + Claude Code both honor these hints.
          ...(t.annotations ? { annotations: t.annotations } : {}),
          // _meta.target tells cloud agents which deployment environment
          // this server instance acts on (local-home / dev-cloud / etc).
          // _meta.risk is informational so agents can self-restrict.
          _meta: { target: INSTANCE.target, risk: t.risk },
        })),
      });

    case "tools/call": {
      const { name, arguments: args } = msg.params || {};
      const tool = findTool(name);
      if (!tool) return rpcError(msg.id, JSONRPC_METHOD_NOT_FOUND, `unknown tool: ${name}`);
      const auditId = newAuditId();
      const t0 = Date.now();
      try {
        const result = await tool.handler(args || {});
        logCall({ auditId, tool: name, args, result, durationMs: Date.now() - t0, remoteAddr: remote, principal });
        // MCP tools/call result shape: { content: [{type:"text", text:"..."}], isError?: bool }
        return rpcResult(msg.id, {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
          _meta: { audit_id: auditId, duration_ms: Date.now() - t0 },
        });
      } catch (e) {
        logCall({ auditId, tool: name, args, error: e, durationMs: Date.now() - t0, remoteAddr: remote });
        return rpcResult(msg.id, {
          content: [{ type: "text", text: `tool error: ${e.message || String(e)}` }],
          isError: true,
          _meta: { audit_id: auditId, duration_ms: Date.now() - t0 },
        });
      }
    }

    default:
      return isNotif ? null : rpcError(msg.id, JSONRPC_METHOD_NOT_FOUND, `unknown method: ${msg.method}`);
  }
}

// Real client IP — prefer CF/proxy headers when present, fall back to socket.
function clientIp(req) {
  return req.headers["cf-connecting-ip"]
    || req.headers["x-forwarded-for"]?.split(",")[0]?.trim()
    || req.socket.remoteAddress;
}

// Defense-in-depth response headers. JSON API so most of CSP is irrelevant,
// but cheap to add. Helps when a misconfigured proxy starts serving our
// responses as HTML (browsers respect these headers).
function setSecurityHeaders(res) {
  res.setHeader("strict-transport-security", "max-age=63072000; includeSubDomains");
  res.setHeader("x-content-type-options", "nosniff");
  res.setHeader("x-frame-options", "DENY");
  res.setHeader("referrer-policy", "no-referrer");
  res.setHeader("content-security-policy", "default-src 'none'; frame-ancestors 'none'");
  // Cache-control: API responses are per-request — never cache.
  res.setHeader("cache-control", "no-store");
}

// ---------- HTTP server ------------------------------------------------------
const server = createServer(async (req, res) => {
  setSecurityHeaders(res);
  const ip = clientIp(req);

  // Health probe — open, returns just liveness (no fleet info). Rate-limited
  // by IP so scrapers can't pound this endpoint enumerating it.
  if (req.method === "GET" && req.url === "/healthz") {
    const rl = takeAnon(ip);
    if (!rl.allowed) {
      res.writeHead(429, { "content-type": "application/json", "retry-after": String(Math.ceil(rl.retryAfterMs / 1000)) });
      res.end(JSON.stringify({ error: "rate_limited" }));
      return;
    }
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ ok: true, server: SERVER_INFO.name, version: SERVER_INFO.version }));
    return;
  }

  // NOTE: We previously served `/.well-known/oauth-protected-resource` here
  // to advertise CF Access as the authorization server for the SaaS-OIDC
  // claude.ai connector flow. With Managed OAuth now enabled on the
  // Self-Hosted Access application (`Local Fleet MCP API`), CF Access
  // intercepts and rewrites that response at the edge, so the in-server
  // handler became dead code. Removed.

  if (req.method !== "POST" || req.url !== "/mcp") {
    res.writeHead(404, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: "not found", hint: "POST /mcp with JSON-RPC 2.0 body and Authorization: Bearer <token>" }));
    return;
  }

  const auth = await checkAuth(req);
  if (!auth.ok) {
    // Anti-brute-force: failed auth attempts get their own (tighter) bucket
    // keyed by IP. Hitting empty here = many bad tokens from one source =
    // active credential-guessing attempt.
    const rlFail = takeAuthFail(ip);
    logSecurityEvent({
      kind: "auth_failed",
      ip,
      reason: auth.reason,
      ua: req.headers["user-agent"]?.slice(0, 200),
      rate_limited: !rlFail.allowed,
    });
    if (!rlFail.allowed) {
      res.writeHead(429, { "content-type": "application/json", "retry-after": String(Math.ceil(rlFail.retryAfterMs / 1000)) });
      res.end(JSON.stringify({ error: "rate_limited" }));
      return;
    }
    res.writeHead(401, { "content-type": "application/json", "www-authenticate": 'Bearer realm="local-fleet"' });
    res.end(JSON.stringify({ error: "unauthorized", reason: auth.reason }));
    return;
  }

  // Authenticated request: rate-limit per principal so a leaked token can't
  // exfiltrate everything before rotation.
  const rl = takeAuthed(auth.principal);
  if (!rl.allowed) {
    logSecurityEvent({ kind: "rate_limited", ip, principal: auth.principal });
    res.writeHead(429, { "content-type": "application/json", "retry-after": String(Math.ceil(rl.retryAfterMs / 1000)) });
    res.end(JSON.stringify({ error: "rate_limited", principal: auth.principal }));
    return;
  }

  // Stash on the request so the handler can include the principal in audit.
  req._principal = auth.principal;

  // Body cap — JSON-RPC requests are tiny; 256 KB is generous, anything larger
  // is a bug or abuse.
  const MAX_BODY = 256 * 1024;
  let received = 0;
  const chunks = [];
  let aborted = false;
  req.on("data", (c) => {
    received += c.length;
    if (received > MAX_BODY) {
      aborted = true;
      logSecurityEvent({
        kind: "body_too_large",
        ip,
        principal: req._principal,
        bytes_seen: received,
        cap: MAX_BODY,
      });
      res.writeHead(413, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: "request too large" }));
      req.destroy();
      return;
    }
    chunks.push(c);
  });
  req.on("end", async () => {
    if (aborted) return;
    let body;
    try { body = JSON.parse(Buffer.concat(chunks).toString("utf8")); }
    catch {
      res.writeHead(400, { "content-type": "application/json" });
      res.end(JSON.stringify(rpcError(null, JSONRPC_PARSE_ERROR, "parse error")));
      return;
    }
    // Prefer the cf-connecting-ip header (set by Cloudflare on tunnel calls)
    // over the raw socket address — without it, every tunneled call appears
    // to come from 127.0.0.1 and we lose all client-IP signal.
    const remote = req.headers["cf-connecting-ip"]
      || req.headers["x-forwarded-for"]?.split(",")[0]?.trim()
      || req.socket.remoteAddress;
    const principal = req._principal;
    try {
      const reply = await handleJsonRpc(body, remote, principal);
      if (reply === null) {
        res.writeHead(204);
        res.end();
        return;
      }
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify(reply));
    } catch (e) {
      res.writeHead(500, { "content-type": "application/json" });
      res.end(JSON.stringify(rpcError(body?.id ?? null, JSONRPC_INTERNAL_ERROR, e.message || "internal error")));
    }
  });
});

server.listen(PORT, HOST, () => {
  console.log(`local-fleet MCP listening on http://${HOST}:${PORT}/mcp`);
  console.log(`instance target: ${INSTANCE.target}  (override with MCP_TARGET env)`);
  console.log(`tools exposed:   ${TOOLS.length}${REGISTRY_SUMMARY.hidden_by_target ? ` (${REGISTRY_SUMMARY.hidden_by_target} hidden by availableOn)` : ""}`);
  console.log(`bearer tokens:   ${TOKEN_REGISTRY.size} (principals: ${[...TOKEN_REGISTRY.keys()].join(", ")})`);
  console.log(`expose externally: node tools/tunnel.mjs start --name mcp`);
  console.log(`stop: Ctrl-C`);
});
