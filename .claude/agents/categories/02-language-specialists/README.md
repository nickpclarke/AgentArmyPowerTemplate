# Language Specialists — Organized by Tier

**MECE taxonomy for routing: languages vs. frameworks vs. platforms**

Language Specialists are organized into three tiers to guide you to the right agent quickly:

1. **`languages/`** — Pure language expertise (idioms, type system, performance, ecosystem)
2. **`frameworks/`** — Framework-specific work (web/mobile app development)
3. **`platforms/`** — Version-pinned or OS-bound specialists (.NET versions, Windows automation)

## 📖 Routing Guide (Start Here)

**See `TAXONOMY.md` for complete decision rules, tie-breakers, and edge cases.**

**TL;DR:**
- **Language agent** when: You need language idioms, type system, concurrency, performance optimization
- **Framework agent** when: You're building an app and need framework conventions (Django, React, Rails, etc.)
- **Platform agent** when: You're locked into a .NET version or Windows/cloud automation

**Example:**
- "Build a REST API in Python" → `python-pro` (design), then `fastapi-developer` (implement with framework)
- "Optimize React component render perf" → `react-specialist`
- "Migrate from .NET Framework to Core" → `dotnet-framework-4.8-expert` → `dotnet-core-expert`

---

## 🗂️ Languages Tier (13 agents)

Pure language expertise: idioms, type system, ecosystem, performance, runtime semantics.

| Agent | Path | Scope |
|-------|------|-------|
| `cpp-pro` | `languages/cpp-pro.md` | Modern C++20/23, systems, performance, memory |
| `csharp-developer` | `languages/csharp-developer.md` | C# language features, async patterns, version-agnostic |
| `elixir-expert` | `languages/elixir-expert.md` | Elixir, OTP, concurrency, BEAM VM |
| `golang-pro` | `languages/golang-pro.md` | Go idioms, goroutines, interfaces, performance |
| `java-architect` | `languages/java-architect.md` | Java enterprise, microservices, JVM tuning |
| `javascript-pro` | `languages/javascript-pro.md` | Modern JS/ES2023+, async, browser/Node APIs |
| `kotlin-specialist` | `languages/kotlin-specialist.md` | Kotlin idioms, coroutines, multiplatform |
| `php-pro` | `languages/php-pro.md` | PHP 8.3+, strict typing, modern patterns |
| `python-pro` | `languages/python-pro.md` | Python idioms, typing, async, performance |
| `rust-engineer` | `languages/rust-engineer.md` | Rust ownership, lifetimes, systems programming |
| `sql-pro` | `languages/sql-pro.md` | SQL query optimization, schema design |
| `swift-expert` | `languages/swift-expert.md` | Swift concurrency, protocols, server-side + iOS |
| `typescript-pro` | `languages/typescript-pro.md` | Advanced types, generics, type-level programming |

---

## 🚀 Frameworks Tier (13 agents)

Framework-specific development: conventions, libraries, middleware, deployment patterns.

### Web Frameworks (`frameworks/web/` — 11 agents)

| Agent | Path | Scope |
|-------|------|-------|
| `angular-architect` | `frameworks/web/angular-architect.md` | Angular 15+, RxJS, enterprise patterns |
| `django-developer` | `frameworks/web/django-developer.md` | Django 4+, ORM, REST APIs, async views |
| `fastapi-developer` | `frameworks/web/fastapi-developer.md` | FastAPI, Pydantic, async Python APIs |
| `laravel-specialist` | `frameworks/web/laravel-specialist.md` | Laravel 10+, Eloquent, queues |
| `nextjs-developer` | `frameworks/web/nextjs-developer.md` | Next.js 14+, App Router, full-stack |
| `node-specialist` | `frameworks/web/node-specialist.md` | Node.js runtime, streams, microservices |
| `react-specialist` | `frameworks/web/react-specialist.md` | React optimization, hooks, state management |
| `rails-expert` | `frameworks/web/rails-expert.md` | Rails, ActiveRecord, Hotwire, conventions |
| `spring-boot-engineer` | `frameworks/web/spring-boot-engineer.md` | Spring Boot 3+, microservices, cloud-native |
| `symfony-specialist` | `frameworks/web/symfony-specialist.md` | Symfony 6+/7+/8+, DI, Doctrine ORM |
| `vue-expert` | `frameworks/web/vue-expert.md` | Vue 3, Composition API, Nuxt |

### Mobile Frameworks (`frameworks/mobile/` — 2 agents)

| Agent | Path | Scope |
|-------|------|-------|
| `expo-react-native-expert` | `frameworks/mobile/expo-react-native-expert.md` | React Native + Expo, cross-platform mobile |
| `flutter-expert` | `frameworks/mobile/flutter-expert.md` | Flutter 3+, iOS/Android/Web |

---

## 🔧 Platforms Tier (5 agents)

Version-pinned or OS-bound specialists: backward compatibility, legacy support, platform-specific automation.

### .NET Versions (`platforms/dotnet/` — 2 agents)

| Agent | Path | Scope |
|-------|------|-------|
| `dotnet-core-expert` | `platforms/dotnet/dotnet-core-expert.md` | .NET Core 5–8, cloud-native, cross-platform |
| `dotnet-framework-4.8-expert` | `platforms/dotnet/dotnet-framework-4.8-expert.md` | .NET Framework 4.8, legacy, Windows enterprise |

### Windows Automation (`platforms/windows-automation/` — 3 agents)

| Agent | Path | Scope |
|-------|------|-------|
| `powershell-5.1-expert` | `platforms/windows-automation/powershell-5.1-expert.md` | Windows Server, AD, GPO, DHCP, DNS |
| `powershell-7-expert` | `platforms/windows-automation/powershell-7-expert.md` | Cross-platform, Azure, cloud orchestration |

*(Also see `powershell-module-architect`, `powershell-ui-architect` in category 06; `powershell-security-hardening` in category 04)*

---

## 🎯 Quick Decision Flow

```
┌─ "I'm optimizing for language X" (types, idioms, perf)
│  → Use languages/ agent
│
├─ "I'm building an app with framework Y"
│  → Use frameworks/ agent
│
└─ "I'm locked into .NET version X or Windows"
   → Use platforms/ agent
```

For complex tasks that span tiers:
1. Start with your primary tier (language / framework / platform)
2. Escalate to another tier if needed (e.g., framework → language if you hit a language-level wall)
3. Pull in domain specialists (DevOps, Database, etc.) from other categories if needed

---

## 📋 MECE Distinctiveness

This taxonomy is **Mutually Exclusive** (no task routes to two agents) and **Collectively Exhaustive** (all tasks have a home).

- **Languages** tier: language-specific work
- **Frameworks** tier: app-building within a framework
- **Platforms** tier: version-pinned or OS-bound work

**No overlap** — each agent owns distinct decision space.

See `TAXONOMY.md` for:
- Explicit tie-breakers (15+ concrete examples)
- Edge case handling (JS/TS split, .NET versions, PowerShell, mobile languages)
- Full routing rules and escalation patterns
- Maintenance rules for adding new agents

---

## 🚀 Using These Agents

Invoke by agent `name:` (path-independent):

```
Agent(subagent_type: "python-pro")
Agent(subagent_type: "react-specialist")
Agent(subagent_type: "dotnet-core-expert")
```

Or route in documentation/discussion:
- "Ask `python-pro`" (language idioms)
- "Ask `fastapi-developer`" (async API patterns)
- "Ask `typescript-pro`" (advanced types)

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.1.0 | 2026-05-22 | Reorganized into tiers (languages/frameworks/platforms); created TAXONOMY.md source-of-truth |
| 1.0.4 | 2026-05-21 | Original flat structure |

---

**Last updated**: 2026-05-22  
**Maintained by**: Agent Army core  
**Questions?** See `TAXONOMY.md` for full routing rules, tie-breakers, and edge cases.
