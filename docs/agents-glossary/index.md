# Agent Roster

Complete glossary of 169 AI specialist agents organized by expertise.

!!! note "Documents as Code"
    These agent definitions are auto-generated from source files in `.claude/agents/categories/`.
    The documentation stays in sync with actual agent definitions.

## Distribution by Category

```mermaid
pieLand
    "Business Product": 13
    "Core Development": 13
    "Data Ai": 14
    "Developer Experience": 15
    "Enterprise Architecture": 11
    "Infrastructure": 19
    "Language Specialists": 30
    "Meta Orchestration": 14
    "Quality Security": 17
    "Research Analysis": 9
    "Specialized Domains": 14
```

## All Agents


### Business Product

- **business-analyst** — Use when analyzing business processes, gathering requirements from stakeholders, or identifying process improvement opportunities to drive operational efficiency and measurable business value.
- **content-marketer** — Use this agent when you need to develop comprehensive content strategies, create SEO-optimized marketing content, or execute multi-channel content campaigns to drive engagement and conversions. Invoke this agent for content planning, content creation, audience analysis, and measuring content ROI.
- **customer-success-manager** — Use this agent when you need to assess customer health, develop retention strategies, identify upsell opportunities, or maximize customer lifetime value. Invoke this agent for account health analysis, churn prevention, product adoption optimization, and customer success planning.
- **developer-advocate** — Use this agent to drive external developer adoption — sample applications, external-audience tutorials, community engagement, and developer-feedback loops back to product. Owns adoption and community; use technical-writer for reference documentation, documentation-engineer for the docs toolchain, and content-marketer for marketing funnels.
- **legal-advisor** — Use this agent when you need to draft contracts, review compliance requirements, develop IP protection strategies, or assess legal risks for technology businesses.
- **license-engineer** — Use this agent when architecting, implementing, or optimizing end-to-end legal licensing systems—from OSI standard selection and dependency compliance pipelines to proprietary deployment and risk monitoring.
- **product-manager** — Use this agent when you need to make product strategy decisions, prioritize features, or define roadmap plans based on user needs and business goals.
- **project-manager** — Use this agent when you need to establish project plans, track execution progress, manage risks, control budget/schedule, and coordinate stakeholders across complex initiatives.
- **sales-engineer** — Use this agent when you need to conduct technical pre-sales activities including solution architecture, proof-of-concept development, and technical demonstrations for complex sales deals.
- **scrum-master** — Use when teams need facilitation, process optimization, velocity improvement, or agile ceremony management—especially for sprint planning, retrospectives, impediment removal, and scaling agile practices across multiple teams. In AgentArmy contexts: invoke for PI planning, release train scheduling, session-based velocity calibration, updating planning/release-trains/milestone calendars, capacity planning for parallel coding agents, and sprint retrospectives after each coding session.
- **technical-writer** — Use this agent when you need to create, improve, or maintain technical documentation including API references, user guides, SDK documentation, and getting-started guides.
- **ux-researcher** — Use this agent when you need to conduct user research, analyze user behavior, or generate actionable insights to validate design decisions and uncover user needs. Invoke when you need usability testing, user interviews, survey design, analytics interpretation, persona development, or competitive research to inform product strategy.
- **wordpress-master** — Use this agent when you need to architect, optimize, or troubleshoot WordPress implementations ranging from custom theme/plugin development to enterprise-scale multisite platforms. Invoke this agent for performance optimization, security hardening, headless WordPress APIs, WooCommerce solutions, and scaling WordPress to handle millions of visitors.

### Core Development

- **api-designer** — Use this agent when designing new APIs, creating API specifications, or refactoring existing API architecture for scalability and developer experience. Invoke when you need REST/GraphQL endpoint design, OpenAPI documentation, authentication patterns, or API versioning strategies.
- **async-messaging-engineer** — Use this agent for event-driven messaging — message broker design and operation (Kafka, RabbitMQ, SQS/SNS, NATS), AsyncAPI event-schema governance, dead-letter-queue strategy, and consumer-group coordination across spokes. Owns the broker layer and event-schema contracts; use integration-architect for pattern selection and websocket-engineer for client realtime transport.
- **backend-developer** — Use this agent when building server-side APIs, microservices, and backend systems that require robust architecture, scalability planning, and production-ready implementation.
- **design-bridge** — Use this agent when you need to translate a DESIGN.md from the VoltAgent/awesome-design-md repository into polished Claude Code instructions for building user interfaces that faithfully match the chosen brand. Invoke this agent whenever a developer or designer asks to replicate the look and feel of an existing product or website.
- **electron-pro** — Use this agent when building Electron desktop applications that require native OS integration, cross-platform distribution, security hardening, and performance optimization. Use electron-pro for complete desktop app development from architecture to signed, distributable installers.
- **frontend-developer** — Use when building complete frontend applications across React, Vue, and Angular frameworks requiring multi-framework expertise and full-stack integration.
- **fullstack-developer** — Use this agent when you need to build complete features spanning database, API, and frontend layers together as a cohesive unit.
- **graphql-architect** — Use this agent when designing or evolving GraphQL schemas across microservices, implementing federation architectures, or optimizing query performance in distributed graphs.
- **microservices-architect** — Use when designing distributed system architecture, decomposing monolithic applications into independent microservices, or establishing communication patterns between services at scale.
- **mobile-developer** — Use this agent when building cross-platform mobile applications using React Native or Flutter where code sharing exceeds 80% while maintaining iOS and Android native excellence. For native-only iOS or Android development, or mobile strategy decisions, use mobile-app-developer.
- **mobile-web-specialist** — Use this agent when making web applications work great on phones and tablets: responsive layouts, touch interactions, safe-area insets, canvas/WebGL sizing, viewport quirks (iOS Safari, Chrome for Android), and progressive web app setup. The right agent for fixing 'it looks bad on my phone', adding mobile media queries, or making a desktop-first visualization usable on small screens.
- **ui-designer** — Use this agent when designing visual interfaces, creating design systems, building component libraries, or refining user-facing aesthetics requiring expert visual design, interaction patterns, and accessibility considerations.
- **websocket-engineer** — Use this agent when implementing real-time bidirectional communication features using WebSockets, Socket.IO, or similar technologies at scale.

### Data Ai

- **ai-engineer** — Use this agent when architecting, implementing, or optimizing end-to-end AI systems—from model selection and training pipelines to production deployment and monitoring.
- **data-analyst** — Use when you need to extract insights from business data, create dashboards and reports, or perform statistical analysis to support decision-making.
- **data-engineer** — Use this agent when you need to design, build, or optimize data pipelines, ETL/ELT processes, and data infrastructure. Invoke when designing data platforms, implementing pipeline orchestration, handling data quality issues, or optimizing data processing costs.
- **data-scientist** — Use this agent when you need to analyze data patterns, build predictive models, or extract statistical insights from datasets. Invoke this agent for exploratory analysis, hypothesis testing, machine learning model development, and translating findings into business recommendations.
- **database-optimizer** — Use this agent when you need to analyze slow queries, optimize database performance across multiple database systems, or implement indexing strategies to improve query execution. For PostgreSQL-specific optimization and advanced features, use postgres-pro. For database infrastructure operations (HA, disaster recovery), use database-administrator.
- **dlt-engineer** — Use this agent when building, debugging, or optimizing data pipelines with dlt (data load tool). Invoke for source connector development, incremental loading strategies, schema evolution, destination configuration (DuckDB, BigQuery, Snowflake, Postgres, filesystem), pipeline orchestration with Airflow/Prefect/GitHub Actions, and transforming raw API/file/database sources into analytics-ready datasets. Also the right agent for SEC EDGAR extraction, REST API pipelines, and any source → destination ELT work in this repo.
- **llm-architect** — Use when designing LLM systems for production, implementing fine-tuning or RAG architectures, optimizing inference serving infrastructure, or managing multi-model deployments.
- **machine-learning-engineer** — Use this agent for the production ML lifecycle — model training pipelines, deployment, serving/inference infrastructure, optimization, and automated retraining at scale. Owns building and running production ML systems; use data-scientist for experimentation/modeling and mlops-engineer for the underlying ML platform, CI/CD, and experiment-tracking infrastructure.
- **mlops-engineer** — Use this agent when you need to design and implement ML infrastructure, set up CI/CD for machine learning models, establish model versioning systems, or optimize ML platforms for reliability and automation. Invoke this agent to build production-grade experiment tracking, implement automated training pipelines, configure GPU resource orchestration, and establish operational monitoring for ML systems.
- **nlp-engineer** — Use when building production NLP systems, implementing text processing pipelines, developing language models, or solving domain-specific NLP tasks like named entity recognition, sentiment analysis, or machine translation.
- **postgres-pro** — Use when you need to optimize PostgreSQL specifically: advanced query optimization, configuration tuning, replication setup, backup strategies, and mastering advanced PostgreSQL features for enterprise deployments. For generic database optimization across multiple database systems, use database-optimizer. For infrastructure operations like HA and DR, use database-administrator.
- **prompt-engineer** — Use this agent when you need to design, optimize, test, or evaluate prompts for large language models in production systems.
- **reinforcement-learning-engineer** — Use when designing RL environments, training agents with reward optimization, implementing policy gradient methods, or deploying decision-making systems for robotics, gaming, and autonomous operations.
- **schema-migration-engineer** — Use this agent for database schema versioning and migration orchestration — Flyway/Liquibase/Alembic migrations, zero-downtime and contract-safe schema evolution across spokes. Owns the migration artifact lifecycle and execution; use database-administrator for database operations and tuning.

### Developer Experience

- **build-engineer** — Use this agent when you need to optimize build performance, reduce compilation times, or scale build systems across growing teams.
- **cli-developer** — Use this agent when building command-line tools and terminal applications that require intuitive command design, cross-platform compatibility, and optimized developer experience.
- **dependency-manager** — Use this agent when you need to audit dependencies for vulnerabilities, resolve version conflicts, optimize bundle sizes, or implement automated dependency updates.
- **documentation-engineer** — Use this agent when you need to create, architect, or overhaul comprehensive documentation systems including API docs, tutorials, guides, and developer-friendly content that keeps pace with code changes.
- **dx-optimizer** — Use this agent when optimizing the complete developer workflow including build times, feedback loops, testing efficiency, and developer satisfaction metrics across the entire development environment.
- **feature-flag-engineer** — Use this agent for feature flag and progressive delivery engineering — flag strategy, targeting and lifecycle management, kill switches, and flag-debt cleanup. Owns flag definitions, targeting, and lifecycle; use deployment-engineer for the deployment strategy (canary percentages, ring rollouts) that flags enable.
- **git-workflow-manager** — Use this agent when you need to design, establish, or optimize Git workflows, branching strategies, and merge management for a project or team.
- **legacy-modernizer** — Use this agent when modernizing legacy systems that need incremental migration strategies, technical debt reduction, and risk mitigation while maintaining business continuity.
- **mcp-developer** — Use this agent when you need to build, debug, or optimize Model Context Protocol (MCP) servers and clients that connect AI systems to external tools and data sources.
- **powershell-module-architect** — Use this agent when architecting and refactoring PowerShell modules, designing profile systems, or creating cross-version compatible automation libraries. Invoke it for module design reviews, profile optimization, packaging reusable code, and standardizing function structure across teams.
- **powershell-ui-architect** — Use when designing or building desktop graphical interfaces (WinForms, WPF, Metro-style dashboards) or terminal user interfaces (TUIs) for PowerShell automation tools that need clean separation between UI and business logic.
- **readme-generator** — Use this agent when you need a maintainer-ready README built from exact repository reality, with deep codebase scanning, zero hallucination, and optional git commit/push only when explicitly requested.
- **refactoring-specialist** — Use when you need to transform poorly structured, complex, or duplicated code into clean, maintainable systems while preserving all existing behavior.
- **slack-expert** — Use this agent when developing Slack applications, implementing Slack API integrations, or reviewing Slack bot code for security and best practices.
- **tooling-engineer** — Use this agent when you need to build or enhance developer tools including CLIs, code generators, build tools, and IDE extensions.

### Enterprise Architecture

- **business-architect** — Use this agent for TOGAF Phase B Business Architecture: business capability modeling, value stream mapping, operating model design, organizational design, and stakeholder analysis. BIZBOK-aligned. Produces capability maps, heat maps, and value stream diagrams for US commercial and federal contexts.
- **capability-planner** — Use this agent to build business capability investment plans: scoring capabilities for strategic importance and performance gaps, running WSJF prioritization, building capability roadmaps, and connecting capability investments to PI planning and portfolio backlogs. Works from the capability map produced by business-architect.
- **enterprise-architect** — Use this agent when driving enterprise-wide architecture programs: establishing the architecture practice, producing Architecture Vision (TOGAF Phase A), governing the Architecture Repository, and coordinating all EA disciplines across TOGAF ADM phases. Invoke as the senior orchestrator for any multi-phase EA engagement.
- **information-architect** — Use this agent for enterprise information and data architecture: conceptual/logical/physical data models, master data management strategy, data governance frameworks, data lineage, information lifecycle management, and TOGAF Phase C data architecture deliverables. DAMA DMBOK 2 aligned, with US regulatory context (CCPA, HIPAA, FISMA, SOX).
- **integration-architect** — Use this agent to design enterprise integration architectures: API strategy and governance, event-driven architecture, canonical data models, ESB-to-event-mesh modernization, and integration patterns at scale. Covers REST/GraphQL API governance, AsyncAPI, Apache Kafka/Pulsar, and enterprise service bus patterns.
- **platform-architect** — Use this agent to design Internal Developer Platforms (IDP): Team Topologies operating model, golden path design, self-service infrastructure, developer portal (Backstage), DORA metrics integration, and platform-as-a-product strategy. Bridges TOGAF Phase D Technology Architecture with engineering execution.
- **security-architect** — Use this agent for enterprise security architecture: Zero Trust Architecture design (NIST SP 800-207), NIST CSF 2.0 program design, FedRAMP authorization support, CMMC Level 2/3 preparation, FISMA ATO processes, cloud security architecture, and identity/access management design at enterprise scale.
- **solution-architect** — Use this agent to design solution architectures that implement enterprise architecture decisions: translating Architecture Building Blocks (ABBs) into Solution Building Blocks (SBBs), producing solution architecture documents, evaluating vendor/product options against architecture constraints, and defining transition architectures for TOGAF Phases E and F.
- **togaf-adm-advisor** — Use this agent for phase-specific TOGAF ADM guidance: producing required deliverables for a named phase, understanding ADM inputs/outputs/steps, tailoring the ADM for your organization, or getting artifact templates (Architecture Vision, Statement of Architecture Work, Architecture Definition Document, etc.).
- **us-regulatory-architect** — Use this agent for US regulatory compliance architecture: FedRAMP (Low/Moderate/High), FISMA/RMF, NIST SP 800-53 control selection, CMMC 2.0 levels, HIPAA technical safeguards, PCI DSS v4, SOX IT controls, CCPA/CPRA privacy architecture, and OMB/CISA directive compliance. Translates regulatory requirements into architecture controls.
- **wardley-strategist** — Use this agent when you need Wardley Mapping analysis: decomposing a user need into a value chain, positioning components on the evolution axis, assessing organizational doctrine, analyzing climatic forces, and selecting strategic gameplay. Produces OWM syntax for rendering at create.wardleymaps.ai. US enterprise and commercial contexts.

### Infrastructure

- **api-gateway-engineer** — Use this agent to configure and operate API gateways — rate limiting, edge authentication/authorization, request routing across spoke APIs, and developer portal setup. Owns gateway runtime configuration and policy; use api-designer for the upstream contract spec and network-engineer for lower-level networking.
- **azure-infra-engineer** — Use when designing, deploying, or managing Azure infrastructure with focus on network architecture, Entra ID integration, PowerShell automation, and Bicep IaC.
- **cloud-architect** — Use this agent when you need to design, evaluate, or optimize cloud infrastructure architecture at scale. Invoke when designing multi-cloud strategies, planning cloud migrations, implementing disaster recovery, optimizing cloud costs, or ensuring security/compliance across cloud platforms.
- **database-administrator** — Use this agent for database infrastructure operations: implementing high-availability architectures, setting up disaster recovery, backup strategy, replication setup, and managing database infrastructure for production systems. For query/index optimization across multiple databases, use database-optimizer. For PostgreSQL-specific optimization and advanced features, use postgres-pro.
- **deployment-engineer** — Use this agent for release and rollout strategy on top of existing pipelines — deployment strategies (canary, blue-green, rolling), artifact promotion, GitOps, and rollback safety. Owns how releases reach production; use devops-engineer to build the CI/CD system and infrastructure automation underneath, and release-manager to coordinate release trains across multiple spoke repos.
- **devops-engineer** — Use this agent when building or operating the CI/CD system and delivery platform itself — infrastructure automation, pipeline construction, containerization, and dev↔ops collaboration. Owns the pipelines and platform; use deployment-engineer for release/rollout strategy (canary/blue-green/rollback) that runs on top of them.
- **devops-incident-responder** — Use when actively responding to production incidents, diagnosing critical service failures, or conducting incident postmortems to implement permanent fixes and preventative measures.
- **docker-expert** — Use this agent when you need to build, optimize, or secure Docker container images and orchestration for production environments.
- **finops-engineer** — Use this agent for cloud cost engineering — cost visibility, unit economics, rightsizing, Reserved Instance/Savings Plan commitments, and showback/chargeback across spokes. Owns cost as the primary deliverable; use cloud-architect for architecture decisions and sre-engineer for reliability.
- **incident-responder** — Use this agent when an active security breach, service outage, or operational incident requires immediate response, evidence preservation, and coordinated recovery.
- **kubernetes-specialist** — Use this agent when you need to design, deploy, configure, or troubleshoot Kubernetes clusters and workloads in production environments.
- **network-engineer** — Use this agent when designing, optimizing, or troubleshooting cloud and hybrid network infrastructures, or when addressing network security, performance, or reliability challenges.
- **observability-engineer** — Use this agent when instrumenting applications and services for telemetry — OpenTelemetry instrumentation, metrics/logs/traces pipelines, collector configuration, and Prometheus/Grafana dashboards. Owns producing observability data; use sre-engineer for SLOs and error budgets that consume it, and performance-engineer to diagnose bottlenecks from it.
- **platform-engineer** — Use when building or improving internal developer platforms (IDPs), designing self-service infrastructure, or optimizing developer workflows to reduce friction and accelerate delivery. The platform-engineer agent specializes in designing platform architecture, implementing golden paths, and maximizing developer self-service capabilities.
- **security-engineer** — Use this agent when implementing comprehensive security solutions across infrastructure, building automated security controls into CI/CD pipelines, or establishing compliance and vulnerability management programs. Invoke for threat modeling, zero-trust architecture design, security automation implementation, and shifting security left into development workflows.
- **sre-engineer** — Use this agent when you need to establish or improve system reliability through SLO definition, error budget management, and automation. Invoke when implementing SLI/SLO frameworks, reducing operational toil, designing fault-tolerant systems, conducting chaos engineering, or optimizing incident response processes.
- **terraform-engineer** — Use when building, refactoring, or scaling infrastructure as code using Terraform with focus on multi-cloud deployments, module architecture, and enterprise-grade state management.
- **terragrunt-expert** — Expert Terragrunt specialist mastering infrastructure orchestration, DRY configurations, and multi-environment deployments. Masters stacks, units, dependency management, and scalable IaC patterns with focus on code reuse, maintainability, and enterprise-grade infrastructure automation.
- **windows-infra-admin** — Use when managing Windows Server infrastructure, Active Directory, DNS, DHCP, and Group Policy configurations, especially for enterprise-scale deployments requiring safe automation and compliance validation.

### Language Specialists

- **angular-architect** — Use when architecting enterprise Angular 15+ applications with complex state management, optimizing RxJS patterns, designing micro-frontend systems, or solving performance and scalability challenges in large codebases.
- **cpp-pro** — Use this agent when building high-performance C++ systems requiring modern C++20/23 features, template metaprogramming, or zero-overhead abstractions for systems programming, embedded systems, or performance-critical applications.
- **csharp-developer** — Use this agent when building ASP.NET Core web APIs, cloud-native .NET solutions, or modern C# applications requiring async patterns, dependency injection, Entity Framework optimization, and clean architecture.
- **django-developer** — Use when building Django 4+ web applications, REST APIs, or modernizing existing Django projects with async views and enterprise patterns.
- **dotnet-core-expert** — Use when building .NET Core applications requiring cloud-native architecture, high-performance microservices, modern C# patterns, or cross-platform deployment with minimal APIs and advanced ASP.NET Core features.
- **dotnet-framework-4.8-expert** — Use this agent when working on legacy .NET Framework 4.8 enterprise applications that require maintenance, modernization, or integration with Windows-based infrastructure.
- **elixir-expert** — Use this agent when you need to build fault-tolerant, concurrent systems leveraging OTP patterns, GenServer architectures, and Phoenix framework for real-time applications.
- **expo-react-native-expert** — Use when building mobile applications with Expo and React Native that require native module integration, navigation setup, performant animations, push notifications, OTA updates, or App Store/Play Store deployment.
- **fastapi-developer** — Use when building modern async Python APIs with FastAPI, implementing Pydantic v2 validation, dependency injection patterns, or deploying high-performance ASGI applications.
- **flutter-expert** — Use when building cross-platform mobile applications with Flutter 3+ that require custom UI implementation, complex state management, native platform integrations, or performance optimization across iOS/Android/Web.
- **golang-pro** — Use when building Go applications requiring concurrent programming, high-performance systems, microservices, or cloud-native architectures where idiomatic patterns, error handling excellence, and efficiency are critical.
- **java-architect** — Use this agent when designing enterprise Java architectures, migrating Spring Boot applications, or establishing microservices patterns for scalable cloud-native systems.
- **javascript-pro** — Use this agent when you need to build, optimize, or refactor modern JavaScript code for browser, Node.js, or full-stack applications requiring ES2023+ features, async patterns, or performance-critical implementations.
- **kotlin-specialist** — Use when building Kotlin applications requiring advanced coroutine patterns, multiplatform code sharing, or Android/server-side development with functional programming principles.
- **laravel-specialist** — Use when building Laravel 10+ applications, architecting Eloquent models with complex relationships, implementing queue systems for async processing, or optimizing API performance.
- **nextjs-developer** — Use this agent when building production Next.js 14+ applications that require full-stack development with App Router, server components, and advanced performance optimization. Invoke when you need to architect or implement complete Next.js applications, optimize Core Web Vitals, implement server actions and mutations, or deploy SEO-optimized applications.
- **node-specialist** — Use this agent when you need to build, optimize, or debug Node.js backend applications, APIs, CLIs, or microservices requiring deep ecosystem knowledge and server-side JavaScript expertise.
- **php-pro** — Use this agent when working with PHP 8.3+ projects that require strict typing, modern language features, and enterprise framework expertise (Laravel or Symfony). Use when building scalable applications, optimizing performance, or requiring async/Fiber patterns.
- **powershell-5.1-expert** — Use when automating Windows infrastructure tasks requiring PowerShell 5.1 scripts with RSAT modules for Active Directory, DNS, DHCP, GPO management, or when building safe, enterprise-grade automation workflows in legacy .NET Framework environments.
- **powershell-7-expert** — Use when building cross-platform cloud automation scripts, Azure infrastructure orchestration, or CI/CD pipelines requiring PowerShell 7+ with modern .NET interop, idempotent operations, and enterprise-grade error handling.
- **python-pro** — Use this agent when you need to build type-safe, production-ready Python code for web APIs, system utilities, or complex applications requiring modern async patterns and extensive type coverage.
- **rails-expert** — Use when building or modernizing Rails applications requiring API development, Hotwire reactivity, real-time features, background job processing, deployment automation, or Rails-idiomatic patterns for maximum productivity. Version-aware: adapts to Rails 7.x and 8.x projects.
- **react-specialist** — Use when optimizing existing React applications for performance, implementing advanced React 18+ features, or solving complex state management and architectural challenges within React codebases.
- **rust-engineer** — Use when building Rust systems where memory safety, ownership patterns, zero-cost abstractions, and performance optimization are critical for systems programming, embedded development, async applications, or high-performance services.
- **spring-boot-engineer** — Use this agent when building enterprise Spring Boot 3+ applications requiring microservices architecture, cloud-native deployment, or reactive programming patterns.
- **sql-pro** — Use this agent when you need to optimize complex SQL queries, design efficient database schemas, or solve performance issues across PostgreSQL, MySQL, SQL Server, and Oracle requiring advanced query optimization, index strategies, or data warehouse patterns.
- **swift-expert** — Use this agent when building native iOS, macOS, or server-side Swift applications requiring advanced concurrency patterns, protocol-oriented architecture, and Swift-specific optimizations. Invoke for SwiftUI modernization, async/await implementation, actor-based state management, or memory safety concerns.
- **symfony-specialist** — Use when building Symfony 6+/7+/8+ applications, architecting Doctrine ORM entities with complex relationships, implementing Messenger component for async processing, or optimizing API Platform performance.
- **typescript-pro** — Use when implementing TypeScript code requiring advanced type system patterns, complex generics, type-level programming, or end-to-end type safety across full-stack applications.
- **vue-expert** — Use this agent when building Vue 3 applications that require Composition API mastery, reactivity optimization, or Nuxt 3 development with enterprise-scale performance concerns.

### Meta Orchestration

- **agent-distinctiveness-advocate** — Use this agent to audit new agents for MECE compliance before merging, ensure semantic distinctiveness across the roster, resolve boundary disputes between overlapping agents, or validate that descriptions guide unambiguous routing. Invoke when onboarding agents, resolving routing ambiguity in production, or periodically (semi-annually) to maintain taxonomic health.
- **agent-installer** — Use this agent when the user wants to discover, browse, or install Claude Code agents from the awesome-claude-code-subagents repository.
- **agent-organizer** — Use when assembling and optimizing multi-agent teams to execute complex projects that require careful task decomposition, agent capability matching, and workflow coordination.
- **codebase-orchestrator** — Use this agent when you need repository-wide refactor governance with explicit approval loops, weighted risk prioritization, diff previews, and deterministic fallback strategies.
- **context-manager** — Use for managing shared state, information retrieval, and data synchronization when multiple agents need coordinated access to context and metadata.
- **error-coordinator** — Use this agent when distributed system errors occur and need coordinated handling across multiple components, or when you need to implement comprehensive error recovery strategies with automated failure detection and cascade prevention.
- **hitl-coordinator** — Use when any agent hits a decision point requiring human judgment, creative direction, or architectural divergence from established system design. Creates structured Decision Artifact issues on the GitHub Projects board, sets up blocking relationships across dependent work items, and after a human or AI app decides, synthesizes the response and routes work forward with the decision embedded. Distinct from codebase-orchestrator (which runs local code-diff approval loops) — hitl-coordinator surfaces decisions to the GitHub Projects board and manages the full cross-session HITL lifecycle.
- **it-ops-orchestrator** — Use for orchestrating complex IT operations tasks that span multiple domains (PowerShell automation, .NET development, infrastructure management, Azure, M365) by intelligently routing work to specialized agents.
- **knowledge-synthesizer** — Use when you need to extract actionable patterns from agent interactions, synthesize insights across multiple workflows, and enable organizational learning from collective experience.
- **multi-agent-coordinator** — Use when coordinating multiple concurrent agents that need to communicate, share state, synchronize work, and handle distributed failures across a system.
- **performance-monitor** — Use when establishing observability infrastructure to track system metrics, detect performance anomalies, and optimize resource usage across multi-agent environments.
- **release-manager** — Use this agent to coordinate cross-spoke release trains across multiple repositories — cut ordering by dependency, dependency-order tagging, cross-repo changelog aggregation, and semver coordination. Owns multi-spoke release coordination only; use deployment-engineer for single-service release/rollout and git-workflow-manager for branch strategy.
- **task-distributor** — Use when distributing tasks across multiple agents or workers, managing queues, and balancing workloads to maximize throughput while respecting priorities and deadlines.
- **workflow-orchestrator** — Use this agent when you need to design, implement, or optimize complex business process workflows with multiple states, error handling, and transaction management.

### Quality Security

- **accessibility-tester** — Use this agent when you need comprehensive accessibility testing, WCAG compliance verification, or assessment of assistive technology support.
- **ad-security-reviewer** — Use this agent when you need to audit Active Directory security posture, evaluate privilege escalation risks, review identity delegation patterns, or assess authentication protocol hardening.
- **ai-writing-auditor** — Use this agent when you need to audit content for AI writing patterns and rewrite text to remove them.
- **architect-reviewer** — Use this agent when you need to evaluate system design decisions, architectural patterns, and technology choices at the macro level.
- **chaos-engineer** — Use this agent when you need to design and execute controlled failure experiments, validate system resilience before incidents occur, or conduct game day exercises to test your team's incident response capabilities.
- **code-reviewer** — Use this agent when you need to conduct comprehensive code reviews focusing on code quality, security vulnerabilities, and best practices.
- **compliance-auditor** — Use this agent when you need to achieve regulatory compliance, implement compliance controls, or prepare for audits across frameworks like GDPR, HIPAA, PCI DSS, SOC 2, and ISO standards.
- **contract-test-engineer** — Use this agent for consumer-driven contract testing across services and spokes — Pact broker setup, provider verification, and schema-drift detection. Owns contract enforcement at runtime; use test-automator for other automated tests (unit/integration/e2e/load) and api-designer for authoring the contract.
- **debugger** — Use this agent when you need to diagnose and fix bugs in a single service or local codebase, identify root causes of failures within one system, or analyze error logs and stack traces to resolve issues. For distributed system error correlation across multiple services, use error-detective.
- **error-detective** — Use this agent when you need to diagnose and correlate errors across a distributed system, identify root causes spanning multiple services, analyze error cascades, and prevent future failures at scale. For single-service bug fixing and local diagnosis, use debugger.
- **penetration-tester** — Use this agent when you need to conduct authorized security penetration tests to identify real vulnerabilities through active exploitation and validation. Use penetration-tester for offensive security testing, vulnerability exploitation, and hands-on risk demonstration.
- **performance-engineer** — Use this agent when you need to identify and eliminate performance bottlenecks in applications, databases, or infrastructure systems, and when baseline performance metrics need improvement.
- **powershell-security-hardening** — Use this agent when you need to harden PowerShell automation, secure remoting configuration, enforce least-privilege design, or align scripts with enterprise security baselines and compliance frameworks.
- **qa-expert** — Use this agent when you need comprehensive quality assurance strategy, test planning across the entire development cycle, or quality metrics analysis to improve overall software quality. For building and implementing automated test frameworks and CI/CD integration, use test-automator.
- **security-auditor** — Use this agent when conducting comprehensive security audits, compliance assessments, or risk evaluations across systems, infrastructure, and processes. Invoke when you need systematic vulnerability analysis, compliance gap identification, or evidence-based security findings.
- **test-automator** — Use this agent when you need to build, implement, or enhance automated test frameworks, create test scripts, or integrate testing into CI/CD pipelines. For QA strategy, test planning, and quality metrics analysis, use qa-expert.
- **ui-ux-tester** — Use this agent when you need exhaustive UI and UX functionality testing driven by documented user flows, with browser or desktop interaction tooling and structured defect reporting.

### Research Analysis

- **competitive-analyst** — Use when you need to analyze direct and indirect competitors, benchmark against market leaders, or develop strategies to strengthen competitive positioning and market advantage.
- **data-researcher** — Use this agent when you need to discover, collect, and validate data from multiple sources to fuel analysis and decision-making. Invoke this agent for identifying data sources, gathering raw datasets, performing quality checks, and preparing data for downstream analysis or modeling.
- **market-researcher** — Use this agent when you need to analyze markets, understand consumer behavior, assess competitive landscapes, and size opportunities to inform business strategy and market entry decisions.
- **project-idea-validator** — Use this agent when you need an idea pressure-tested with brutal honesty, competitor teardown, market validation, and clear go/no-go guidance before building.
- **research-analyst** — Use this agent when you need comprehensive research across multiple sources with synthesis of findings into actionable insights, trend identification, and detailed reporting.
- **scientific-literature-researcher** — Use when you need to search scientific literature and retrieve structured experimental data from published studies. Invoke this agent when the task requires evidence-grounded answers from full-text research papers, including methods, results, sample sizes, and quality scores.
- **search-specialist** — Use when you need to find specific information across multiple sources using advanced search strategies, query optimization, and targeted information retrieval. Invoke this agent when the priority is locating precise, relevant results efficiently rather than analyzing or synthesizing content.
- **spike-researcher** — Use this agent for time-boxed technical spikes that produce runnable proof-of-concept code and a build-vs-buy recommendation — library/framework evaluation with working evidence. Produces a PoC branch plus recommendation; use research-analyst for written analysis without code and project-idea-validator for product idea validation.
- **trend-analyst** — Use when analyzing emerging patterns, predicting industry shifts, or developing future scenarios to inform strategic planning and competitive positioning.

### Specialized Domains

- **api-documenter** — Use this agent when creating or improving API documentation, writing OpenAPI specifications, building interactive documentation portals, or generating code examples for APIs.
- **blockchain-developer** — Use this agent when building smart contracts, DApps, and blockchain protocols that require expertise in Solidity, gas optimization, security auditing, and Web3 integration.
- **embedded-systems** — Use when developing firmware for resource-constrained microcontrollers, implementing RTOS-based applications, or optimizing real-time systems where hardware constraints, latency guarantees, and reliability are critical.
- **fintech-engineer** — Use when building payment systems, financial integrations, or compliance-heavy financial applications that require secure transaction processing, regulatory adherence, and high transaction accuracy.
- **game-developer** — Use this agent when implementing game systems, optimizing graphics rendering, building multiplayer networking, or developing gameplay mechanics for games targeting specific platforms.
- **github-projects-manager** — Use this agent when you need to create, read, update, or query GitHub Projects v2 boards — including project items, issues, milestones, custom fields, views, and sprint-style iterations. Invoke when connecting a codebase to a kanban/project board, triaging issues into a project, or reporting project status.
- **healthcare-admin** — Use when working on healthcare administration tasks including revenue cycle management, HIPAA/compliance auditing, medical coding (ICD-10, CPT, DRGs), CMS cost reports, payer contract analysis, quality improvement, clinical operations, health IT/interoperability, population health, and pharmacy benefits.
- **iot-engineer** — Use when designing and deploying IoT solutions requiring expertise in device management, edge computing, cloud integration, and handling challenges like massive device scale, complex connectivity scenarios, or real-time data pipelines.
- **m365-admin** — Use when automating Microsoft 365 administrative tasks including Exchange Online mailbox provisioning, Teams collaboration management, SharePoint site configuration, license lifecycle management, and Graph API-driven identity automation.
- **mobile-app-developer** — Use this agent when developing native iOS and Android applications or making platform-specific mobile strategy decisions. For cross-platform mobile applications using React Native or Flutter where code sharing exceeds 80%, use mobile-developer.
- **payment-integration** — Use this agent when implementing payment systems, integrating payment gateways, or handling financial transactions that require PCI compliance, fraud prevention, and secure transaction processing.
- **quant-analyst** — Use this agent when you need to develop quantitative trading strategies, build financial models with rigorous mathematical foundations, or conduct advanced risk analytics for derivatives and portfolios. Invoke this agent for statistical arbitrage strategy development, backtesting with historical validation, derivatives pricing models, and portfolio risk assessment.
- **risk-manager** — Use this agent when you need to identify, quantify, and mitigate enterprise-level risks across financial, operational, regulatory, and strategic domains. Invoke this agent when you need to assess risk exposure, design control frameworks, validate risk models, or ensure regulatory compliance.
- **seo-specialist** — Use this agent when you need comprehensive SEO optimization encompassing technical audits, keyword strategy, content optimization, and search rankings improvement.
