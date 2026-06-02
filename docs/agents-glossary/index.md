# Agent Roster

Complete glossary of 39 AI specialist agents organized by expertise.

!!! note "Documents as Code"
    These agent definitions are auto-generated from source files in `.claude/agents/categories/`.
    The documentation stays in sync with actual agent definitions.

## Distribution by Category

```mermaid
pieLand
    "Business Product": 5
    "Core Development": 5
    "Developer Experience": 4
    "Enterprise Architecture": 4
    "Infrastructure": 6
    "Language Specialists": 3
    "Meta Orchestration": 4
    "Quality Security": 5
    "Research Analysis": 2
    "Specialized Domains": 1
```

## All Agents


### Business Product

- **business-analyst** — Use when analyzing business processes, gathering requirements from stakeholders, or identifying process improvement opportunities to drive operational efficiency and measurable business value.
- **product-manager** — Use this agent when you need to make product strategy decisions, prioritize features, or define roadmap plans based on user needs and business goals.
- **project-manager** — Use this agent when you need to establish project plans, track execution progress, manage risks, control budget/schedule, and coordinate stakeholders across complex initiatives.
- **scrum-master** — Use when teams need facilitation, process optimization, velocity improvement, or agile ceremony management—especially for sprint planning, retrospectives, impediment removal, and scaling agile practices across multiple teams. In AgentArmyPowerTemplate contexts: invoke for PI planning, release train scheduling, session-based velocity calibration, updating docs/release-trains/milestone calendars, capacity planning for parallel coding agents, and sprint retrospectives after each coding session.
- **ux-researcher** — Use this agent when you need to conduct user research, analyze user behavior, or generate actionable insights to validate design decisions and uncover user needs. Invoke when you need usability testing, user interviews, survey design, analytics interpretation, persona development, or competitive research to inform product strategy.

### Core Development

- **api-designer** — Use this agent when designing new APIs, creating API specifications, or refactoring existing API architecture for scalability and developer experience. Invoke when you need REST/GraphQL endpoint design, OpenAPI documentation, authentication patterns, or API versioning strategies.
- **backend-developer** — Use this agent when building server-side APIs, microservices, and backend systems that require robust architecture, scalability planning, and production-ready implementation.
- **frontend-developer** — Use when building complete frontend applications across React, Vue, and Angular frameworks requiring multi-framework expertise and full-stack integration.
- **fullstack-developer** — Use this agent when you need to build complete features spanning database, API, and frontend layers together as a cohesive unit.
- **ui-designer** — Use this agent when designing visual interfaces, creating design systems, building component libraries, or refining user-facing aesthetics requiring expert visual design, interaction patterns, and accessibility considerations.

### Developer Experience

- **dependency-manager** — Use this agent when you need to audit dependencies for vulnerabilities, resolve version conflicts, optimize bundle sizes, or implement automated dependency updates.
- **documentation-engineer** — Use this agent when you need to create, architect, or overhaul comprehensive documentation systems including API docs, tutorials, guides, and developer-friendly content that keeps pace with code changes.
- **git-workflow-manager** — Use this agent when you need to design, establish, or optimize Git workflows, branching strategies, and merge management for a project or team.
- **readme-generator** — Use this agent when you need a maintainer-ready README built from exact repository reality, with deep codebase scanning, zero hallucination, and optional git commit/push only when explicitly requested.

### Enterprise Architecture

- **business-architect** — Use this agent for TOGAF Phase B Business Architecture: business capability modeling, value stream mapping, operating model design, organizational design, and stakeholder analysis. BIZBOK-aligned. Produces capability maps, heat maps, and value stream diagrams for US commercial and federal contexts.
- **capability-planner** — Use this agent to build business capability investment plans: scoring capabilities for strategic importance and performance gaps, running WSJF prioritization, building capability roadmaps, and connecting capability investments to PI planning and portfolio backlogs. Works from the capability map produced by business-architect.
- **enterprise-architect** — Use this agent when driving enterprise-wide architecture programs: establishing the architecture practice, producing Architecture Vision (TOGAF Phase A), governing the Architecture Repository, and coordinating all EA disciplines across TOGAF ADM phases. Invoke as the senior orchestrator for any multi-phase EA engagement.
- **wardley-strategist** — Use this agent when you need Wardley Mapping analysis: decomposing a user need into a value chain, positioning components on the evolution axis, assessing organizational doctrine, analyzing climatic forces, and selecting strategic gameplay. Produces OWM syntax for rendering at create.wardleymaps.ai. US enterprise and commercial contexts.

### Infrastructure

- **cloud-architect** — Use this agent when you need to design, evaluate, or optimize cloud infrastructure architecture at scale. Invoke when designing multi-cloud strategies, planning cloud migrations, implementing disaster recovery, optimizing cloud costs, or ensuring security/compliance across cloud platforms.
- **deployment-engineer** — Use this agent for release and rollout strategy on top of existing pipelines — deployment strategies (canary, blue-green, rolling), artifact promotion, GitOps, and rollback safety.
- **devops-engineer** — Use this agent when building or operating the CI/CD system and delivery platform itself — infrastructure automation, pipeline construction, containerization, and dev↔ops collaboration.
- **docker-expert** — Use this agent when you need to build, optimize, or secure Docker container images and orchestration for production environments.
- **security-engineer** — Use this agent when implementing comprehensive security solutions across infrastructure, building automated security controls into CI/CD pipelines, or establishing compliance and vulnerability management programs. Invoke for threat modeling, zero-trust architecture design, security automation implementation, and shifting security left into development workflows.
- **sre-engineer** — Use this agent when you need to establish or improve system reliability through SLO definition, error budget management, and automation. Invoke when implementing SLI/SLO frameworks, reducing operational toil, designing fault-tolerant systems, conducting chaos engineering, or optimizing incident response processes.

### Language Specialists

- **javascript-pro** — Use this agent when you need to build, optimize, or refactor modern JavaScript code for browser, Node.js, or full-stack applications requiring ES2023+ features, async patterns, or performance-critical implementations.
- **python-pro** — Use this agent when you need to build type-safe, production-ready Python code for web APIs, system utilities, or complex applications requiring modern async patterns and extensive type coverage.
- **typescript-pro** — Use when implementing TypeScript code requiring advanced type system patterns, complex generics, type-level programming, or end-to-end type safety across full-stack applications.

### Meta Orchestration

- **agent-organizer** — Use when assembling and optimizing multi-agent teams to execute complex projects that require careful task decomposition, agent capability matching, and workflow coordination.
- **hitl-coordinator** — Use when any agent hits a decision point requiring human judgment, creative direction, or architectural divergence from established system design. Creates structured Decision Artifact issues on the GitHub Projects board, sets up blocking relationships across dependent work items, and after a human or AI app decides, synthesizes the response and routes work forward with the decision embedded.
- **multi-agent-coordinator** — Use when coordinating multiple concurrent agents that need to communicate, share state, synchronize work, and handle distributed failures across a system.
- **workflow-orchestrator** — Use this agent when you need to design, implement, or optimize complex business process workflows with multiple states, error handling, and transaction management.

### Quality Security

- **accessibility-tester** — Use this agent when you need comprehensive accessibility testing, WCAG compliance verification, or assessment of assistive technology support.
- **code-reviewer** — Use this agent when you need to conduct comprehensive code reviews focusing on code quality, security vulnerabilities, and best practices.
- **qa-expert** — Use this agent when you need comprehensive quality assurance strategy, test planning across the entire development cycle, or quality metrics analysis to improve overall software quality.
- **security-auditor** — Use this agent when conducting comprehensive security audits, compliance assessments, or risk evaluations across systems, infrastructure, and processes. Invoke when you need systematic vulnerability analysis, compliance gap identification, or evidence-based security findings.
- **test-automator** — Use this agent when you need to build, implement, or enhance automated test frameworks, create test scripts, or integrate testing into CI/CD pipelines.

### Research Analysis

- **research-analyst** — Use this agent when you need comprehensive research across multiple sources with synthesis of findings into actionable insights, trend identification, and detailed reporting.
- **spike-researcher** — Use this agent for time-boxed technical spikes that produce runnable proof-of-concept code and a build-vs-buy recommendation — library/framework evaluation with working evidence. Produces a PoC branch plus recommendation.

### Specialized Domains

- **github-projects-manager** — Use this agent when you need to create, read, update, or query GitHub Projects v2 boards — including project items, issues, milestones, custom fields, views, and sprint-style iterations. Invoke when connecting a codebase to a kanban/project board, triaging issues into a project, or reporting project status.
