// Server-side tool registry filter.
//
// One server instance carries one deployment label (`INSTANCE_TARGET` from
// config.mjs — set via MCP_TARGET env, default `local-home`). Tools are
// universal by default; if a tool declares `availableOn: [...]`, it's only
// exposed when the instance target is in that list.
//
// Keeps tools.mjs free of per-instance config so a single codebase can
// power many MCP server instances with no source changes.

import { INSTANCE_TARGET } from "./config.mjs";
import { TOOLS as ALL_TOOLS } from "./tools.mjs";

function isAvailable(tool) {
  if (!Array.isArray(tool.availableOn)) return true; // universal
  return tool.availableOn.includes(INSTANCE_TARGET);
}

export const TOOLS = ALL_TOOLS.filter(isAvailable);
export const INSTANCE = { target: INSTANCE_TARGET };

export const REGISTRY_SUMMARY = {
  instance_target: INSTANCE_TARGET,
  enablement_source: process.env.MCP_TARGET ? "MCP_TARGET env" : "default",
  exposed: TOOLS.length,
  hidden_by_target: ALL_TOOLS.length - TOOLS.length,
};

export function findTool(name) { return TOOLS.find((t) => t.name === name); }
