# Architecture Decision Document — eGov Cameroun MCP

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER (Browser)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼────────────────────────────────────┐
│              FRONTEND — Next.js (Vercel)                     │
│  • Chat UI (React)                                           │
│  • MCP Client (calls /sse for tool discovery)                │
│  • Calls /chat for conversational AI                         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS / SSE
┌────────────────────────▼────────────────────────────────────┐
│          MCP SERVER — FastAPI + Python (Render)              │
│                                                              │
│  /sse      ← MCP SSE transport endpoint                      │
│  /messages ← MCP message handler                            │
│  /chat     ← Chat orchestration (Claude + MCP tools)         │
│  /tools    ← Tool metadata listing                           │
│  /health   ← Health check                                    │
│                                                              │
│  Tools:                                                      │
│  ├── verify_cnps_matricule  → cons.cnps.cm (HTTP)            │
│  ├── get_statistical_data   → api.worldbank.org (HTTP)       │
│  ├── calculate_vat          → Internal computation           │
│  ├── calculate_cnps_contr.  → Internal computation           │
│  └── get_tax_deadlines      → Internal computation           │
└──────┬──────────────────────────┬───────────────────────────┘
       │                          │
┌──────▼──────────┐     ┌────────▼──────────┐
│  Anthropic API  │     │  External APIs     │
│  (Claude Sonnet)│     │  • CNPS Cameroun   │
│                 │     │  • World Bank API  │
└─────────────────┘     └───────────────────┘
```

## Monorepo vs Multi-Repository

**Decision: Monorepo**

**Why:** This is a 2-service system (frontend + backend) owned by one team. A monorepo
means one `git clone`, one CI pipeline, atomic commits across services, and shared
configuration (`.gitignore`, `.github/workflows`, `docker-compose.yml`). The complexity
overhead of managing inter-repo dependencies (versioning, API contracts) is not justified
at this scale.

**Advantages:**
- Single PR covers a frontend change + the backend API change it requires
- One CI run validates the full stack
- Easier local dev: `docker-compose up` starts everything
- Shared tooling (linting, formatting, secrets management)

**Disadvantages:**
- If the team grows, a large Python team and large JS team could conflict on CI/CD config
- Build times grow as both codebases scale
- Independent deploy cadences are harder (though still possible with path-based triggers)

**When to switch:** When two separate teams own the services and deploy independently at
different cadences — then the coordination overhead of a monorepo exceeds the benefits.

## MCP Tool Design Rationale

Each tool was designed around a specific user intent derived from the assessment examples:

| Tool | Intent | Why this design |
|------|--------|-----------------|
| `verify_cnps_matricule` | "Vérifie ce matricule CNPS" | Real HTTP call to CNPS public portal — proves network execution to reviewers |
| `get_statistical_data` | Economic context questions | World Bank API is public, documented, reliable. Gives real government data |
| `calculate_vat` | "Prépare ma déclaration TVA" | Implements CGI Art. 128 (19.25%) — real computation, inputs → outputs |
| `calculate_cnps_contributions` | "Cotisations sociales de mes employés" | Implements Code du Travail 1992 rates — parameterized, not mocked |
| `get_tax_deadlines` | "Vérifie les échéances fiscales" | Dynamic computation based on month/year — different inputs give different results |

Tools 1 and 2 produce real network traffic. Tools 3, 4, 5 implement real Cameroonian
legal rules — results are dynamically computed from user inputs, not hardcoded.

## Deployment Topology

- **Backend → Render (free tier)**: FastAPI runs well on Render's free web service.
  Render provides persistent processes (unlike serverless), necessary for SSE connections.
  Auto-deploy from `main` branch via GitHub integration.

- **Frontend → Vercel (free tier)**: Next.js is first-class on Vercel. Zero-config deploy,
  global CDN, preview URLs for every PR. The `output: standalone` in next.config.ts ensures
  the Docker build also works for self-hosting.

- **Environment variables**: Managed via Render dashboard (backend) and Vercel dashboard
  (frontend). Never committed to git. `.env.example` documents required variables.

## Data Flow

```
1. User types: "Calcule ma TVA de mars 2026 pour 5M FCFA HT"
2. Frontend POST /chat  {message, history}
3. Backend sends messages to Claude API with all 5 tool definitions
4. Claude returns tool_use: calculate_vat({revenue_ht: 5000000, period: "2026-03"})
5. Backend executes MCP tool → returns {tva: 962500, deadline: "2026-04-15", ...}
6. Backend sends tool_result back to Claude
7. Claude generates human response: "Votre TVA de mars 2026 est de 962 500 FCFA..."
8. Backend returns {message, tool_calls: [{name, input, output}]}
9. Frontend renders message + collapsible tool execution panel
```

## Scalability Plan: 100 → 100,000 Users

### 100 users (current)
Single Render instance + Vercel. No database needed. Total cost: $0/month (free tiers).

### 1,000 users
- Add Redis for conversation history (avoid re-sending full history on every request)
- Add request-level caching for stable responses (tax deadlines, World Bank data — TTL 1h)
- Render paid tier for no sleep + higher memory

### 10,000 users
- **Horizontal scaling**: Render scales to multiple instances. FastAPI + uvicorn are
  stateless by design — scaling is trivial.
- **Background jobs**: Celery + Redis for long-running tool executions (e.g. bulk CNPS
  verification). API returns a job_id, frontend polls status.
- **Database**: PostgreSQL for conversation persistence, audit logs, user accounts.
- **Rate limiting**: Per-user token budget to control Anthropic API costs.

### 100,000 users
- **CDN + Edge caching**: Cache Vercel responses at edge. Static tool definitions cached.
- **Observability**: OpenTelemetry → Grafana/Datadog. Each MCP tool call is a traced span.
  Critical for debugging Claude tool loops.
- **LLM cost control**: Route simple queries (tax deadlines) to a smaller/cheaper model
  (Haiku). Reserve Sonnet for complex multi-tool orchestration.
- **CNPS/Gov API rate limiting**: Government APIs have unknown rate limits. Add a local
  cache (Redis, TTL 24h) for CNPS matricule verifications.
- **Cost estimate at 100k users**: ~$5k-$15k/month (dominated by Anthropic API costs).
  Mitigation: prompt caching, tool result caching, model tiering.
