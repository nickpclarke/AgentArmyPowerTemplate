# Language Specialist Routing

Guide to routing language-level work to the right specialist.

## The Three Tiers

Language routing is structured in three distinct tiers (MECE) to avoid ambiguity:

### Tier 1: Languages (Idioms, Runtime, Type Systems)
Use when you need language expertise: type system design, performance optimization, runtime semantics, idiomatic patterns.

| Language | Specialist | Use For |
|----------|-----------|---------|
| **Python** | `python-pro` | Performance optimization, async patterns, type safety |
| **TypeScript** | `typescript-pro` | Type system expertise, generics, type-level programming |
| **JavaScript** | `javascript-pro` | ES2023+ features, browser APIs, async/await |
| **Go** | `golang-pro` | Goroutines, channels, concurrency, performance |
| **Rust** | `rust-engineer` | Ownership, lifetimes, zero-cost abstractions |
| **Java** | `java-architect` | Enterprise patterns, generics, concurrent design |
| **C++** | `cpp-pro` | Modern C++20/23, templates, performance |
| **C#** | `csharp-developer` | Async patterns, LINQ, type safety |
| **Kotlin** | `kotlin-specialist` | Coroutines, functional patterns |
| **PHP** | `php-pro` | Modern PHP 8.3+, type safety, async |
| **Swift** | `swift-expert` | Concurrency, protocol-oriented design |
| **Elixir** | `elixir-expert` | OTP patterns, fault tolerance |
| **Ruby/Rails** | `rails-expert` | Idiomatic Rails, ActiveRecord |

**Decision Rule**: "Build a REST API in Python" → First use `python-pro` for design decisions, then apply `fastapi-developer` for framework.

---

### Tier 2: Web Frameworks & ORMs
Use when building applications WITH a framework: conventions, libraries, patterns specific to that framework.

| Framework | Specialist | Language |
|-----------|-----------|----------|
| **FastAPI** | `fastapi-developer` | Python |
| **Django** | `django-developer` | Python |
| **Spring Boot** | `spring-boot-engineer` | Java |
| **ASP.NET Core** | `dotnet-core-expert` | C# |
| **.NET Framework 4.8** | `dotnet-framework-4.8-expert` | C# |
| **Laravel** | `laravel-specialist` | PHP |
| **Symfony** | `symfony-specialist` | PHP |
| **Rails** | `rails-expert` | Ruby |
| **Elixir/Phoenix** | `elixir-expert` | Elixir |
| **Next.js** | `nextjs-developer` | TypeScript/JavaScript |
| **React** | `react-specialist` | TypeScript/JavaScript |
| **Vue 3** | `vue-expert` | TypeScript/JavaScript |
| **Angular 15+** | `angular-architect` | TypeScript |
| **Nuxt 3** | `nextjs-developer` | TypeScript/JavaScript |
| **GraphQL** | `graphql-architect` | Any (Federated design) |

**Decision Rule**: "Optimize React component perf" → Use `react-specialist`, not generic `typescript-pro` or `javascript-pro`.

---

### Tier 3: Mobile & Cross-Platform
Use for mobile-specific work: platform APIs, native optimizations, cross-platform code sharing.

| Framework | Specialist | Target |
|-----------|-----------|--------|
| **React Native** | `expo-react-native-expert` | iOS/Android |
| **Flutter** | `flutter-expert` | iOS/Android/Web |
| **Native iOS** | `mobile-app-developer` | iOS |
| **Native Android** | `mobile-app-developer` | Android |
| **Mobile Web** | `mobile-web-specialist` | Responsive, touch, Safari/Chrome mobile |
| **Electron** | `electron-pro` | Desktop (Mac/Windows/Linux) |

**Decision Rule**: "Make our web app work on phones" → Use `mobile-web-specialist`. "Build a React Native app" → Use `expo-react-native-expert`.

---

### Tier 4: Version-Pinned & OS-Bound Work
Use for version-specific or OS-specific platforms where version matters.

| Platform | Specialist | When |
|----------|-----------|------|
| **.NET Core** (latest) | `dotnet-core-expert` | Modern cloud-native |
| **.NET Framework 4.8** | `dotnet-framework-4.8-expert` | Legacy enterprise systems |
| **PowerShell 7+** | `powershell-7-expert` | Cloud automation, cross-platform |
| **PowerShell 5.1** | `powershell-5.1-expert` | Legacy Windows automation |
| **Windows Server** | `windows-infra-admin` | Infrastructure, Group Policy |
| **Azure** | `azure-infra-engineer` | Cloud infrastructure |

**Decision Rule**: "Migrate from .NET Framework 4.8 to Core" → Start with `dotnet-framework-4.8-expert`, then involve `dotnet-core-expert`.

---

## Quick Decision Matrix

### "Build a REST API"
```
Python  → python-pro (design) → fastapi-developer (FastAPI) OR django-developer (Django)
Go      → golang-pro (design) → (implement directly, minimal framework)
Rust    → rust-engineer (design) → actix/axum (minimal frameworks)
Java    → java-architect (design) → spring-boot-engineer (Spring)
.NET    → csharp-developer (design) → dotnet-core-expert (ASP.NET Core)
```

### "Optimize Database Queries"
```
PostgreSQL      → postgres-pro
MySQL/Oracle    → sql-pro
General (any)   → database-optimizer
```

### "Fix Async/Await Bug"
```
Python  → python-pro
Go      → golang-pro
Rust    → rust-engineer
Node.js → javascript-pro OR typescript-pro
C#      → csharp-developer
```

### "Refactor Monolith"
```
Large codebase  → Delegate to language-specialist first to assess
Then:           → Refactoring-specialist for systematic transformation
Architecture:   → architect-reviewer for decomposition strategy
```

---

## Escalation & Cross-Specialist Work

| Scenario | Specialists |
|----------|-------------|
| New API + Web UI | `backend-developer` + `frontend-developer` |
| Performance bottleneck in React app | `react-specialist` + `performance-engineer` |
| Async bug in TypeScript backend | `typescript-pro` + `node-specialist` |
| Database optimization + Python code | `database-optimizer` + `python-pro` |
| Migrate from .NET Framework to Core | `dotnet-framework-4.8-expert` → `dotnet-core-expert` |

---

## Edge Cases & Tie-Breakers

### JavaScript vs TypeScript
- **JavaScript**: `javascript-pro` — ES2023+, browser APIs, ecosystem depth
- **TypeScript**: `typescript-pro` — Type systems, generics, type-level programming
- **React App**: `react-specialist` — Component architecture, state management
- **Decision**: Use `typescript-pro` for type design. Use `react-specialist` for component optimization.

### Multiple Languages in One Project
Example: Python backend + React frontend + Flutter mobile
```
1. Create separate issues per layer
2. Route backend issue → python-pro or fastapi-developer
3. Route frontend issue → react-specialist
4. Route mobile issue → expo-react-native-expert
5. Coordinator → fullstack-developer OR scrum-master
```

### Greenfield vs Optimization
- **Greenfield**: Use language specialist first (design patterns)
- **Optimization**: Use framework specialist (conventions) or performance-engineer (bottlenecks)

---

## Full Agent Roster

See [agents.md](agents.md) for 168+ specialist definitions across all categories.
