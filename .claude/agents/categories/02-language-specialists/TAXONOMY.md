# Language Specialists Taxonomy

**Source of truth for routing decisions in category 02**

Last updated: 2026-05-22 | Version: 1.1.0

---

## Three Tiers: How Agents Are Organized

### 1. **Languages/** — Pure Language Expertise
"I need help with this language's idioms, type system, ecosystem, or performance."

**Scope**: Language semantics, runtime behavior, concurrency patterns, memory, type safety, package management, conventions.

**Agents** (13):
cpp-pro, csharp-developer, elixir-expert, golang-pro, java-architect, javascript-pro, kotlin-specialist, php-pro, python-pro, rust-engineer, sql-pro, swift-expert, typescript-pro

**When to invoke**: 
- Type-level design (generics, lifetimes, traits, protocols)
- Language idioms (goroutines, async/await, comprehensions, pattern matching)
- Runtime semantics (GC, memory layout, concurrency model)
- Performance optimization at language level
- Advanced patterns (macros, metaprogramming, reflection)
- Package ecosystem decisions (npm, pip, cargo, gems, etc.)

### 2. **Frameworks/** — Framework/Platform-Specific Work
"I'm building an app ON this framework/runtime."

**Scope**: Framework conventions, libraries, middleware, routing, ORM, templating, deployment patterns, ecosystem tooling.

#### **2a. frameworks/web/** — Web Application Frameworks (11 agents)
angular-architect, django-developer, fastapi-developer, laravel-specialist, nextjs-developer, node-specialist, react-specialist, rails-expert, spring-boot-engineer, symfony-specialist, vue-expert

**When to invoke**: 
- Framework-idiomatic code (Django ORM, Rails conventions, FastAPI Pydantic, React hooks, Vue composition API)
- App architecture within the framework (routing, middleware, state management)
- Framework dependencies and library choices
- Deployment/DevOps for that framework
- Performance optimization within the framework

#### **2b. frameworks/mobile/** — Mobile Application Frameworks (2 agents)
expo-react-native-expert, flutter-expert

**When to invoke**:
- Mobile UI development (React Native, Flutter widgets)
- Mobile platform integration (push notifications, native modules, app store deployment)
- Mobile-specific concerns (offline, battery, storage)
- Cross-platform code sharing strategies

### 3. **Platforms/** — Version-Pinned / OS-Bound Specialists
"I'm locked into this version or OS; this isn't a general language choice."

**Scope**: Backward-compatible/legacy version support; Windows/cloud-specific automation; platform constraints.

#### **3a. platforms/dotnet/** — .NET Runtime Versions (2 agents)
dotnet-core-expert (cloud-native .NET 5–8), dotnet-framework-4.8-expert (legacy Windows .NET)

**When to invoke**:
- Upgrading or stuck on a specific .NET version
- Framework vs. Core trade-offs
- Legacy .NET Framework 4.8 maintenance or migration
- Cloud-native .NET Core patterns

#### **3b. platforms/windows-automation/** — Windows/Cloud Automation (2 agents)
powershell-5.1-expert (Windows Server, AD, GPO), powershell-7-expert (cross-platform, Azure, cloud)

**When to invoke**:
- Windows infrastructure automation (AD, DNS, DHCP, GPO)
- Azure cloud scripting and orchestration
- PowerShell remoting and DSC
- Legacy Windows Server environments

---

## The Decision Rule: Language vs Framework vs Platform

### **Start here: Which tier?**

```
Is the task ABOUT THE LANGUAGE ITSELF?
├─ YES → Go to Languages/ tier
│        Type systems, idioms, memory, concurrency, stdlib, patterns
│
└─ NO, it's about building an APP
   │
   ├─ Is it locked to a specific .NET version or Windows/cloud automation?
   │  ├─ YES → Platforms/ tier (dotnet/*, windows-automation/*)
   │  │
   │  └─ NO
   │     │
   │     ├─ Is it mobile (iOS/Android/React Native/Flutter)?
   │     │  ├─ YES → Frameworks/mobile/
   │     │  │
   │     │  └─ NO → Frameworks/web/
   │     │
   │     └─ Do you know the specific framework (Django, React, Next.js, Rails, etc.)?
   │        ├─ YES → Use that framework agent
   │        │
   │        └─ NO (e.g., "build a REST API in Python")
   │           └─ Use the language agent, then escalate to framework agent
   │              if you need framework-specific patterns
```

### **Tie-breakers: Concrete Examples**

| Task | Primary Agent | Use when | Escalate to (if needed) |
|------|---|---|---|
| "Optimize React component render perf" | `react-specialist` | You have working React code | `typescript-pro` for type-level optimization |
| "Design a generic type-safe API client" | `typescript-pro` | Language-level generics, decorators, advanced types | — |
| "Build a REST API in Python" | `python-pro` (initial design) → `fastapi-developer` (implement) | Choose language first; then pick framework | — |
| "Debug async/await issue in Node" | `javascript-pro` or `typescript-pro` | JavaScript runtime semantics | `node-specialist` if framework-specific (Express, Next.js) |
| "Implement a feature in Rails" | `rails-expert` | Rails conventions, ORM, routing | `ruby-*` (if existed; no pure Ruby agent yet) |
| "Optimize database queries in Spring Boot" | `spring-boot-engineer` | Within Spring/JPA context | `java-architect` for JVM-level tuning; `sql-pro` for query patterns |
| "Migrate from .NET Framework 4.8 to Core" | `dotnet-framework-4.8-expert` → `dotnet-core-expert` | Version-specific constraints | `csharp-developer` for language pattern updates |
| "Automate AD user provisioning" | `powershell-5.1-expert` (Windows) or `powershell-7-expert` (Azure) | OS/cloud-specific automation | `devops-engineer` for broader infrastructure |
| "Build a Vue 3 dashboard" | `vue-expert` | Vue idioms, composition API, Pinia | `typescript-pro` for type-safety at Vue boundaries |
| "Implement Kotlin multiplatform code" | `kotlin-specialist` | Kotlin language idioms, expect/actual | `flutter-expert` if Android UI is involved |
| "Custom SwiftUI components" | `swift-expert` (or future `swift-ios-expert`) | Swift concurrency, property wrappers, protocol extensions | (Mobile-specific wrappers optional; use `swift-expert` for now) |

### **Default Escalation Pattern**

```
Framework Agent (application work)
     ↓ (hits language-level wall)
Language Agent (deep patterns, performance, type system)
     ↓ (hits cross-language concern)
Domain Specialist (DevOps, Database, Security, etc., outside category 02)
```

Example: "Slow React queries" → `react-specialist` → `typescript-pro` → `database-optimizer` / `performance-engineer`

---

## Edge Cases & Resolutions

### JavaScript & TypeScript (Language vs. Framework Split)

**Decision**: Scoped by role, not by file path.

| Agent | Path | Scope |
|-------|------|-------|
| `javascript-pro` | `languages/javascript-pro.md` | Language core, ES2023+, runtime semantics, async patterns, browser/Node APIs |
| `typescript-pro` | `languages/typescript-pro.md` | Advanced type system, generics, type-level programming, end-to-end type safety |
| `nextjs-developer` | `frameworks/web/nextjs-developer.md` | Next.js app architecture, App Router, Server Components, deployment |
| `react-specialist` | `frameworks/web/react-specialist.md` | React component optimization, hooks, state management within React |
| `node-specialist` | `frameworks/web/node-specialist.md` | Node.js runtime, async I/O, package ecosystem, microservices patterns |
| `vue-expert` | `frameworks/web/vue-expert.md` | Vue 3, Composition API, Nuxt |
| `angular-architect` | `frameworks/web/angular-architect.md` | Angular RxJS, state management, enterprise patterns |

**Route**: "Advanced TypeScript types for a React app" → `typescript-pro` (types). "Build a Next.js app" → `nextjs-developer`. "Node.js microservice architecture" → `node-specialist`.

### .NET Framework 4.8 vs. Core (Version-Specific Split)

**Decision**: Version-pinned work goes to `platforms/dotnet/`, not `languages/`.

| Agent | Path | Scope |
|-------|------|-------|
| `csharp-developer` | `languages/csharp-developer.md` | C# language, modern patterns, version-agnostic idioms |
| `dotnet-framework-4.8-expert` | `platforms/dotnet/dotnet-framework-4.8-expert.md` | Legacy .NET Framework 4.8, Windows-only, backward compatibility |
| `dotnet-core-expert` | `platforms/dotnet/dotnet-core-expert.md` | .NET Core 5+, cloud-native, cross-platform deployment |

**Route**: "New C# 12 features" → `csharp-developer`. "Maintain WCF service" → `dotnet-framework-4.8-expert`. "Azure cloud deployment" → `dotnet-core-expert`.

### PowerShell (Windows Automation, Not a General Language)

**Decision**: PowerShell is inherently OS/cloud-bound. Scoped to `platforms/windows-automation/`, not `languages/`.

| Agent | Path | Scope |
|-------|------|-------|
| `powershell-5.1-expert` | `platforms/windows-automation/powershell-5.1-expert.md` | Windows Server, AD, DNS, DHCP, GPO, WinRM, DSC |
| `powershell-7-expert` | `platforms/windows-automation/powershell-7-expert.md` | Cross-platform, Azure SDK, cloud automation, CI/CD |

**Companion agents** (outside category 02):
- `powershell-module-architect` (category 06) — module design, cross-version compatibility
- `powershell-ui-architect` (category 06) — WPF/WinForms GUI design
- `powershell-security-hardening` (category 04) — constrained language mode, AMSI, security hardening

**Route**: "Automate AD user creation" → `powershell-5.1-expert`. "Deploy to Azure with IaC" → `powershell-7-expert`. "Design a reusable module" → `powershell-module-architect`. "Build a secure automation framework" → `powershell-security-hardening`.

### Mobile Languages (Swift, Kotlin) with Framework Aspects

**Decision**: Keep language agent; add optional framework pointers; avoid duplication.

| Agent | Path | Scope | Status |
|-------|------|-------|--------|
| `swift-expert` | `languages/swift-expert.md` | Swift language idioms, concurrency, protocols, memory safety; server-side + iOS/macOS | ✅ Current |
| `kotlin-specialist` | `languages/kotlin-specialist.md` | Kotlin idioms, coroutines, multiplatform, functional patterns; JVM + Android | ✅ Current |
| (optional) `swift-ios-expert` | `frameworks/mobile/swift-ios-expert.md` | iOS-specific (SwiftUI, UIKit, Combine); routes to `swift-expert` for language questions | 📋 Phase 2 |
| (optional) `kotlin-android-expert` | `frameworks/mobile/kotlin-android-expert.md` | Android-specific (Jetpack Compose, Coroutines for Android); routes to `kotlin-specialist` for language questions | 📋 Phase 2 |

**Current routing** (no optional wrappers): "Build an iOS app in Swift" → `swift-expert` + `mobile-developer` (from category 01). "Implement Kotlin multiplatform" → `kotlin-specialist`.

**Future routing** (if wrappers added in Phase 2): "SwiftUI component design" → `swift-ios-expert` → `swift-expert` (for language-level). "Android Jetpack Compose" → `kotlin-android-expert` → `kotlin-specialist`.

---

## Maintenance Rules (For Stability)

### Adding new agents to category 02

1. **New language?** One `.md` file in `languages/`, never a new folder.
   - Example: adding Gleam → `languages/gleam-expert.md`
   
2. **New web framework?** One `.md` file in existing `frameworks/web/`, never a new folder.
   - Example: adding Remix → `frameworks/web/remix-developer.md`
   
3. **New mobile framework?** One `.md` file in `frameworks/mobile/`.
   - Example: adding Jetpack Compose standalone → `frameworks/mobile/jetpack-specialist.md`
   
4. **Version-pinned or OS-bound?** Create under `platforms/<family>/`.
   - Example: adding Ruby on Windows → `platforms/windows-ruby/` (if justified by demand)

5. **Never rename `name:` frontmatter fields.** They are an API. Only add new agents.

6. **Tier hierarchy is read-only** — language vs. framework vs. platform is now fixed. Don't introduce new tiers.

---

## Agent Map (Full Reference Table)

| Agent | Tier | Path | Primary Deliverable | Use When | Don't Use For |
|-------|------|------|---|---|---|
| `cpp-pro` | Languages | `languages/cpp-pro.md` | C++ systems, performance, memory safety | Modern C++20/23, systems/embedded | Script-level tooling |
| `csharp-developer` | Languages | `languages/csharp-developer.md` | C# code, async patterns, clean arch | Language idioms, version-agnostic | Specific .NET version constraints (use platforms) |
| `elixir-expert` | Languages | `languages/elixir-expert.md` | Elixir systems, OTP, concurrency | Fault-tolerant systems, real-time | Non-Erlang VM code |
| `golang-pro` | Languages | `languages/golang-pro.md` | Go systems, concurrency, interfaces | Idiomatic Go, performance, goroutines | Framework-heavy work (use frameworks) |
| `java-architect` | Languages | `languages/java-architect.md` | Java architecture, JVM tuning | Enterprise Java, microservices, JVM | Specific framework details (use spring-boot-engineer) |
| `javascript-pro` | Languages | `languages/javascript-pro.md` | Modern JS, ES2023+, async | Language patterns, runtime behavior | Framework idioms (use frameworks) |
| `kotlin-specialist` | Languages | `languages/kotlin-specialist.md` | Kotlin idioms, coroutines, multiplatform | Language semantics, functional patterns | Android-specific UI (use kotlin-android-expert or flutter) |
| `php-pro` | Languages | `languages/php-pro.md` | PHP 8.3+, strict typing, modern patterns | Language features, async/Fiber | Framework conventions (use laravel-specialist or symfony-specialist) |
| `python-pro` | Languages | `languages/python-pro.md` | Python code, typing, async, performance | Language idioms, type safety, performance | Web framework specifics (use fastapi-developer or django-developer) |
| `rust-engineer` | Languages | `languages/rust-engineer.md` | Rust systems, ownership, lifetimes | Memory safety, systems, async | Web frameworks (consider framework agents if existed) |
| `sql-pro` | Languages | `languages/sql-pro.md` | SQL queries, schema design, optimization | Query patterns, indexes, performance | Database-specific (use database-optimizer or postgres-pro) |
| `swift-expert` | Languages | `languages/swift-expert.md` | Swift idioms, concurrency, protocols | Language semantics, server-side Swift, iOS language patterns | iOS-specific frameworks (consider swift-ios-expert in future) |
| `typescript-pro` | Languages | `languages/typescript-pro.md` | Advanced TypeScript, generics, types | Type system design, type-level programming | Framework specifics (use frameworks) |
| `angular-architect` | Frameworks/Web | `frameworks/web/angular-architect.md` | Angular apps, RxJS, state management, enterprise | Angular enterprise patterns, complexity | Non-Angular work (use frameworks or languages) |
| `django-developer` | Frameworks/Web | `frameworks/web/django-developer.md` | Django apps, ORM, REST APIs | Django-idiomatic development | Pure Python idioms (use python-pro) |
| `fastapi-developer` | Frameworks/Web | `frameworks/web/fastapi-developer.md` | FastAPI services, Pydantic, async | Async APIs, validation, performance | Pure Python (use python-pro) |
| `laravel-specialist` | Frameworks/Web | `frameworks/web/laravel-specialist.md` | Laravel apps, Eloquent, queues | Laravel idioms, ORM, real-time | Pure PHP patterns (use php-pro) |
| `nextjs-developer` | Frameworks/Web | `frameworks/web/nextjs-developer.md` | Next.js apps, SSR, App Router | Full-stack Next.js development | Pure JavaScript/React (use javascript-pro or react-specialist) |
| `node-specialist` | Frameworks/Web | `frameworks/web/node-specialist.md` | Node.js services, streams, modules | Node.js ecosystem, microservices | Language-level JS (use javascript-pro or typescript-pro) |
| `react-specialist` | Frameworks/Web | `frameworks/web/react-specialist.md` | React optimization, hooks, state mgmt | Existing React codebase optimization | Framework selection (use frontend-developer) |
| `rails-expert` | Frameworks/Web | `frameworks/web/rails-expert.md` | Rails apps, ActiveRecord, Hotwire | Rails-idiomatic development | Ruby language patterns (no pure Ruby agent yet) |
| `spring-boot-engineer` | Frameworks/Web | `frameworks/web/spring-boot-engineer.md` | Spring Boot apps, cloud-native | Spring-idiomatic microservices | Pure Java patterns (use java-architect) |
| `symfony-specialist` | Frameworks/Web | `frameworks/web/symfony-specialist.md` | Symfony apps, DI, Doctrine | Symfony framework conventions | Pure PHP (use php-pro) |
| `vue-expert` | Frameworks/Web | `frameworks/web/vue-expert.md` | Vue 3, Composition API, Nuxt | Vue-idiomatic apps, Nuxt | Framework-agnostic JavaScript (use javascript-pro) |
| `expo-react-native-expert` | Frameworks/Mobile | `frameworks/mobile/expo-react-native-expert.md` | Expo + React Native apps | Cross-platform mobile with React Native | Native Swift/Kotlin (use swift-expert or kotlin-specialist) |
| `flutter-expert` | Frameworks/Mobile | `frameworks/mobile/flutter-expert.md` | Flutter apps (iOS, Android, Web) | Cross-platform Dart/Flutter development | Pure Dart language (use languages tier if existed) |
| `dotnet-core-expert` | Platforms/DotNet | `platforms/dotnet/dotnet-core-expert.md` | .NET Core 5–8 cloud-native apps | Cloud deployment, modern .NET, cross-platform | Legacy .NET (use dotnet-framework-4.8-expert) |
| `dotnet-framework-4.8-expert` | Platforms/DotNet | `platforms/dotnet/dotnet-framework-4.8-expert.md` | .NET Framework 4.8 apps, legacy Windows | Maintenance, modernization of .NET 4.8 | New cloud projects (use dotnet-core-expert) |
| `powershell-5.1-expert` | Platforms/Windows | `platforms/windows-automation/powershell-5.1-expert.md` | Windows automation, AD, GPO, DSC | Windows Server infrastructure | Cross-platform (use powershell-7-expert) |
| `powershell-7-expert` | Platforms/Windows | `platforms/windows-automation/powershell-7-expert.md` | Cross-platform automation, Azure, cloud | Cloud orchestration, modern PowerShell | Windows-only legacy work (use powershell-5.1-expert) |

---

## Feedback & Iteration

This taxonomy reflects the state as of 2026-05-22. It is durable but not rigid. To propose changes:

1. **New agent doesn't fit a tier?** Discuss whether it's truly needed vs. expanding an existing agent's scope.
2. **Two agents should merge?** Use the MECE audit rubric (see `AGENT_MECE_AUDIT_RUBRIC.md`).
3. **Boundary rule unclear?** Add a concrete example (task description + expected agent choice) to the tie-breaker table above.

**Owner**: Agent Army maintainers. Reviewed: on each backlog addition; audited semi-annually.
