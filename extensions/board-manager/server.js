/**
 * AgentArmy Board Manager — GitHub Copilot Extension
 *
 * Invoke with @board-manager in GitHub Copilot Chat (VS Code or github.com).
 *
 * Deploy to Vercel, Railway, or any Node.js host.
 * Register as a GitHub App at github.com/settings/apps.
 */

import express from 'express'
import { Octokit } from '@octokit/rest'
import {
  createAckEvent,
  createTextEvent,
  createDoneEvent,
  verifyAndParseRequest,
} from '@copilot-extensions/preview-sdk'

const PORT    = process.env.PORT           || 3000
const OWNER   = process.env.GITHUB_OWNER
const REPO    = process.env.GITHUB_REPO
const PROJECT = parseInt(process.env.PROJECT_NUMBER || '1')

const app = express()

app.get('/', (_req, res) => res.send('AgentArmy Board Manager — online'))

app.post('/agent', express.raw({ type: '*/*' }), async (req, res) => {
  const signature = req.headers['github-public-key-signature']
  const keyId     = req.headers['github-public-key-identifier']
  const token     = req.headers['x-github-token']

  let payload
  try {
    payload = await verifyAndParseRequest(req.body, signature, keyId, { token })
  } catch {
    return res.status(401).send('Unauthorized')
  }

  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.flushHeaders()
  res.write(createAckEvent())

  const octokit = new Octokit({ auth: token })
  const msg     = (payload.messages.filter(m => m.role === 'user').at(-1)?.content ?? '').toLowerCase()

  try {
    res.write(createTextEvent(await route(msg, octokit)))
  } catch (err) {
    res.write(createTextEvent(`❌ ${err.message}`))
  }

  res.write(createDoneEvent())
  res.end()
})

// ─── Router ──────────────────────────────────────────────────────────────────

async function route(msg, octokit) {
  if (has(msg, ['help', 'what can', 'how do']))              return help()
  if (has(msg, ['blocked', 'impediment', 'blocker']))        return blockedItems(octokit)
  if (has(msg, ['sprint', 'iteration', 'this week']))        return sprintStatus(octokit)
  if (has(msg, ['pi-', 'pi progress', 'program increment'])) return piProgress(msg, octokit)
  if (has(msg, ['p0', 'critical', 'urgent', 'priority']))    return priorityItems(octokit)
  if (has(msg, ['create', 'new issue', 'new story', 'add'])) return createGuide(msg)
  return boardStatus(octokit)  // default: overview
}

const has = (msg, keywords) => keywords.some(k => msg.includes(k))

// ─── Handlers ────────────────────────────────────────────────────────────────

async function boardStatus(octokit) {
  const items = await projectItems(octokit)
  const total = items.length
  const c = count(items, 'status')
  const pct = total > 0 ? Math.round(((c.Done || 0) / total) * 100) : 0

  return mdTable('📋 Board Overview', [
    ['Status', 'Count'],
    ['🔵 Todo', c.Todo || 0],
    ['🟡 In Progress', c['In progress'] || 0],
    ['🟢 Done', c.Done || 0],
    ['**Total**', `**${total}**`],
  ]) + `\n\n**${pct}% complete**`
}

async function sprintStatus(octokit) {
  const items  = await projectItems(octokit)
  const active = items.filter(i => i.iteration && i.status !== 'Done')
  if (!active.length) return '📭 No in-progress items in the current iteration.'

  const lines = [`**🏃 Current Sprint — ${active[0].iteration}**`, '']
  for (const i of active) {
    const tag = i.status === 'In progress' ? '🟡' : '🔵'
    lines.push(`${tag} #${i.number}: ${i.title} _(${i.size || '?'}, ${i.type || '?'})_`)
  }
  return lines.join('\n')
}

async function blockedItems(octokit) {
  const { data } = await octokit.rest.issues.listForRepo({
    owner: OWNER, repo: REPO, labels: 'blocked-by', state: 'open',
  })
  if (!data.length) return '✅ No blocked items found.'
  return ['**🚧 Blocked Items**', '', ...data.map(i => `- #${i.number}: ${i.title}`)].join('\n')
}

async function priorityItems(octokit) {
  const items = await projectItems(octokit)
  const p0    = items.filter(i => i.priority === 'P0' && i.status !== 'Done')
  if (!p0.length) return '✅ No open P0 items.'
  return ['**🔴 P0 Items**', '', ...p0.map(i => `- #${i.number}: ${i.title} [${i.status}]`)].join('\n')
}

async function piProgress(msg, octokit) {
  const m      = msg.match(/pi-?\s*(\d+)/i)
  const piName = m ? `PI-${m[1]}` : null
  const items  = await projectItems(octokit)
  const subset = piName ? items.filter(i => i.pi === piName) : items

  if (!subset.length) return piName ? `No items found for ${piName}.` : 'No PI items found.'

  const c     = count(subset, 'status')
  const total = subset.length
  const pct   = total > 0 ? Math.round(((c.Done || 0) / total) * 100) : 0

  return mdTable(`🗓 ${piName || 'PI'} Progress`, [
    ['Status', 'Count'],
    ['Todo', c.Todo || 0],
    ['In Progress', c['In progress'] || 0],
    ['Done', c.Done || 0],
  ]) + `\n\n**${pct}% of ${total} items complete**`
}

function createGuide(msg) {
  const type = has(msg, ['bug'])     ? 'Bug'
             : has(msg, ['feature']) ? 'Feature'
             : has(msg, ['enabler']) ? 'Enabler'
             : 'Story'

  return [
    `**➕ Create a ${type}**`,
    '',
    '```bash',
    `gh issue create \\`,
    `  --title "Your title here" \\`,
    `  --label "${type}" \\`,
    `  --body "## Acceptance Criteria\\n- [ ] ..." \\`,
    `  --repo ${OWNER}/${REPO}`,
    '```',
    '',
    `Then set the **PI**, **Size**, and **Estimate** fields on the project board.`,
    '',
    `Add \`copilot-task\` label for small/bounded work, \`agent-army-task\` for complex work.`,
  ].join('\n')
}

function help() {
  return [
    '**🪖 AgentArmy Board Manager**',
    '',
    'Ask me anything about your project board:',
    '',
    '| Query | Example |',
    '|-------|---------|',
    '| Board overview | _"status"_ or _"board overview"_ |',
    '| Current sprint | _"what\'s in the sprint"_ |',
    '| Blocked items | _"what\'s blocked"_ |',
    '| PI progress | _"PI-1 progress"_ |',
    '| P0 items | _"show P0 items"_ |',
    '| Create an issue | _"create a story for login"_ |',
  ].join('\n')
}

// ─── GitHub Projects query ────────────────────────────────────────────────────

async function projectItems(octokit) {
  const query = `
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) {
          items(first: 100) {
            nodes {
              content {
                ... on Issue { title number state }
              }
              fieldValues(first: 15) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name field { ... on ProjectV2SingleSelectField { name } }
                  }
                  ... on ProjectV2ItemFieldTextValue {
                    text field { ... on ProjectV2Field { name } }
                  }
                  ... on ProjectV2ItemFieldIterationValue {
                    title field { ... on ProjectV2IterationField { name } }
                  }
                  ... on ProjectV2ItemFieldNumberValue {
                    number field { ... on ProjectV2Field { name } }
                  }
                }
              }
            }
          }
        }
      }
    }
  `
  const result = await octokit.graphql(query, { owner: OWNER, number: PROJECT })
  return result.user.projectV2.items.nodes
    .map(node => {
      const fields = {}
      for (const f of node.fieldValues.nodes) {
        const key = f.field?.name
        if (key) fields[key] = f.name ?? f.text ?? f.title ?? f.number
      }
      return {
        title:    node.content?.title,
        number:   node.content?.number,
        state:    node.content?.state,
        status:   fields['Status'],
        type:     fields['Type'],
        pi:       fields['PI'],
        iteration: fields['Iteration'],
        priority: fields['Priority'],
        size:     fields['Size'],
        estimate: fields['Estimate'],
      }
    })
    .filter(i => i.title)
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function count(items, key) {
  return items.reduce((acc, item) => {
    const val = item[key] || 'Unknown'
    acc[val] = (acc[val] || 0) + 1
    return acc
  }, {})
}

function mdTable(title, rows) {
  const [header, ...body] = rows
  const sep = header.map(() => '---')
  const fmt = r => `| ${r.join(' | ')} |`
  return [title, '', fmt(header), fmt(sep), ...body.map(fmt)].join('\n')
}

app.listen(PORT, () => console.log(`Board Manager listening on :${PORT}`))
