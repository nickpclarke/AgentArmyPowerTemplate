#!/usr/bin/env python3
"""Handle board slash commands (/board-status, /sprint, /blocked, /p0, /pi, /board-help).

Invoked by .github/workflows/board-commands.yml. Reads the triggering comment and
project coordinates from environment variables, queries the GitHub Projects v2
board, and posts a markdown reply on the issue/PR.
"""

import os
import json
import subprocess
import re
import sys

OWNER          = os.environ['OWNER']
PROJECT_NUMBER = int(os.environ['PROJECT_NUMBER'])
FULL_REPO      = os.environ['FULL_REPO']
ISSUE_NUM      = os.environ['ISSUE_NUM']
CMD            = os.environ['CMD'].strip()


# ── GitHub helpers ────────────────────────────────────────

def graphql(query, **vars):
    args = ['gh', 'api', 'graphql', '-f', f'query={query}']
    for k, v in vars.items():
        args += ['-F' if isinstance(v, int) else '-f', f'{k}={v}']
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"GraphQL query failed (exit {r.returncode}): {r.stderr.strip()}",
              file=sys.stderr)
        return {}
    return json.loads(r.stdout).get('data', {})


def post(body):
    r = subprocess.run(
        ['gh', 'issue', 'comment', ISSUE_NUM, '--repo', FULL_REPO, '--body', body],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Failed to post comment: {r.stderr.strip()}")


def get_items():
    q = '''query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) {
          items(first: 500) {
            nodes {
              content { ... on Issue { title number } }
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
                }
              }
            }
          }
        }
      }
      organization(login: $owner) {
        projectV2(number: $number) {
          items(first: 500) {
            nodes {
              content { ... on Issue { title number } }
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
                }
              }
            }
          }
        }
      }
    }'''
    data = graphql(q, owner=OWNER, number=PROJECT_NUMBER)
    user_project = data.get('user', {}).get('projectV2')
    org_project = data.get('organization', {}).get('projectV2')
    project = user_project if user_project is not None else org_project if org_project is not None else {}
    nodes = project.get('items', {}).get('nodes', [])
    items = []
    for node in nodes:
        if not node.get('content'):
            continue
        f = {}
        for fv in node['fieldValues']['nodes']:
            key = (fv.get('field') or {}).get('name')
            if key:
                f[key] = fv.get('name') or fv.get('text') or fv.get('title')
        items.append({
            'title':     node['content'].get('title'),
            'number':    node['content'].get('number'),
            'status':    f.get('Status'),
            'type':      f.get('Type'),
            'pi':        f.get('PI'),
            'iteration': f.get('Iteration'),
            'priority':  f.get('Priority'),
            'size':      f.get('Size'),
        })
    return items


def md_table(title, headers, rows):
    sep = ['---'] * len(headers)
    lines = [title, '',
             '| ' + ' | '.join(headers) + ' |',
             '| ' + ' | '.join(sep) + ' |']
    for row in rows:
        lines.append('| ' + ' | '.join(str(c) for c in row) + ' |')
    return '\n'.join(lines)


# ── Command handlers ──────────────────────────────────────

def cmd_status():
    items = get_items()
    counts = {}
    for i in items:
        s = i['status'] or 'Unknown'
        counts[s] = counts.get(s, 0) + 1
    total = len(items)
    done  = counts.get('Done', 0)
    pct   = round(done * 100 / total) if total else 0
    rows  = [
        ['🔵 Todo',              counts.get('Todo', 0)],
        ['⚪ Ready',             counts.get('Ready', 0)],
        ['🟡 In Progress',       counts.get('In Progress', 0)],
        ['🟠 In Review',         counts.get('In Review', 0)],
        ['🟢 Done',              done],
        ['🟣 Awaiting Decision', counts.get('Awaiting Decision', 0)],
        ['**Total**',            f'**{total}**'],
    ]
    return md_table('## 📋 Board Status', ['Status', 'Count'], rows) \
           + f'\n\n**{pct}% complete**'


def cmd_sprint():
    items  = get_items()
    active = [i for i in items if i['iteration'] and i['status'] != 'Done']
    if not active:
        return '📭 No in-progress items in the current iteration.'
    sprint = active[0]['iteration']
    lines  = [f'## 🏃 Sprint: {sprint}', '']
    for i in active:
        icon = {
            'Ready': '⚪',
            'In Progress': '🟡',
            'In Review': '🟠',
            'Awaiting Decision': '🟣',
        }.get(i['status'], '🔵')
        lines.append(f"{icon} #{i['number']}: {i['title']} _({i.get('size','?')})_")
    return '\n'.join(lines)


def cmd_blocked():
    r = subprocess.run(
        ['gh', 'issue', 'list', '--repo', FULL_REPO,
         '--label', 'blocked-by', '--state', 'open', '--json', 'number,title'],
        capture_output=True, text=True)
    issues = json.loads(r.stdout) if r.returncode == 0 else []
    if not issues:
        return '✅ No blocked items found.'
    return '\n'.join(['## 🚧 Blocked Items', ''] +
                     [f"- #{i['number']}: {i['title']}" for i in issues])


def cmd_p0():
    items = get_items()
    p0    = [i for i in items if i['priority'] == 'P0' and i['status'] != 'Done']
    if not p0:
        return '✅ No open P0 items.'
    return '\n'.join(['## 🔴 Open P0 Items', ''] +
                     [f"- [{i['status']}] #{i['number']}: {i['title']}" for i in p0])


def cmd_pi(pi_name):
    items  = get_items()
    subset = [i for i in items if i['pi'] == pi_name] if pi_name else items
    if not subset:
        return f'No items found for {pi_name}.' if pi_name else 'No PI items found.'
    counts = {}
    for i in subset:
        s = i['status'] or 'Unknown'
        counts[s] = counts.get(s, 0) + 1
    total = len(subset)
    done  = counts.get('Done', 0)
    pct   = round(done * 100 / total) if total else 0
    rows  = [
        ['Todo',              counts.get('Todo', 0)],
        ['Ready',             counts.get('Ready', 0)],
        ['In Progress',       counts.get('In Progress', 0)],
        ['In Review',         counts.get('In Review', 0)],
        ['Done',              done],
        ['Awaiting Decision', counts.get('Awaiting Decision', 0)],
    ]
    return md_table(f'## 🗓 {pi_name or "PI"} Progress', ['Status', 'Count'], rows) \
           + f'\n\n**{pct}% of {total} items complete**'


def cmd_decisions():
    from datetime import datetime, timezone

    r = subprocess.run(
        [
            'gh', 'issue', 'list', '--repo', FULL_REPO,
            '--label', 'hitl-decision', '--state', 'open',
            '--json', 'number,title,assignees,labels,createdAt',
        ],
        capture_output=True,
        text=True,
    )
    issues = json.loads(r.stdout) if r.returncode == 0 else []
    if not issues:
        return '✅ No open decision artifacts.'

    now = datetime.now(timezone.utc)
    groups = {}
    for issue in issues:
        atype = 'human'
        for label in issue.get('labels', []):
            if label['name'].startswith('assignee:'):
                atype = label['name'].replace('assignee:', '')
                break
        groups.setdefault(atype, []).append(issue)

    lines = ['## 🧭 Open Decision Artifacts', '']
    for atype, items in sorted(groups.items()):
        lines.append(f'### Assignee: `{atype}`')
        lines.append('')
        for i in items:
            created = datetime.fromisoformat(i['createdAt'].replace('Z', '+00:00'))
            age = (now - created).days
            names = ', '.join(f"@{a['login']}" for a in i.get('assignees', [])) or '_(unassigned)_'
            lines.append(f"- #{i['number']}: **{i['title']}** — {names} — open **{age}d**")
        lines.append('')
    return '\n'.join(lines).strip()


def cmd_help():
    return '\n'.join([
        '## 🪖 Board Commands',
        '',
        '| Command | Description |',
        '|---------|-------------|',
        '| `/board-status` | Board overview — status breakdown + % complete |',
        '| `/sprint` | Items in the current iteration |',
        '| `/blocked` | Issues with `blocked-by` label |',
        '| `/decisions` | Open HITL Decision Artifacts grouped by assignee type |',
        '| `/p0` | Open P0 priority items |',
        '| `/pi PI-1` | Progress for a specific Program Increment |',
        '| `/board-help` | This help message |',
    ])


# ── Router ────────────────────────────────────────────────

def main():
    cmd = CMD.lower()

    if   '/board-status' in cmd: out = cmd_status()
    elif '/sprint'       in cmd: out = cmd_sprint()
    elif '/blocked'      in cmd: out = cmd_blocked()
    elif '/decisions'    in cmd: out = cmd_decisions()
    elif '/p0'           in cmd: out = cmd_p0()
    elif '/pi '          in cmd:
        m       = re.search(r'/pi\s+(pi-?\s*\d+)', cmd, re.IGNORECASE)
        pi_name = None
        if m:
            raw     = re.sub(r'\s+', '', m.group(1)).upper()
            pi_name = raw if raw.startswith('PI-') else 'PI-' + raw.lstrip('PI')
        out = cmd_pi(pi_name)
    else:
        out = cmd_help()

    post(out)


if __name__ == '__main__':
    main()
