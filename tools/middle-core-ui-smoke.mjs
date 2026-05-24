#!/usr/bin/env node

const baseUrl = process.argv[2] ?? "http://127.0.0.1:18001";

async function getJson(path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, options);
  const body = await response.text();
  let payload;
  try {
    payload = JSON.parse(body);
  } catch {
    throw new Error(`${path} did not return JSON: ${body.slice(0, 160)}`);
  }

  return { response, payload };
}

async function getText(path) {
  const response = await fetch(`${baseUrl}${path}`);
  const body = await response.text();
  return { response, body };
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const health = await getJson("/health");
assert(health.response.ok, "/health must return HTTP 200");
assert(health.payload.status === "ok", "/health must report ok");

const model = await getJson("/model");
assert(model.response.ok, "/model must return HTTP 200");
assert(model.payload.model_id === "middle-core-runtime-prototype", "/model must report the generated model id");
assert(model.payload.state_machine_count === 9, "/model must expose 9 generated state machines");

const demo = await getText("/model/demo");
assert(demo.response.ok, "/model/demo must return HTTP 200");
for (const text of [
  "Knowledge Drop Scenario Lab",
  "Run success path",
  "Run disabled-handler path",
  "Runtime Object Graph",
  "Step Evidence",
  "Evidence Output"
]) {
  assert(demo.body.includes(text), `/model/demo missing visible test text: ${text}`);
}

const run = await getJson("/model/scenarios/knowledge-drop/run");
assert(run.response.ok, "knowledge-drop success path must return HTTP 200");
assert(run.payload.status === "passed", "knowledge-drop must pass");
assert(run.payload.graph.objects.length === 6, "knowledge-drop must create 6 graph objects");
assert(run.payload.graph.edges.length === 5, "knowledge-drop must create 5 graph edges");
assert(run.payload.evidence.status === "complete", "knowledge-drop must complete evidence");

const failure = await getJson("/model/scenarios/knowledge-drop/run?disableLastHandler=true");
assert(failure.response.status === 400, "disabled-handler path must return HTTP 400");
assert(failure.payload.status === "failed", "disabled-handler path must fail cleanly");
assert(failure.payload.evidence === null, "disabled-handler path must not create evidence");

console.log(JSON.stringify({
  status: "passed",
  base_url: baseUrl,
  demo_url: `${baseUrl}/model/demo`,
  model_id: model.payload.model_id,
  state_machines: model.payload.state_machine_count,
  success_objects: run.payload.graph.objects.length,
  success_edges: run.payload.graph.edges.length,
  evidence_status: run.payload.evidence.status,
  failure_status: failure.response.status
}, null, 2));
