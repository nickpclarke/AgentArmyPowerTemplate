# Glossary

## Armies & Agents

**Army** — A specialized group of AI agents that operate together. AgentArmy has three armies: Claude Code, GitHub Copilot, and dlt.

**Agent** — A single AI specialist with expertise in a specific domain (e.g., `react-specialist`, `dlt-engineer`). See [agents.md](agents.md) for the full roster.

**Agent Distinctiveness** — Property of agents that they are semantically non-overlapping (MECE). Each agent handles a specific, well-defined scope without duplication.

**MECE** — Mutually Exclusive, Collectively Exhaustive. Framework for organizing agents so routing is unambiguous and complete coverage is guaranteed.

**Specialist** — A Claude agent with deep expertise in a narrow domain (e.g., `postgres-pro`, `kubernetes-specialist`). Distinguished from generalist agents.

## GitHub Projects & Workflow

**GitHub Projects v2** — Beta GitHub feature providing a shared task board with custom fields. Single source of truth for all armies.

**Issue** — A unit of work tracked on GitHub Projects. Has Type, Size, Estimate, PI, Status, etc.

**PR (Pull Request)** — Code change proposed for merge. Must link back to issue with `Closes #N`.

**Type** — Custom field on issue: Epic, Feature, Story, Enabler, Bug, Spike, Decision. Defines hierarchy and kind of work.

**Size** — Custom field on issue: XS, S, M, L, XL. T-shirt estimate for routing and effort prediction.

**Estimate** — Custom field on issue: Story points (1,2,3,5,8,13). Fibonacci scale for velocity tracking.

**Priority** — Custom field on issue: P0 (must ship this sprint), P1 (should ship this PI), P2 (backlog).

**PI (Program Increment)** — ~10-week planning horizon with a goal, multiple sprints, and quarterly business review. Tracked as GitHub Milestone.

**Status** — Field tracking work state: Todo → Ready → In Progress → In Review → Done, with **Awaiting Decision** as a hold state when a HITL decision is required. The `auto-status` workflow sets In Progress on PR open and Done on PR merge (with `Closes #N`); Ready and In Review are set manually.

**Iteration** — 2-week sprint. Assigned to issues during sprint planning.

**Acceptance Criteria** — Definition of what "done" means for a Story. Written as checklist in issue body.

**Definition of Ready (DoR)** — Criteria issue must meet before work starts: Type, PI, Size, Estimate, acceptance criteria set.

**Definition of Done (DoD)** — Criteria before issue can move to Done: Code merged, tests passing, `Closes #N` in PR body.

## SAFe Framework

**SAFe** — Scaled Agile Framework. Hierarchical planning model: Portfolio → Program → Team, across multiple PIs.

**PI Planning** — Quarterly event where features are estimated, prioritized, and assigned to sprints. Output: PI Goal and committed stories.

**Velocity** — Average story points completed per sprint. Used to forecast PI capacity.

**Backlog Grooming** — Refinement session where upcoming stories get Size and Estimate.

**Sprint Goal** — Outcome a team commits to in a 2-week sprint. Measured by completed stories.

**Release Train** — All teams executing within a PI. Coordinated through Program Increment.

## Armies & Specialization

**Claude Code Army** — Deep, local, strategic. Handles architecture, large features, security audits. Response time: hours to days.

**GitHub Copilot Army** — Fast, GitHub-native, lightweight. Handles PR review, simple tasks (XS/S), board queries. Response time: minutes to hours.

**dlt-engineer** — Claude Code specialist agent for data pipelines. Handles ETL/ELT, incremental loading, schema evolution, source connector development, and destination wiring. Part of the Claude Code army.

**Copilot Coding Agent** — GitHub Copilot automation that takes `copilot-task` labeled issues and auto-implements them.

**Copilot Review** — GitHub Copilot that provides first-pass PR review on all PRs.

**Board Manager Extension** — Azure-deployable Copilot Chat extension for querying GitHub Projects board via `@board-manager`.

## Data & Pipelines

**dlt** — "data load tool." Lightweight Python framework for ETL/ELT: extraction, incremental loading, schema inference, destination wiring.

**ETL** — Extract, Transform, Load. Data pipeline pattern: pull from source, transform, push to destination.

**ELT** — Extract, Load, Transform. Modern variation: pull from source, push to data warehouse, transform in place.

**Incremental Loading** — Loading only new/changed data since last run. Opposed to full reload. More efficient, lower latency.

**Schema Evolution** — Handling changes to data structure over time. Adding columns, changing types, etc.

**Source Connector** — dlt abstraction for extracting from an external system (API, file, database).

**Destination** — Where data lands: DuckDB, BigQuery, Snowflake, Postgres, Parquet files, etc.

## Architecture & Enterprise

**Architecture Decision Record (ADR)** — Document explaining a significant architecture decision, its alternatives, and rationale. Written as MADR v4.0 format.

**Capability Map** — Business capability model. Hierarchical decomposition of "what the business does" into abstract capabilities.

**Wardley Map** — Strategic map showing: user needs, value chain, component evolution (genesis → custom → product → commodity), organizational doctrine.

**TOGAF** — The Open Group Architecture Framework. Enterprise architecture methodology with ADM (Architecture Development Method).

**Enterprise Architecture** — Holistic approach to designing organizations, information systems, and technology strategy across multiple PIs.

**Zero Trust Architecture** — Security model: never trust, always verify. Every access request is authenticated and authorized.

## Development & CI/CD

**Branch** — Named commit history. Feature branches isolate work; main is production-ready.

**Merge** — Integrating changes from one branch to another.

**Rebase** — Reorganizing commits on top of another branch. Cleaner history than merge.

**CI/CD** — Continuous Integration / Continuous Deployment. Automated pipeline: test on push, deploy on merge.

**CI** — Continuous Integration. Automated build/test on every push (the "CI" half of CI/CD).

**Workflow** — GitHub Actions workflow. Automation triggered on events (push, PR, schedule).

**Auto-merge** — Automatically merge PR when all conditions met (tests passing, reviews approved, checks green).

**Pre-commit Hook** — Code that runs before commit. Used to lint, format, validate.

## Code & Technical

**Refactoring** — Restructuring code without changing behavior. Improves readability, testability, performance.

**Monolith** — Single large application. Opposed to microservices (decomposed into independent services).

**Microservices** — Architecture pattern: independent, loosely-coupled services with separate databases.

**Async/Await** — Programming pattern for handling asynchronous operations (network, I/O) without blocking.

**Type Safety** — Language feature ensuring type mismatches are caught at compile time, not runtime.

**Idiomatic** — Following language conventions and best practices. E.g., "idiomatic Python" means Pythonic code.

**Performance Bottleneck** — Code or infrastructure point that limits system throughput or latency.

**Observable** — System that emits metrics, logs, traces. Enables root cause analysis and alerting.

## Messaging & Eventing

**NATS** — "Neural Autonomic Transport System." A lightweight message bus: services publish to named *subjects* and subscribers receive them instantly. The fleet's inter-service pub/sub backbone.

**JetStream** — NATS' persistence layer (a product name, not an acronym). Durably stores messages on streams so offline consumers can catch up after reconnecting.

**HMAC** — Hash-based Message Authentication Code. A shared-secret signature proving a payload is authentic and untampered — e.g. GitHub signs webhooks with the `X-Hub-Signature-256` header.

**CloudEvents** — A CNCF specification (not an acronym) defining a standard envelope format for events carried on the bus.

**Webhook** — An HTTP callback: a service POSTs a payload to a URL you control the instant an event fires (true push, vs polling).

## Networking & Web

**API** — Application Programming Interface. A defined contract for one program to call another.

**PAT** — Personal Access Token. A scoped credential for authenticating to GitHub's API/git over HTTPS. Prefer fine-grained, single-repo PATs over classic `repo`-scope tokens.

**HTTP / HTTPS** — HyperText Transfer Protocol (Secure). The request/response protocol of the web; HTTPS adds TLS encryption.

**SSH** — Secure Shell. Encrypted protocol for remote access and authenticated git push/pull via key pairs.

**URL** — Uniform Resource Locator. The address of a resource (e.g. a repository or an endpoint).

**CRLF / LF** — Carriage Return + Line Feed (`\r\n`, Windows) vs Line Feed (`\n`, Unix). Mismatched line endings produce phantom diffs across platforms.

**CDN** — Content Delivery Network. Edge-cached distribution (e.g. `raw.githubusercontent.com`) — a reason freshly-pushed files can briefly 404.

## Docker & Runtime

**WSL2** — Windows Subsystem for Linux v2. The lightweight Linux VM that Docker Desktop runs containers in on Windows.

**I/O** — Input/Output. Disk or network read/write activity; "I/O wait" is time a process spends blocked on it.

**OOM** — Out Of Memory. When a process or container exceeds its memory limit and is killed by the kernel's OOM-killer.

**WAL** — Write-Ahead Log. A durability technique (ArcadeDB, Postgres) where changes are logged before being applied, enabling crash recovery.

**GC / G1GC** — Garbage Collection / Garbage-First GC. Automatic memory reclamation in the JVM; G1GC targets low, predictable pause times.

**JVM** — Java Virtual Machine. The runtime that executes Java applications such as ArcadeDB.

**JAVA_OPTS** — Environment variable carrying JVM flags, e.g. `-Xms`/`-Xmx` (initial/max heap). Note: the ArcadeDB image's heap knob is `ARCADEDB_OPTS_MEMORY`, not `JAVA_OPTS`.

**HA** — High Availability. Architecture that survives node failure (e.g. primary + standby replication with automatic failover).

**SLA** — Service Level Agreement. A committed reliability/availability target, e.g. 99.9% uptime.

## Platform & Stack

**MCP** — Model Context Protocol. Open protocol letting AI agents call external tools and data sources through a uniform interface (the fleet exposes several MCP servers).

**BFF** — Backend For Frontend. A server tier dedicated to one frontend; AgentArmy's Next.js BFF at `/api/copilotkit` owns session-cookie → JWT injection (ARC-ADR-002).

**ACA / ACI** — Azure Container Apps / Azure Container Instances. Managed container hosts — ACA for rolling app/function deploys, ACI for single stateful containers (e.g. the ArcadeDB test instance).

**DBOS** — DataBase-Oriented Operating System. A Python durable-execution library (used by backend-core) that stores workflow state in Postgres.

**RDF** — Resource Description Framework. W3C graph data model of subject–predicate–object triples; the ontology / knowledge-graph substrate.

**SHACL** — Shapes Constraint Language. W3C language for validating RDF graphs against shape constraints (the "ontology sieve").

**SPARQL** — SPARQL Protocol And RDF Query Language (a recursive acronym). The query language for RDF graphs, served by Fuseki.

## Acronym Index (A–Z)

Quick-reference expansions for acronyms used across the docs. Run `node tools/acronyms.mjs` to find acronyms that appear in the docs but are missing here.

**A2A** — Agent-to-Agent (inter-agent communication). · **ABAC** — Attribute-Based Access Control. · **ABB** — Architecture Building Block (TOGAF). · **ACID** — Atomicity, Consistency, Isolation, Durability (DB transactions). · **ACL** — Access Control List. · **ACR** — Azure Container Registry. · **AD** — Active Directory. · **ADBC** — Arrow Database Connectivity. · **ADM** — Architecture Development Method (TOGAF). · **ADO** — Azure DevOps. · **AI** — Artificial Intelligence. · **AKS** — Azure Kubernetes Service. · **AKV** — Azure Key Vault. · **ANSI** — American National Standards Institute. · **AOT** — Ahead-Of-Time (compilation). · **AQL** — ArcadeDB Query Language. · **ARIA** — Accessible Rich Internet Applications (web a11y). · **ARM** — Azure Resource Manager. · **ASP** — Active Server Pages (ASP.NET). · **AWS** — Amazon Web Services.

**BA** — Business Architecture / Business Analyst (TOGAF Phase B). · **BFO** — Basic Formal Ontology. · **BI** — Business Intelligence. · **BIZBOK** — Business Architecture Body of Knowledge. · **BK** — Business Key (Data Vault). · **BPEL** — Business Process Execution Language. · **BPMN** — Business Process Model and Notation. · **BQ** — BigQuery. · **BSL** — Business Source License. · **BV** — Business Vault (Data Vault). · **BYO** — Bring Your Own.

**CACAO** — Collaborative Automated Course of Action Operations (OASIS). · **CCO** — Common Core Ontologies. · **CCPA** — California Consumer Privacy Act. · **CDC** — Change Data Capture. · **CDK** — Cloud Development Kit. · **CDM** — Canonical Data Model. · **CF** — Cloudflare. · **CL** — Common Logic (ontology). · **CLI** — Command-Line Interface. · **CLR** — Common Language Runtime (.NET). · **CMMC** — Cybersecurity Maturity Model Certification. · **CMMI** — Capability Maturity Model Integration. · **CNAME** — Canonical Name (DNS record). · **CNCF** — Cloud Native Computing Foundation. · **CORS** — Cross-Origin Resource Sharing. · **CPRA** — California Privacy Rights Act. · **CPU** — Central Processing Unit. · **CQ** — Competency Question (ontology). · **CRDT** — Conflict-free Replicated Data Type. · **CRM** — Customer Relationship Management. · **CRUD** — Create, Read, Update, Delete. · **CSF** — Cybersecurity Framework (NIST CSF). · **CSS** — Cascading Style Sheets. · **CSV** — Comma-Separated Values.

**DAG** — Directed Acyclic Graph. · **DAMA** — Data Management Association (DMBOK). · **Dapr / DAPR** — Distributed Application Runtime. · **DB** — Database. · **DDL** — Data Definition Language. · **DI** — Dependency Injection. · **DID** — Decentralized Identifier. · **DL** — Description Logic (ontology). · **DLQ** — Dead-Letter Queue. · **DMBOK** — Data Management Body of Knowledge. · **DML** — Data Manipulation Language. · **DMN** — Decision Model and Notation. · **DNS** — Domain Name System. · **DOLCE** — Descriptive Ontology for Linguistic and Cognitive Engineering. · **DOM** — Document Object Model. · **DORA** — DevOps Research and Assessment (metrics). · **DR** — Disaster Recovery. · **DSL** — Domain-Specific Language. · **DSN** — Data Source Name. · **DSRP** — Distinctions, Systems, Relationships, Perspectives. · **DSS** — Data Security Standard (as in PCI DSS). · **DTCG** — Design Tokens Community Group (W3C). · **DV** — Data Vault. · **DW** — Data Warehouse. · **DX** — Developer Experience.

**E2E** — End-to-End (testing). · **EA** — Enterprise Architecture. · **ECR** — Elastic Container Registry (AWS). · **ECS** — Elastic Container Service (AWS). · **EDA** — Event-Driven Architecture. · **EDGAR** — Electronic Data Gathering, Analysis, and Retrieval (SEC). · **EDW** — Enterprise Data Warehouse. · **EHR** — Electronic Health Record. · **EKS** — Elastic Kubernetes Service (AWS). · **ELK** — Elasticsearch, Logstash, Kibana. · **ER** — Entity-Relationship (modeling). · **ESB** — Enterprise Service Bus.

**FE** — Frontend. · **FEEL** — Friendly Enough Expression Language (DMN). · **FHIR** — Fast Healthcare Interoperability Resources. · **FIBO** — Financial Industry Business Ontology. · **FISMA** — Federal Information Security Management Act. · **FK** — Foreign Key. · **FOAF** — Friend Of A Friend (RDF vocabulary). · **FOIS** — Formal Ontology in Information Systems. · **FPS** — Frames Per Second. · **FTE** — Full-Time Equivalent.

**GB** — Gigabyte. · **GCP** — Google Cloud Platform. · **GCS** — Google Cloud Storage. · **GDPR** — General Data Protection Regulation. · **GDS** — Graph Data Science (Neo4j). · **GFO** — General Formal Ontology. · **GH** — GitHub. · **GHCR** — GitHub Container Registry. · **GIN** — Generalized Inverted Index (Postgres). · **GKE** — Google Kubernetes Engine. · **GNU** — GNU's Not Unix (recursive; the free-software project behind the GPL/LGPL licenses). · **GPT** — Generative Pre-trained Transformer. · **GPU** — Graphics Processing Unit. · **GUI** — Graphical User Interface.

**HIPAA** — Health Insurance Portability and Accountability Act. · **HITL** — Human-In-The-Loop. · **HK** — Hash Key (Data Vault). · **HLC** — Hybrid Logical Clock. · **HMR** — Hot Module Replacement. · **HS256** — HMAC-SHA256 (JWT signing algorithm). · **HSM** — Hardware Security Module. · **HTML** — HyperText Markup Language.

**IAM** — Identity and Access Management. · **IAO** — Information Artifact Ontology. · **IBM** — International Business Machines. · **ID** — Identifier. · **IDE** — Integrated Development Environment. · **IDOR** — Insecure Direct Object Reference. · **IDP** — Internal Developer Platform (also Identity Provider). · **IEC** — International Electrotechnical Commission. · **IIS** — Internet Information Services. · **IP** — Internet Protocol. · **IRI** — Internationalized Resource Identifier. · **ISBN** — International Standard Book Number. · **ISO** — International Organization for Standardization. · **ITGC** — IT General Controls.

**JIT** — Just-In-Time. · **JS** — JavaScript. · **JSON** — JavaScript Object Notation. · **JSONB** — JSON Binary (Postgres type). · **JUEL** — Java Unified Expression Language. · **JWKS** — JSON Web Key Set. · **JWS** — JSON Web Signature. · **JWT** — JSON Web Token.

**KB** — Knowledge Base (also Kilobyte). · **KEDA** — Kubernetes Event-Driven Autoscaling. · **KG** — Knowledge Graph. · **KMS** — Key Management Service. · **KR** — Key Result (OKR). · **KV** — Key Vault (Azure), or key-value.

**LB** — Load Balancer. · **LCP** — Largest Contentful Paint (web vital). · **LD** — Linked Data. · **LGPL** — GNU Lesser General Public License. · **LINQ** — Language-Integrated Query (.NET). · **LLM** — Large Language Model. · **LOC** — Lines Of Code. · **LPG** — Labeled Property Graph. · **LRU** — Least Recently Used (cache eviction). · **LSP** — Language Server Protocol.

**M365** — Microsoft 365. · **MADR** — Markdown Architecture Decision Records (format). · **MAS** — Multi-Agent System. · **MB** — Megabyte. · **MC** — middle-core (abbrev.). · **MDM** — Master Data Management. · **MIME** — Multipurpose Internet Mail Extensions. · **MIT** — MIT License (Massachusetts Institute of Technology). · **ML** — Machine Learning. · **MPL** — Mozilla Public License. · **MQTT** — Message Queuing Telemetry Transport. · **MSAL** — Microsoft Authentication Library. · **MTTR** — Mean Time To Recovery. · **MUI** — Material UI. · **MVP** — Minimum Viable Product.

**NDJSON** — Newline-Delimited JSON. · **NER** — Named Entity Recognition. · **.NET** — Microsoft's cross-platform application framework. · **NIST** — National Institute of Standards and Technology. · **NLP** — Natural Language Processing. · **NPU** — Neural Processing Unit. · **NTLM** — a legacy Windows challenge-response authentication protocol. · **NTP** — Network Time Protocol.

**OAEI** — Ontology Alignment Evaluation Initiative. · **OASIS** — Organization for the Advancement of Structured Information Standards. · **OBO** — Open Biological and Biomedical Ontologies (Foundry). · **OBT** — One Big Table (data modeling). · **OCI** — Open Container Initiative. · **OIDC** — OpenID Connect. · **OKR** — Objectives and Key Results. · **OLTP** — Online Transaction Processing. · **OMG** — Object Management Group. · **OPA** — Open Policy Agent. · **ORAS** — OCI Registry As Storage. · **ORM** — Object-Relational Mapping. · **OS** — Operating System. · **OSI** — Open Source Initiative. · **OSS** — Open-Source Software. · **OTLP** — OpenTelemetry Protocol. · **OTP** — One-Time Password. · **OWL** — Web Ontology Language. · **OWM** — Online Wardley Map (syntax for create.wardleymaps.ai).

**PATO** — Phenotype And Trait Ontology. · **PCI** — Payment Card Industry (PCI DSS). · **PEP** — Python Enhancement Proposal. · **PG** — Postgres (abbrev.). · **PHP** — PHP: Hypertext Preprocessor. · **PID** — Process Identifier. · **PII** — Personally Identifiable Information. · **PIT** — Point-In-Time (Data Vault table). · **PK** — Primary Key. · **POCO** — Plain Old CLR Object. · **PROV** — Provenance (W3C PROV ontology). · **PS** — PowerShell. · **PTP** — Precision Time Protocol. · **PWA** — Progressive Web App.

**QA** — Quality Assurance. · **R2RML** — RDB-to-RDF Mapping Language. · **RAG** — Retrieval-Augmented Generation. · **RAM** — Random-Access Memory. · **RBAC** — Role-Based Access Control. · **RCE** — Remote Code Execution. · **RDB** — Relational Database. · **RDBMS** — Relational Database Management System. · **RDFS** — RDF Schema. · **RDS** — Relational Database Service (AWS). · **REQM** — Requirements Management. · **REST** — Representational State Transfer. · **RFC** — Request For Comments. · **RFP** — Request For Proposal. · **RG** — Resource Group (Azure). · **RI** — Reserved Instance (cloud). · **RL** — Reinforcement Learning. · **RLS** — Row-Level Security. · **RMF** — Risk Management Framework (NIST). · **RML** — RDF Mapping Language. · **RN** — React Native. · **RO** — Relations Ontology. · **ROI** — Return On Investment. · **RPC** — Remote Procedure Call. · **RSC** — React Server Components. · **RT** — Release Train. · **RTOS** — Real-Time Operating System.

**SAFe / SAFE** — Scaled Agile Framework. · **SAML** — Security Assertion Markup Language. · **SAS** — Shared Access Signature (Azure). · **SBB** — Solution Building Block (TOGAF). · **SBOM** — Software Bill of Materials. · **SCD** — Slowly Changing Dimension. · **SCIM** — System for Cross-domain Identity Management. · **SCP** — Service Control Policy (AWS). · **SDK** — Software Development Kit. · **SEC** — Securities and Exchange Commission (US). · **SEO** — Search Engine Optimization. · **SHA** — Secure Hash Algorithm. · **SKOS** — Simple Knowledge Organization System. · **SLI** — Service Level Indicator. · **SLO** — Service Level Objective. · **SMS** — Short Message Service. · **SMT** — Satisfiability Modulo Theories. · **SNS** — Simple Notification Service (AWS). · **SOAP** — Simple Object Access Protocol. · **SOAR** — Security Orchestration, Automation, and Response. · **SOC** — System and Organization Controls (SOC 2). · **SOPS** — Secrets OPerationS (Mozilla SOPS). · **SOX** — Sarbanes-Oxley Act. · **SP** — Special Publication (e.g. NIST SP 800-53). · **SPA** — Single-Page Application. · **SPOF** — Single Point Of Failure. · **SQL** — Structured Query Language. · **SQS** — Simple Queue Service (AWS). · **SRE** — Site Reliability Engineering. · **SSE** — Server-Sent Events. · **SSG** — Static Site Generation. · **SSO** — Single Sign-On. · **SSRF** — Server-Side Request Forgery. · **STIX** — Structured Threat Information eXpression. · **SVG** — Scalable Vector Graphics. · **SWA** — Azure Static Web Apps. · **SWRL** — Semantic Web Rule Language.

**TB** — Terabyte. · **TBT** — Total Blocking Time (web vital). · **TDB2** — Apache Jena TDB2 (triple store). · **TLP** — Traffic Light Protocol. · **TLS** — Transport Layer Security. · **TOML** — Tom's Obvious Minimal Language. · **TOTP** — Time-based One-Time Password. · **TS** — TypeScript. · **TSDB** — Time-Series Database. · **TTI** — Time To Interactive (web vital). · **TTL** — Time To Live (also Turtle, the `.ttl` RDF format). · **TTM** — Time To Market. · **TUI** — Terminal User Interface. · **TZ** — Time Zone.

**UAT** — User Acceptance Testing. · **UC** — Use Case. · **UFO** — Unified Foundational Ontology. · **UI** — User Interface. · **ULID** — Universally-unique Lexicographically-sortable Identifier. · **URI** — Uniform Resource Identifier. · **URN** — Uniform Resource Name. · **UTC** — Coordinated Universal Time. · **UTF** — Unicode Transformation Format. · **UUID** — Universally Unique Identifier. · **UX** — User Experience.

**VHDX** — Virtual Hard Disk v2 (Hyper-V). · **VM** — Virtual Machine. · **VPC** — Virtual Private Cloud. · **W3C** — World Wide Web Consortium. · **WSD** — Word-Sense Disambiguation (resolving which sense of an ambiguous term is meant). · **WAF** — Web Application Firewall. · **WCAG** — Web Content Accessibility Guidelines. · **WCF** — Windows Communication Foundation. · **WIF** — Workload Identity Federation. · **WPF** — Windows Presentation Foundation. · **WSJF** — Weighted Shortest Job First (SAFe prioritization). · **WSL** — Windows Subsystem for Linux. · **WSUS** — Windows Server Update Services. · **XACML** — eXtensible Access Control Markup Language. · **XML** — eXtensible Markup Language. · **XSD** — XML Schema Definition. · **XXE** — XML External Entity (attack). · **YAGNI** — You Aren't Gonna Need It. · **YAML** — YAML Ain't Markup Language. · **ZTA** — Zero Trust Architecture.

> **Project identifiers (not acronyms):** `MCR-F*` (middle-core requirement), `GPM-E*` (an epic group), `PIN-F*` (the pinning subsystem), `UDA` (an RT6 contract), `IKW-GraphEngine` (a component), `CIDX-*` (a CI check). These are internal IDs — see [contracts.md](contracts.md) and the release-train docs rather than expecting an acronym expansion.

---

## System Ontology — Components, Capabilities & Surfaces

The platform self-model (`ontology/platform-self-model/`) distinguishes a **capability** (the verb — a functional disposition) from a **surface** (the UX space you interface it through). Both project from one ontology.

**Capability** — A functional disposition the system provides, independent of how it's implemented (T-Box `Capability`). The *verb*.

**Surface** — A user-experience space (product/ops UI) through which one or more capabilities are interfaced (T-Box `Surface`). The *noun/place*. Encoded as `Surface ──capability-exposure──▶ Capability`.

**forge** (`agentarmy-forge`, ARC-ADR-029) — The **capability** that materializes an ontology into the **Object Model** projection (typed source: C#/TS/Python/Rust). The Materialize→Object-Model arm of Crucible — *not* a synonym for Crucible. In the self-model: `cap-forge` realized-by `ctr-forge`/`repo-forge`.

**Crucible** — The flagship **surface** (untool product ontology, `Crucible.html`): the *corpus → ontology* experience (`Corpus → Ground → Derive → Materialize`). You interface the forge capability *through* Crucible. In the self-model: `srf-crucible ──exposes──▶ cap-forge`.

**UDA (Universal Data Adapter)** — The runtime **read-seam** (`backend-core/rust-api-v2/src/uda.rs`) that hydrates the generated Object Model from the cost/latency-optimal backend (ArcadeDB, BigQuery, Postgres, DBOS, ontology sieve) per a data object's access pattern. forge *emits* the typed objects; UDA *serves* them.

**Object Model** — One of three lockstep projections of the materialized ontology (Knowledge Graph · Vector DB · Object Model). The typed objects the armies call directly.

---

## Related Docs

- **[Armies Overview](armies-overview.md)** — Three armies model
- **[GitHub Projects](github-projects.md)** — Board field reference
- **[SAFe Framework](safe.md)** — PI planning details
- **[FAQ](faq.md)** — Answers to common questions
