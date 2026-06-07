# eGov Cameroun — AI-Native MCP Platform

An AI-native eGovernment platform for Cameroon built with MCP (Model Context Protocol).
Users interact with DGI and CNPS services through natural language in French or English.

## Architecture

```
React Frontend (MCP Client) → MCP Server (FastAPI) → Government APIs
                                     ↓
                              Claude Sonnet 4.6
```

Full details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)  
AI strategy: [docs/AI_STRATEGY.md](docs/AI_STRATEGY.md)

## MCP Tools

| Tool | Description | API |
|------|-------------|-----|
| `verify_cnps_matricule` | CNPS registration check | cons.cnps.cm |
| `get_statistical_data` | Economic indicators | api.worldbank.org |
| `calculate_vat` | TVA declaration (19.25%) | Internal |
| `calculate_cnps_contributions` | Social contributions | Internal |
| `get_tax_deadlines` | DGI/CNPS deadlines | Internal |

## Quick Start

```bash
# 1. Clone
git clone <repo-url> && cd egov-cameroun

# 2. Configure
cp backend/.env.example backend/.env
# Edit backend/.env — add ANTHROPIC_API_KEY

cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local

# 3. Run with Docker
docker-compose up --build
# → Frontend: http://localhost:3000
# → Backend:  http://localhost:8000
# → API docs: http://localhost:8000/docs
```

## Local Development (without Docker)

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Running Tests

```bash
cd backend
pytest -v
```

## Deployment

### Backend → Render
1. Create a new Web Service on render.com
2. Connect your GitHub repo
3. Set root directory: `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables: `ANTHROPIC_API_KEY`, `API_SECRET_KEY`, `ALLOWED_ORIGINS`

### Frontend → Vercel
1. Import repo on vercel.com
2. Set root directory: `frontend`
3. Add env vars: `NEXT_PUBLIC_API_URL` (your Render URL), `NEXT_PUBLIC_API_KEY`

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/docs` | GET | OpenAPI documentation |
| `/tools` | GET | List MCP tools |
| `/sse` | GET | MCP SSE transport |
| `/messages` | POST | MCP message handler |
| `/chat` | POST | Chat (requires X-API-Key header) |

## Assumptions & Tradeoffs

- **CNPS API**: The CNPS public portal does not publish a REST API spec. The tool calls
  the public verification form via HTTP. If the portal is down, the tool returns a graceful
  error — it never fabricates a result.
- **Tax calculations**: Rates are based on CGI 2026 and Code du Travail 1992. These change
  yearly — a production system would need an admin interface to update rates.
- **No auth/users**: No user accounts in v1. The API key secures the `/chat` endpoint.
  A production system would add JWT-based user auth.
- **Conversation history**: Stored client-side in React state. Lost on page refresh.
  Production: store in PostgreSQL with user sessions.

## Future Improvements

1. User authentication (JWT) + conversation persistence (PostgreSQL)
2. Document upload → auto-fill VAT declarations from accounting exports
3. WhatsApp Business integration (dominant messaging in Cameroon)
4. SMS deadline reminders via Orange Cameroun API
5. Model tiering: Haiku for simple lookups, Sonnet for tool orchestration
6. Cameroonian French fine-tuned model for reduced hallucination on local regulations

## AI Usage Disclosure

This project was built with Claude Code (claude-sonnet-4-6) assistance.

**AI-assisted:**
- Initial file scaffolding and boilerplate
- Pydantic model definitions
- Tailwind CSS class composition

**Manually written / verified:**
- All tax calculation logic (CGI rates, CNPS rates — cross-checked against official texts)
- MCP tool architecture design decisions
- CNPS API integration approach
- All architecture and AI strategy documents
- Test assertions and business logic validation
