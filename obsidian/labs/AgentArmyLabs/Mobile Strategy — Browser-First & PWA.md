---
tags: [platform, layer, ui, mobile, pwa]
track: platform
layer: UI
status: draft
---
# Mobile Strategy — Browser-First & PWA

> [!abstract] Scope
> How AgentArmy reaches phones. The decision: **mobile-browser-first** (responsive + PWA), reusing every existing contract. A **native** app (Expo/Flutter) is deferred until a concrete device-API/store need appears.

**🎛 [[Obsidian Board]] · 🧭 [[Platform Atlas]] · 🖥 [[Layer — UI]] · 🔌 [[API Strategy — Internal, External, Open & Monetized]]**

> [!tip] Decision
> 1. **Mobile browser = the existing Next.js app, made responsive + installable (PWA).** No new layer, no new spoke, **no new contract**.
> 2. **Native is a separate, later bet.** Only a native app with deep device APIs justifies a dedicated `mobile-bff` contract — a PWA never does.

## Mobile browser ≠ mobile app

A phone hitting the site uses the **same** surfaces the desktop browser does:

- `frontend-bff.openapi.json` (browser ↔ Next.js BFF, ADR-002 cookie-in → JWT-out)
- `backend-core.openapi.json` (the Data API)
- `agui-stream.asyncapi.yaml` (AG-UI agent SSE stream)

The contract surface is **transport-agnostic** — browser, mobile browser, and a future native client can all bind to the same BFF. So "mobile browser" is a **frontend concern** (layout, touch, viewport, offline), not a contract gap. The bench already has `mobile-web-specialist` (responsive/touch/PWA) and `expo-react-native-expert` / `flutter-expert` (native) — none used yet.

## Readiness audit — frontend-core (2026-05-25)

> [!warning] Critical gap: no viewport
> `app/layout.tsx` exports `metadata` but **no `viewport`** → no `<meta name="viewport">`. Mobile browsers render at desktop width, zoomed out. This is the single highest-impact fix.

Current state (Next 16 App Router + React 19, CopilotKit; **hand-rolled CSS** in `app/globals.css`, no Tailwind; mid **Svelte→Next strangler migration**, plus a nested `agentarmy-console/`):

| Area | State |
|---|---|
| Viewport meta | ❌ missing (`export const viewport`) |
| PWA manifest | ❌ none (`app/manifest.ts` / `public/manifest.json`) |
| Service worker | ❌ none (no offline, not installable; no `next-pwa`/Serwist) |
| Responsive CSS | ⚠️ hand-rolled in `globals.css` — breakpoints/touch targets unaudited |
| Safe-area / notch | ⚠️ needs `viewport-fit=cover` + `env(safe-area-inset-*)` |
| Dark mode | ✅ no-flash theme, respects `prefers-color-scheme` |
| Test harness | ✅ Lighthouse CI (`lhci`), `size-limit`, Playwright + axe already wired |
| Dual-stack | ⚠️ Svelte (Vite :5173) + Next (:3000) + console — target the **Next** strangler surface |

## PWA enablement punch-list (ordered)

> [!todo] Frontend-only — no backend/contract work
> 1. **Viewport** — add `export const viewport: Viewport = { width: "device-width", initialScale: 1, viewportFit: "cover" }` to `app/layout.tsx`.
> 2. **Manifest** — `app/manifest.ts` (name, short_name, `display: "standalone"`, `start_url`, `theme_color`/`background_color` matching the dark/light tokens) + maskable icons (192/512).
> 3. **Service worker** — Serwist (Next 16-friendly) or a hand-rolled SW: precache the app shell, runtime-cache static assets, network-first for `/api/*` (never cache authed data carelessly).
> 4. **Offline shell** — a minimal offline fallback route.
> 5. **Install affordance** — handle `beforeinstallprompt` (Android); document iOS "Add to Home Screen" caveats.
> 6. **Gate it** — add the Lighthouse **PWA + mobile** categories to the existing `lhci` run; add a mobile-viewport Playwright project.

## Responsive punch-list

- Audit `globals.css` for mobile breakpoints; ensure fluid/`clamp()` sizing over fixed widths.
- Touch targets ≥ 44px; verify the CopilotKit sidebar collapses sensibly on narrow screens.
- `env(safe-area-inset-*)` padding for notch/home-indicator.
- Test the real pain point: **iOS Safari** (100vh, safe-areas, no install prompt).

## When to go native (and only then, a contract)

Trigger = camera/biometrics/background tasks/push at scale/app-store presence. Then:

- New **mobile spoke** (`expo-react-native-expert` or `flutter-expert`).
- It can **reuse `frontend-bff.openapi.json`**, or — if its needs diverge — author a dedicated **`mobile-bff.openapi.json`** (+ an AsyncAPI for push/realtime), register it in [[Layer — API]] / `docs/contracts.md`, and **mock it in Postman** so the mobile spoke builds before any backend work (mock-first).

Until that trigger fires, **PWA is the 80/20**: one codebase, instant updates, no store review.

Related: [[Layer — UI]], [[API Strategy — Internal, External, Open & Monetized]], [[Platform Atlas]].
