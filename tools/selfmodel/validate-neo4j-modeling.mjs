#!/usr/bin/env node
// Validation harness for the neo4j-data-modeling MCP server (Docker MCP Toolkit).
//
// Drives `mcp/neo4j-data-modeling` over MCP stdio to prove the RDF↔LPG round-trip
// (ARC-ADR-041) on the platform self-model: OWL Turtle -> property-graph data-model
// -> validate -> Cypher ingest. No database required (design-time tool, no secret).
//
// Usage:
//   node tools/selfmodel/validate-neo4j-modeling.mjs list          # tools/list (schemas)
//   node tools/selfmodel/validate-neo4j-modeling.mjs roundtrip     # full round-trip + report
//
// Exit 0 = PASS, non-zero = FAIL. Reproducible; the only dependency is Docker.

import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(__dirname, '..', '..');
const TTL = resolve(REPO, 'ontology/platform-self-model/semantic/model.gufo.ttl');
const OUT_DIR = resolve(REPO, 'ontology/platform-self-model/generated');
const IMAGE = 'mcp/neo4j-data-modeling';
const mode = process.argv[2] || 'list';

// --- Minimal MCP stdio client: spawn the server, do the handshake, run calls. ---
class McpStdio {
  constructor(image) {
    this.proc = spawn('docker', ['run', '-i', '--rm', image], { stdio: ['pipe', 'pipe', 'pipe'] });
    this.buf = '';
    this.pending = new Map();
    this.nextId = 1;
    this.proc.stdout.on('data', (d) => this._onData(d));
    this.proc.stderr.on('data', (d) => process.env.DEBUG && process.stderr.write(`[srv] ${d}`));
  }
  _onData(d) {
    this.buf += d.toString();
    let nl;
    while ((nl = this.buf.indexOf('\n')) >= 0) {
      const line = this.buf.slice(0, nl).trim();
      this.buf = this.buf.slice(nl + 1);
      if (!line) continue;
      let msg;
      try { msg = JSON.parse(line); } catch { continue; }
      if (msg.id != null && this.pending.has(msg.id)) {
        const { resolve: res, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? reject(new Error(JSON.stringify(msg.error))) : res(msg.result);
      }
    }
  }
  _send(obj) { this.proc.stdin.write(JSON.stringify(obj) + '\n'); }
  notify(method, params) { this._send({ jsonrpc: '2.0', method, params }); }
  request(method, params) {
    const id = this.nextId++;
    this._send({ jsonrpc: '2.0', id, method, params });
    return new Promise((res, reject) => {
      this.pending.set(id, { resolve: res, reject });
      setTimeout(() => this.pending.has(id) && reject(new Error(`timeout: ${method}`)), 60000);
    });
  }
  async handshake() {
    await this.request('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'selfmodel-validate', version: '0.1.0' },
    });
    this.notify('notifications/initialized', {});
  }
  close() { try { this.proc.stdin.end(); this.proc.kill(); } catch {} }
}

const textOf = (result) =>
  (result?.content || []).filter((c) => c.type === 'text').map((c) => c.text).join('\n');

async function main() {
  const cli = new McpStdio(IMAGE);
  try {
    await cli.handshake();

    if (mode === 'list') {
      const { tools } = await cli.request('tools/list', {});
      for (const t of tools) {
        const req = t.inputSchema?.required || [];
        const props = Object.keys(t.inputSchema?.properties || {});
        console.log(`- ${t.name}(${props.join(', ')})${req.length ? `  required: ${req.join(',')}` : ''}`);
      }
      return 0;
    }

    if (mode === 'roundtrip') {
      mkdirSync(OUT_DIR, { recursive: true });
      const ttl = readFileSync(TTL, 'utf8');
      const checks = [];

      // 1) OWL Turtle -> property-graph data model
      const loaded = await cli.request('tools/call', {
        name: 'load_from_owl_turtle',
        arguments: { owl_turtle_str: ttl },
      });
      const dataModelText = textOf(loaded);
      let dataModel;
      try { dataModel = JSON.parse(dataModelText); } catch { dataModel = dataModelText; }
      const nNodes = dataModel?.nodes?.length ?? null;
      const nRels = dataModel?.relationships?.length ?? null;
      checks.push(['load_from_owl_turtle', !loaded.isError && !!dataModelText, `${nNodes ?? '?'} node(s), ${nRels ?? '?'} rel(s)`]);
      writeFileSync(resolve(OUT_DIR, 'selfmodel.neo4j-datamodel.json'),
        typeof dataModel === 'string' ? dataModel : JSON.stringify(dataModel, null, 2));

      // 2) validate the resulting data model
      const validated = await cli.request('tools/call', {
        name: 'validate_data_model',
        arguments: { data_model: dataModel },
      });
      const vText = textOf(validated);
      checks.push(['validate_data_model', !validated.isError, vText.slice(0, 120) || '(ok)']);

      // 3) generate Cypher ingest (constraints for whole model + per-node) — runs against ArcadeDB (openCypher)
      const constraints = await cli.request('tools/call', {
        name: 'get_constraints_cypher_queries',
        arguments: { data_model: dataModel },
      });
      const cypherText = textOf(constraints);
      checks.push(['get_constraints_cypher_queries', !constraints.isError && /CONSTRAINT|CREATE/i.test(cypherText), `${cypherText.split('\n').filter(Boolean).length} stmt(s)`]);

      let nodeCypher = '';
      if (dataModel?.nodes?.length) {
        const nc = await cli.request('tools/call', {
          name: 'get_node_cypher_ingest_query',
          arguments: { node: dataModel.nodes[0] },
        });
        nodeCypher = textOf(nc);
        checks.push(['get_node_cypher_ingest_query', !nc.isError && /MERGE|CREATE/i.test(nodeCypher), nodeCypher.split('\n')[0]?.slice(0, 80) || '']);
      }
      writeFileSync(resolve(OUT_DIR, 'selfmodel.ingest.cypher'),
        `// constraints\n${cypherText}\n\n// sample node ingest\n${nodeCypher}\n`);

      // 4) project back to OWL Turtle (round-trip the other direction)
      const owl = await cli.request('tools/call', {
        name: 'export_to_owl_turtle',
        arguments: { data_model: dataModel },
      });
      const owlText = textOf(owl);
      checks.push(['export_to_owl_turtle', !owl.isError && (owlText.includes('@prefix') || owlText.includes('owl:')), `${owlText.length} chars`]);
      writeFileSync(resolve(OUT_DIR, 'selfmodel.roundtrip.ttl'), owlText);

      const pass = checks.every((c) => c[1]);
      console.log('\nneo4j-data-modeling round-trip on platform-self-model:');
      for (const [name, ok, note] of checks) console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}  — ${note}`);
      console.log(pass ? '\nRESULT: PASS' : '\nRESULT: FAIL');
      return pass ? 0 : 1;
    }

    console.error(`unknown mode: ${mode}`);
    return 2;
  } finally {
    cli.close();
  }
}

main().then((c) => process.exit(c)).catch((e) => { console.error(e.message); process.exit(1); });
