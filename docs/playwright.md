# Playwright Browser Testing

Playwright is a browser automation and end-to-end testing tool from Microsoft. In this repo, use it when a change needs proof that a human-facing page actually works in a browser, not just that an API returned JSON.

The short version:

| Tooling | Use it for |
|---|---|
| Playwright Test | Repeatable browser tests committed to the repo and run locally or in CI. |
| Playwright UI mode | Interactive debugging of tests while developing a page or workflow. |
| Playwright Codegen | Recording a first draft of a test from manual browser actions. |
| Playwright MCP | Letting an AI agent drive a browser through MCP tools and accessibility snapshots. |

Official docs:

- Playwright: <https://playwright.dev/>
- Playwright Test intro: <https://playwright.dev/docs/intro>
- Playwright MCP: <https://playwright.dev/docs/getting-started-mcp>
- Playwright MCP capabilities: <https://playwright.dev/mcp/capabilities>

## Why We Added It

The middle-core runtime prototype has a human demo at `/model/demo`. A curl check can prove the endpoint returns JSON, but it cannot prove the page is understandable or that the buttons work. Playwright fills that gap by opening the actual page, reading visible UI, clicking controls, and asserting the rendered result.

Current middle-core browser test:

```text
tests/e2e/middle-core-scenario-lab.spec.js
```

It verifies:

- the scenario lab page renders;
- generated model counts appear;
- state-machine count is visible;
- success path renders 6 graph nodes and 5 graph edges;
- evidence status becomes `complete`;
- clicking the disabled-handler path moves the UI to failed/no-evidence state;
- clicking back to success restores the completed evidence view.

## Local Commands

Install dependencies:

```powershell
npm install
```

Install browser binaries if they are not already present:

```powershell
npx playwright install
```

Run all Playwright tests:

```powershell
npx playwright test
```

Run only the middle-core scenario lab test:

```powershell
$env:MIDDLE_CORE_BASE_URL="http://127.0.0.1:18001"
npx playwright test tests/e2e/middle-core-scenario-lab.spec.js --project=chromium
```

Open the Playwright interactive UI:

```powershell
npx playwright test --ui
```

Generate a starter test from manual browser actions:

```powershell
npx playwright codegen http://127.0.0.1:18001/model/demo
```

## Middle-Core Pipeline

The middle-core localhost pipeline now runs both API-level smoke checks and the Playwright browser test:

```powershell
.\scripts\middle-core\Test-MiddleCoreLocalPipeline.ps1
```

Use a different port when another middle-core instance is already running:

```powershell
.\scripts\middle-core\Test-MiddleCoreLocalPipeline.ps1 -Port 18098
```

The script starts middle-core, verifies `/health`, `/model`, `/model/demo`, the success scenario, the failure scenario, and then runs the Playwright scenario-lab spec against the live page.

## Playwright MCP

Playwright MCP is different from committed Playwright tests. It exposes browser automation as MCP tools so an AI assistant can navigate, click, inspect pages, take screenshots, and debug browser state through a standard MCP interface.

The official MCP server can be configured with:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

Useful modes from the official docs:

| Mode | Why use it |
|---|---|
| Default headed mode | Watch the browser while an agent tests a page. |
| `--headless` | Run automation without a visible browser. |
| `--browser=firefox` or `--browser=webkit` | Check a non-Chromium browser. |
| `--isolated` | Start each session with a clean browser profile. |
| `--extension` | Connect through the Playwright extension to existing browser tabs and sessions. |
| `--caps=vision,pdf,devtools,network,storage,testing` | Enable additional MCP tool groups beyond the core browser controls. |

Security note: browser automation can interact with real pages and, depending on configuration, real sessions. Keep MCP browser tools scoped to trusted clients and local test targets unless the user explicitly approves broader use.

## Repo Rules

- Prefer committed Playwright specs for repeatable acceptance checks.
- Prefer Playwright MCP for exploratory agent-assisted browser work, triage, screenshots, and test generation.
- Keep generated Playwright reports out of git. `playwright-report/` and `test-results/` are ignored.
- Use `MIDDLE_CORE_BASE_URL` for tests that target middle-core so they can run against any local port.
- Do not rely only on screenshots for acceptance. Assert visible text, counts, status changes, and user actions.
