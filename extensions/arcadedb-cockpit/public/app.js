const state = {
  config: null,
  graph: { nodes: [], edges: [], stats: {} },
  selectedId: null,
  db: 'knowledge',
  motion: true,
  pulse: 0,
  pointer: { x: 0, y: 0 },
}

const bootstrap = window.__ARCADE_BOOTSTRAP__ || {}

const els = {
  targetText: document.querySelector('#targetText'),
  databaseSelect: document.querySelector('#databaseSelect'),
  refreshButton: document.querySelector('#refreshButton'),
  queryJumpButton: document.querySelector('#queryJumpButton'),
  readyDot: document.querySelector('#readyDot'),
  readyText: document.querySelector('#readyText'),
  readyGauge: document.querySelector('#readyGauge'),
  latencyGauge: document.querySelector('#latencyGauge'),
  recordGauge: document.querySelector('#recordGauge'),
  edgeGauge: document.querySelector('#edgeGauge'),
  typeGauge: document.querySelector('#typeGauge'),
  commandTicker: document.querySelector('#commandTicker'),
  graphCanvas: document.querySelector('#graphCanvas'),
  emptyState: document.querySelector('#emptyState'),
  selectedType: document.querySelector('#selectedType'),
  selectedLabel: document.querySelector('#selectedLabel'),
  selectedFields: document.querySelector('#selectedFields'),
  selectedLinks: document.querySelector('#selectedLinks'),
  queryPanel: document.querySelector('#queryPanel'),
  sqlInput: document.querySelector('#sqlInput'),
  runQueryButton: document.querySelector('#runQueryButton'),
  sampleQueryButton: document.querySelector('#sampleQueryButton'),
  queryStatus: document.querySelector('#queryStatus'),
  queryOutput: document.querySelector('#queryOutput'),
  mutationMode: document.querySelector('#mutationMode'),
  pulseButton: document.querySelector('#pulseButton'),
  fitButton: document.querySelector('#fitButton'),
  motionToggle: document.querySelector('#motionToggle'),
}

const ctx = els.graphCanvas.getContext('2d')
const tones = {
  cyan: '#38e8ff',
  lime: '#a9ff45',
  magenta: '#ff4fd8',
  red: '#ff5c70',
}

init()

async function init() {
  bindEvents()
  resizeCanvas()
  await loadConfig()
  applyBootstrap()
  await refreshAll()
  requestAnimationFrame(draw)
  setInterval(refreshTelemetry, 4500)
}

function bindEvents() {
  window.addEventListener('resize', resizeCanvas)
  els.refreshButton.addEventListener('click', refreshAll)
  els.databaseSelect.addEventListener('change', () => {
    state.db = els.databaseSelect.value
    refreshAll()
  })
  els.queryJumpButton.addEventListener('click', () => els.queryPanel.scrollIntoView({ behavior: 'smooth', block: 'center' }))
  els.runQueryButton.addEventListener('click', runQuery)
  els.sampleQueryButton.addEventListener('click', () => {
    els.sqlInput.value = 'SELECT @rid AS id, source, source_id, kind, chunk_index, content FROM Chunk LIMIT 10'
    runQuery()
  })
  els.pulseButton.addEventListener('click', () => {
    state.pulse = 1
  })
  els.fitButton.addEventListener('click', seedPositions)
  els.motionToggle.addEventListener('change', () => {
    state.motion = els.motionToggle.checked
  })
  document.querySelectorAll('.rail-button').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.rail-button').forEach((item) => item.classList.remove('is-active'))
      button.classList.add('is-active')
      if (button.dataset.view === 'query') els.queryPanel.scrollIntoView({ behavior: 'smooth', block: 'center' })
      if (button.dataset.view === 'metrics') document.querySelector('.instrument-deck').scrollIntoView({ behavior: 'smooth' })
    })
  })
  els.graphCanvas.addEventListener('pointermove', (event) => {
    const rect = els.graphCanvas.getBoundingClientRect()
    state.pointer = { x: event.clientX - rect.left, y: event.clientY - rect.top }
  })
  els.graphCanvas.addEventListener('click', (event) => {
    const rect = els.graphCanvas.getBoundingClientRect()
    const hit = hitNode(event.clientX - rect.left, event.clientY - rect.top)
    if (hit) selectNode(hit.id)
  })
}

async function loadConfig() {
  state.config = bootstrap.config || await api('/api/config')
  state.db = state.config.defaultDatabase
  els.targetText.textContent = `${state.config.target} / ${state.config.defaultDatabase}`
  els.mutationMode.textContent = state.config.mutationEnabled ? 'Mutation enabled' : 'Read-only'
}

function applyBootstrap() {
  if (bootstrap.health) renderHealth(bootstrap.health)
  if (bootstrap.graph) {
    state.graph = normalizeGraph(bootstrap.graph)
    state.selectedId = state.graph.nodes[0]?.id || null
    seedPositions()
    renderStats()
    renderInspector()
    els.emptyState.classList.toggle('is-visible', state.graph.nodes.length === 0)
  }
}

async function refreshAll() {
  await Promise.allSettled([refreshHealth(), refreshDatabases()])
  await refreshGraph()
  await refreshTelemetry()
}

async function refreshHealth() {
  try {
    const health = await api('/api/health')
    renderHealth(health)
  } catch {
    els.readyDot.classList.remove('is-ready')
    els.readyText.textContent = 'Offline'
    els.readyGauge.textContent = 'Offline'
  }
}

function renderHealth(health) {
  els.readyDot.classList.toggle('is-ready', health.ready)
  els.readyText.textContent = health.ready ? 'Ready' : 'Offline'
  els.readyGauge.textContent = health.ready ? 'Ready' : 'Offline'
  els.latencyGauge.textContent = `${health.latencyMs || 0} ms`
}

async function refreshDatabases() {
  try {
    const data = await api('/api/databases')
    const databases = data.databases.length ? data.databases : [state.db]
    els.databaseSelect.innerHTML = databases.map((db) => `<option value="${escapeHtml(db)}">${escapeHtml(db)}</option>`).join('')
    els.databaseSelect.value = databases.includes(state.db) ? state.db : databases[0]
    state.db = els.databaseSelect.value
  } catch {
    els.databaseSelect.innerHTML = `<option>${escapeHtml(state.db)}</option>`
  }
}

async function refreshGraph() {
  try {
    const graph = await api(`/api/graph?db=${encodeURIComponent(state.db)}`)
    state.graph = normalizeGraph(graph)
    state.selectedId = state.graph.nodes[0]?.id || null
    seedPositions()
    renderStats()
    renderInspector()
    els.emptyState.classList.toggle('is-visible', state.graph.nodes.length === 0)
  } catch (error) {
    state.graph = { nodes: [], edges: [], stats: {}, byId: new Map() }
    els.emptyState.classList.add('is-visible')
    els.queryOutput.textContent = `Could not load graph:\n${error.message}`
    renderStats()
  }
}

async function refreshTelemetry() {
  try {
    const data = await api('/api/telemetry')
    els.commandTicker.innerHTML = data.commands.slice(-5).reverse().map((item) => (
      `<li>${escapeHtml(item.elapsedMs)} ms - ${escapeHtml(shortSql(item.sql))}</li>`
    )).join('')
    if (data.averageCommandMs) els.latencyGauge.textContent = `${data.averageCommandMs} ms`
  } catch {
    els.commandTicker.innerHTML = '<li>No telemetry yet</li>'
  }
}

function normalizeGraph(graph) {
  const nodes = graph.nodes.map((node, index) => ({
    ...node,
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    size: Number(node.size || 8),
    index,
  }))
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const edges = graph.edges.filter((edge) => byId.has(edge.from) && byId.has(edge.to))
  return { ...graph, nodes, edges, byId }
}

function seedPositions() {
  const { width, height } = els.graphCanvas.getBoundingClientRect()
  const cx = width / 2
  const cy = height / 2
  const radius = Math.max(92, Math.min(width, height) * 0.28)
  const groupCenters = {
    database: { x: cx, y: cy },
    type: { x: cx - radius * 0.25, y: cy },
    source: { x: cx - radius * 0.9, y: cy + radius * 0.3 },
    chunk: { x: cx + radius * 0.55, y: cy + radius * 0.08 },
    job: { x: cx + radius * 0.75, y: cy - radius * 0.45 },
  }
  state.graph.nodes.forEach((node, index) => {
    const sameType = state.graph.nodes.filter((candidate) => candidate.type === node.type)
    const typeIndex = sameType.findIndex((candidate) => candidate.id === node.id)
    const typeCount = Math.max(1, sameType.length)
    const angle = (typeIndex / typeCount) * Math.PI * 2
    const center = groupCenters[node.type] || groupCenters.chunk
    const localRadius = node.type === 'database' ? 0 : node.type === 'type' ? 58 : node.type === 'source' ? 118 : node.type === 'job' ? 96 : 178
    node.x = center.x + Math.cos(angle) * localRadius
    node.y = center.y + Math.sin(angle) * localRadius * 0.72
    node.tx = node.x
    node.ty = node.y
    node.vx = 0
    node.vy = 0
  })
}

function draw() {
  const rect = els.graphCanvas.getBoundingClientRect()
  ctx.clearRect(0, 0, rect.width, rect.height)
  drawGrid(rect.width, rect.height)
  if (state.motion) tickPhysics(rect.width, rect.height)
  drawEdges()
  drawNodes()
  state.pulse = Math.max(0, state.pulse - 0.018)
  requestAnimationFrame(draw)
}

function tickPhysics(width, height) {
  const nodes = state.graph.nodes
  const edges = state.graph.edges
  for (const edge of edges) {
    const a = state.graph.byId.get(edge.from)
    const b = state.graph.byId.get(edge.to)
    if (!a || !b) continue
    const dx = b.x - a.x
    const dy = b.y - a.y
    const distance = Math.max(1, Math.hypot(dx, dy))
    const target = 90 + (1 - Number(edge.weight || 0.5)) * 120
    const force = (distance - target) * 0.0009
    const fx = dx * force
    const fy = dy * force
    a.vx += fx
    a.vy += fy
    b.vx -= fx
    b.vy -= fy
  }
  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const a = nodes[i]
      const b = nodes[j]
      const dx = b.x - a.x
      const dy = b.y - a.y
      const distance = Math.max(12, Math.hypot(dx, dy))
      const push = 34 / (distance * distance)
      a.vx -= dx * push
      a.vy -= dy * push
      b.vx += dx * push
      b.vy += dy * push
    }
  }
  for (const node of nodes) {
    node.vx += ((node.tx || width / 2) - node.x) * 0.0022
    node.vy += ((node.ty || height / 2) - node.y) * 0.0022
    node.vx *= 0.88
    node.vy *= 0.88
    node.x = clamp(node.x + node.vx, 24, width - 24)
    node.y = clamp(node.y + node.vy, 58, height - 24)
  }
}

function drawGrid(width, height) {
  ctx.save()
  ctx.strokeStyle = 'rgba(56, 232, 255, 0.06)'
  ctx.lineWidth = 1
  for (let x = 0; x < width; x += 38) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
  }
  for (let y = 0; y < height; y += 38) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }
  ctx.restore()
}

function drawEdges() {
  ctx.save()
  for (const edge of state.graph.edges) {
    const a = state.graph.byId.get(edge.from)
    const b = state.graph.byId.get(edge.to)
    if (!a || !b) continue
    ctx.strokeStyle = selectedInEdge(edge) ? 'rgba(169, 255, 69, 0.82)' : 'rgba(142, 162, 173, 0.24)'
    ctx.lineWidth = selectedInEdge(edge) ? 2 : 1
    ctx.beginPath()
    ctx.moveTo(a.x, a.y)
    ctx.lineTo(b.x, b.y)
    ctx.stroke()
  }
  ctx.restore()
}

function drawNodes() {
  ctx.save()
  for (const node of state.graph.nodes) {
    const color = tones[node.tone] || tones.cyan
    const selected = node.id === state.selectedId
    const hover = hitNode(state.pointer.x, state.pointer.y)?.id === node.id
    const pulse = selected ? 8 + state.pulse * 26 : state.pulse * 10
    ctx.shadowColor = color
    ctx.shadowBlur = selected || hover ? 28 : 12
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(node.x, node.y, node.size + pulse, 0, Math.PI * 2)
    ctx.globalAlpha = 0.16
    ctx.fill()
    ctx.globalAlpha = 1
    ctx.beginPath()
    ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2)
    ctx.fill()
    ctx.shadowBlur = 0
    if (shouldLabelNode(node, selected, hover)) {
      ctx.fillStyle = '#eff7fb'
      ctx.font = `${selected ? 800 : 650} ${selected ? 13 : 12}px Inter, system-ui, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillText(node.label, node.x, node.y + node.size + 8, 170)
    }
  }
  ctx.restore()
}

function shouldLabelNode(node, selected, hover) {
  if (selected || hover) return true
  return ['database', 'type', 'source', 'job'].includes(node.type)
}

function hitNode(x, y) {
  let best = null
  for (const node of state.graph.nodes) {
    const distance = Math.hypot(node.x - x, node.y - y)
    if (distance <= node.size + 10 && (!best || distance < best.distance)) {
      best = { ...node, distance }
    }
  }
  return best
}

function selectNode(id) {
  state.selectedId = id
  state.pulse = 1
  renderInspector()
}

function renderInspector() {
  const node = state.graph.byId?.get(state.selectedId)
  if (!node) {
    els.selectedType.textContent = 'Nothing selected'
    els.selectedLabel.textContent = 'Choose a node'
    els.selectedFields.innerHTML = ''
    els.selectedLinks.innerHTML = ''
    return
  }
  els.selectedType.textContent = node.type
  els.selectedLabel.textContent = node.label
  const meta = flattenMeta(node.meta || {})
  els.selectedFields.innerHTML = Object.entries(meta).slice(0, 18).map(([key, value]) => (
    `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(formatValue(value))}</dd>`
  )).join('')
  const links = state.graph.edges.filter((edge) => edge.from === node.id || edge.to === node.id)
  els.selectedLinks.innerHTML = links.slice(0, 12).map((edge) => {
    const otherId = edge.from === node.id ? edge.to : edge.from
    const other = state.graph.byId.get(otherId)
    return `<li>${escapeHtml(edge.type)} - ${escapeHtml(other?.label || otherId)}</li>`
  }).join('') || '<li>No direct links</li>'
}

function renderStats() {
  const stats = state.graph.stats || {}
  const records = Number(stats.chunks || 0) + Number(stats.objects || 0) + Number(stats.jobs || 0)
  els.recordGauge.textContent = String(records)
  els.edgeGauge.textContent = String(state.graph.edges.length || 0)
  els.typeGauge.textContent = String((state.graph.nodes || []).filter((node) => node.type === 'type').length)
}

async function runQuery() {
  els.queryStatus.textContent = 'Running'
  try {
    const result = await api('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ db: state.db, sql: els.sqlInput.value }),
    })
    els.queryStatus.textContent = `${result.rows.length} rows in ${result.elapsedMs} ms`
    els.queryOutput.textContent = JSON.stringify(result.rows, null, 2)
    await refreshTelemetry()
  } catch (error) {
    els.queryStatus.textContent = 'Error'
    els.queryOutput.textContent = error.message
  }
}

async function api(path, options) {
  const response = await fetch(path, options)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || body.error || response.statusText)
  return body
}

function resizeCanvas() {
  const rect = els.graphCanvas.getBoundingClientRect()
  const scale = window.devicePixelRatio || 1
  els.graphCanvas.width = Math.max(1, Math.floor(rect.width * scale))
  els.graphCanvas.height = Math.max(1, Math.floor(rect.height * scale))
  ctx.setTransform(scale, 0, 0, scale, 0, 0)
  seedPositions()
}

function selectedInEdge(edge) {
  return edge.from === state.selectedId || edge.to === state.selectedId
}

function flattenMeta(meta) {
  const flat = {}
  for (const [key, value] of Object.entries(meta)) {
    if (key === 'embedding' || key === 'data') {
      flat[key] = Array.isArray(value) ? `[${value.length} values]` : '[binary payload]'
    } else {
      flat[key] = value
    }
  }
  return flat
}

function formatValue(value) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function shortSql(sql) {
  return String(sql || '').replace(/\s+/g, ' ').trim().slice(0, 58)
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]))
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}
