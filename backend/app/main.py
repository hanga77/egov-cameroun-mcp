import json
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mcp.server.sse import SseServerTransport

from app.config import settings
from app.auth import require_api_key
from app.models import ChatRequest, ChatResponse
from app.chat import process_chat
from app.mcp_server import mcp, list_tools

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

sse_transport = SseServerTransport("/messages")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("egov_mcp_server_starting", environment=settings.environment)
    yield
    logger.info("egov_mcp_server_stopping")


app = FastAPI(
    title="eGov Cameroun MCP Server",
    description="Serveur MCP pour les services gouvernementaux du Cameroun",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": "egov-cameroun-mcp", "version": "1.0.0"}


# ── MCP SSE endpoints ───────────────────────────────────────────────────────

@app.get("/sse", tags=["MCP"])
async def mcp_sse(request: Request):
    """MCP Server-Sent Events endpoint — MCP client connects here."""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp.run(streams[0], streams[1], mcp.create_initialization_options())


@app.post("/messages", tags=["MCP"])
async def mcp_messages(request: Request):
    """MCP message handler for the SSE transport."""
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)


# ── Tools metadata ──────────────────────────────────────────────────────────

@app.get("/tools", tags=["MCP"])
async def get_tools():
    """List all available MCP tools with their schemas."""
    tools = await list_tools()
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema,
            }
            for t in tools
        ]
    }


# ── Chat endpoint ────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    body: ChatRequest,
    _: str = Depends(require_api_key),
):
    """
    Reçoit un message en langage naturel, orchestre Claude + outils MCP,
    et retourne la réponse avec la liste des outils exécutés.
    """
    logger.info("chat_endpoint_called", message_len=len(body.message))
    result = await process_chat(body.message, body.history)
    return ChatResponse(**result)


# ── Global error handler ─────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Erreur interne du serveur."})
