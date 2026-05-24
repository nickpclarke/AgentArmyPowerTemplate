# Cloud Serving Landscape

When you fork AgentArmy and build a spoke (UI layer, API layer, worker, infra layer), the first question is: **which cloud, which database, which LLM?** This guide makes that choice fast with opinionated defaults, hard limits, and a routing table for the right agent.

---

## TL;DR — Opinionated Starter Stacks

Pick one and go. You can always migrate later; the LLM abstraction principle (below) keeps your options open.

| Stack | Components | Best for |
|---|---|---|
| **Zero-ops** | GitHub Pages + Vercel Functions + Neon Postgres + Claude API | Solo dev, zero infra management, pay-as-you-go |
| **GCP** | Cloud Run + Cloud SQL + Vertex AI (Gemini) | Google-ecosystem teams, per-request billing, strong IAM |
| **Azure** | Container Apps + Azure SQL + Azure OpenAI | Enterprise M365/Azure shops, existing EA agreements |
| **AWS** | App Runner/Fargate + RDS Aurora + AWS Bedrock | AWS-native teams, compliance-sensitive workloads |
| **GitHub-native** | GitHub Pages + GitHub Actions compute | Fully GitHub, no external accounts, documentation-first |

**Default recommendation for new spokes:** Start with the Zero-ops stack. Vercel + Neon costs nothing at small scale, deploys in minutes, and you can move compute to Cloud Run or ECS later with a container swap.

---

## GitHub Pages: Capabilities and Limits

GitHub Pages is already wired up in this template (MkDocs auto-deployed via `deploy-docs.yml`). Here is what it can and cannot do:

### What it does well
- Serves static files: HTML, CSS, JS, images, JSON, PDFs
- Supports Jekyll natively or any SSG (Hugo, Astro, MkDocs, Eleventy) via GitHub Actions
- Custom domains with automatic HTTPS via Let's Encrypt
- Free on public repos; included in GitHub plans for private repos
- Ideal for: documentation sites, project portals, OpenAPI spec browsers, marketing pages

### Hard limits
| Limit | Value |
|---|---|
| Repository size | 1 GB |
| Site size | 1 GB |
| Bandwidth | 100 GB/month (soft limit — GitHub may throttle, not block) |
| Build timeout | 10 minutes |
| Deploys per hour | 10 |

### What it cannot do
- **No server-side execution** — no Node.js, Python, PHP, or any runtime at request time
- **No API endpoints** — any dynamic behavior must come from an external service called via client-side JS
- **No server-side secrets** — anything in a Pages site is public; never embed API keys
- **No auth at the edge** — anyone can access any URL; use a separate identity provider + SPA auth
- **No databases** — all data access must go through a client-side API call to an external backend

**Rule of thumb:** If a request needs to read a database or call an LLM, it does not belong on GitHub Pages — it belongs in a Vercel Function, Cloud Run service, or similar compute layer.

---

## Decision Matrix: Static / Frontend Hosting

| Provider | Free tier | Custom domain | Build included | Server-side | Notes |
|---|---|---|---|---|---|
| **GitHub Pages** | Yes (public repos) | Yes (CNAME) | Via Actions | No | Best for docs and project portals |
| **Vercel** | Yes (Hobby) | Yes | Yes (Vercel CI) | Yes (Functions) | Best for full-stack Next.js/SvelteKit |
| **Netlify** | Yes (Starter) | Yes | Yes | Yes (Functions) | JAMstack, form handling, identity |
| **Azure SWA** | Yes (Free tier) | Yes | Yes | Yes (Azure Functions) | Best within existing Azure EA |
| **Cloudflare Pages** | Yes | Yes | Yes | Yes (Workers) | Global edge, Workers KV, R2 |

**When to choose Vercel over GitHub Pages for a spoke frontend:** any time the spoke needs server-side rendering, API routes, or LLM streaming — even if it's "mostly static."

---

## Decision Matrix: Compute / API Hosting

| Provider | Model | Cold start | Max duration | Best for |
|---|---|---|---|---|
| **Vercel Functions** | Serverless + Edge | ~50ms (Edge), ~300ms (Node) | 300s (Pro), 30s (Edge) | Full-stack apps co-located with frontend |
| **Google Cloud Run** | Container, autoscale-to-zero | ~500ms | 3600s | Any container, long-running tasks, GCP IAM |
| **Azure Container Apps** | Container, KEDA autoscale | ~1s | Unlimited | Azure ecosystem, Dapr sidecar, KEDA scaling |
| **AWS App Runner** | Container, managed | ~1s | Unlimited | AWS-native, simpler than Fargate |
| **AWS Fargate** | Container, task-based | ~30s | Unlimited | AWS-native, fine-grained task control |
| **Railway** | Container, always-on option | Minimal | Unlimited | Solo dev, zero-config Dockerfile deploys |
| **Fly.io** | Container, anycast | Minimal | Unlimited | Multi-region, persistent volumes, ops-aware teams |

**Recommendation:** Cloud Run is the most flexible managed option — any container, true scale-to-zero, per-request billing. Vercel Functions wins when the spoke is a Next.js / SvelteKit app. Railway and Fly.io are great for teams that want Git-push deploys without a full cloud account setup.

---

## Decision Matrix: Managed Databases

| Service | Engine | Free tier | Serverless | Best for |
|---|---|---|---|---|
| **Supabase** | Postgres | Yes (500 MB) | Yes (pause on inactivity) | Full-stack: Auth + Storage + Realtime + Postgres in one |
| **Neon** | Postgres | Yes (0.5 CU) | Yes | Vercel + Neon canonical pair; branch-per-PR databases |
| **PlanetScale** | MySQL (Vitess) | No (free tier paused) | Yes | High-scale MySQL, schema branching, no foreign keys |
| **Firestore** | NoSQL document | Yes (Spark plan) | Yes | GCP-native, mobile/serverless, event-driven |
| **DynamoDB** | NoSQL KV + doc | Free tier | On-demand billing | AWS-native, massive scale, single-digit ms latency |
| **Upstash Redis** | Redis | Yes (10k cmds/day) | Yes | Cache, sessions, rate limiting alongside a primary DB |
| **Turso (libSQL)** | SQLite (distributed) | Yes | Yes | Edge databases, extremely low-latency reads globally |

**Recommendation for most spokes:** Neon (with Vercel) or Supabase (standalone). Both are Postgres, serverless, and have generous free tiers. Add Upstash Redis for session storage or rate limiting if needed.

---

## Decision Matrix: LLM Providers

AgentArmy uses Claude for orchestration. Spoke applications may use any provider — abstract the client so you can swap without code changes.

| Provider | Models | Pricing style | Strengths | Best for |
|---|---|---|---|---|
| **Anthropic (Claude API)** | Haiku, Sonnet, Opus | Per token (input/output) | Reasoning, code, long context | Default for AgentArmy-built agents |
| **OpenAI** | GPT-4o, GPT-4o-mini | Per token | Ecosystem breadth, vision, function calling | Existing OpenAI integrations |
| **Vertex AI (GCP)** | Gemini, Claude via Vertex | Per token | Audit logging, VPC Service Controls, GCP IAM | GCP-native compliance workloads |
| **AWS Bedrock** | Claude, Llama, Titan | Per token | PrivateLink, SCPs, AWS compliance | AWS-native, HIPAA/FedRAMP workloads |
| **Ollama (self-hosted)** | Llama, Mistral, Qwen, Phi | Compute cost only | Air-gapped, cost ceiling, no data egress | Privacy-sensitive, on-prem, cost-capped |
| **Groq / Together.ai** | Llama, Mixtral, Gemma | Per token (low cost) | Very high throughput, low latency | Budget inference, high-volume PoCs |

**Cost guidance:** Haiku-class models (Claude Haiku, GPT-4o-mini) are 10–20× cheaper than flagship models and handle most classification, extraction, and light reasoning tasks. Reserve Sonnet/Opus/GPT-4o for tasks that measurably need them.

---

## The LLM Abstraction Principle

The AgentArmy roadmap (Play 5) says: **consume, abstract provider, avoid lock-in, stay multi-vendor.**

In practice this means:

```python
# BAD — hardcoded provider
from anthropic import Anthropic
client = Anthropic()

# GOOD — parameterized via env var + abstraction layer
import litellm  # or Vercel AI SDK, LangChain, custom wrapper
response = litellm.completion(
    model=os.environ["LLM_MODEL"],  # e.g. "claude-3-5-sonnet-latest" or "gpt-4o"
    messages=[...]
)
```

Options for the abstraction layer:
- **Vercel AI SDK** (`ai` npm) — provider-agnostic, built for streaming, ideal for Vercel spokes
- **LiteLLM** (Python) — unified OpenAI-compatible API across 100+ providers
- **LangChain** — broader orchestration, more abstraction overhead
- **Custom env-var wrapper** — for simple spokes that call one model at a time

Set `LLM_PROVIDER` and `LLM_MODEL` as environment variables per spoke environment. The model changes in config, not code.

---

## Which Agent to Use

| Scenario | Agent |
|---|---|
| GCP infrastructure (Cloud Run, Cloud SQL, GKE, IAM, Vertex AI, Cloud Build) | `gcp-infra-engineer` |
| AWS infrastructure (Fargate, RDS, Bedrock, EKS, CDK/CloudFormation, IAM/SCP) | `aws-infra-engineer` |
| Azure infrastructure (Container Apps, Bicep, Entra ID, Azure OpenAI) | `azure-infra-engineer` |
| Vercel platform (Functions, Postgres/KV/Blob, edge middleware, monorepo, AI SDK) | `vercel-engineer` |
| Multi-cloud strategy, cloud provider selection, landing zone design | `cloud-architect` |
| LLM system design, RAG, multi-model orchestration, inference serving | `llm-architect` |
| Cloud cost governance, unit economics, RI/Savings Plan commitments | `finops-engineer` |
| IaC module design, Terraform state management, Terragrunt orchestration | `terraform-engineer` |

---

## Coming Soon (Backlog)

These features are tracked as GitHub Issues on the project board:

- **IaC starter templates** — Terraform modules for Cloud Run + Cloud SQL, Fargate + RDS, Container Apps
- **Spoke stack builder** — a CLI/Actions workflow that scaffolds a new spoke with provider-specific IaC and pipelines
- **CI/CD workflow templates** — reusable `deploy-gcp.yml`, `deploy-aws.yml`, `deploy-vercel.yml` for spoke repos
- **LLM provider abstraction layer** — shared wrapper library for RT2 Play 5
- **Cloud-native CI/CD research spike** — GCP Cloud Build/Deploy vs AWS CodePipeline vs GitHub Actions evaluation

## Azure Dev Container Lane

For Azure-first spoke development, use [Azure Container Apps Dev Deploy](azure-container-apps-dev.md). It pairs a trusted local PC or self-hosted runner with Azure Container Registry and Azure Container Apps Dev, while keeping production promotion as a separate environment-gated workflow.

For multi-cloud lifecycle routing, use [Lifecycle Promotion Management](lifecycle-promotion-management.md). It defines the local Docker gate and target-adapter pattern that can route a spoke to Azure Container Apps, GCP Cloud Run, Vertex AI Agent Engine, or future runtime targets.
