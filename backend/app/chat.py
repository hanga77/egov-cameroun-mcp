import json
import structlog
import anthropic

from app.config import settings
from app.models import ChatMessage, ToolCall
from app.mcp_server import call_tool, list_tools

logger = structlog.get_logger()

SYSTEM_PROMPT = """Tu es un assistant IA pour les services gouvernementaux du Cameroun.
Tu aides les entreprises et les citoyens à :
- Vérifier des matricules CNPS
- Calculer leurs déclarations TVA
- Calculer leurs cotisations sociales CNPS
- Consulter les échéances fiscales DGI
- Obtenir des statistiques économiques sur le Cameroun

Tu réponds en français ou en anglais selon la langue de l'utilisateur.
Utilise les outils disponibles pour fournir des résultats précis et basés sur les données réelles.
Présente les montants en FCFA avec formatage lisible (ex: 1 500 000 FCFA).
Sois concis, précis et professionnel."""


async def process_chat(message: str, history: list[ChatMessage]) -> dict:
    """
    Orchestre un échange avec Claude en utilisant les outils MCP définis.
    Claude décide quels outils appeler, les appels sont exécutés sur le serveur MCP,
    les résultats sont renvoyés à Claude pour générer la réponse finale.
    """
    log = logger.bind(message_len=len(message))
    log.info("chat_request_received")

    if not settings.anthropic_api_key:
        return {
            "message": "Clé API Anthropic non configurée. Veuillez définir ANTHROPIC_API_KEY.",
            "tool_calls": [],
        }

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Build Anthropic tool definitions from MCP tool list
    mcp_tools = await list_tools()
    anthropic_tools = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.inputSchema,
        }
        for t in mcp_tools
    ]

    # Convert history to Anthropic message format
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": message})

    executed_tool_calls: list[ToolCall] = []
    max_iterations = 5  # prevent infinite loops

    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=anthropic_tools,
        )
        log.info("claude_response", stop_reason=response.stop_reason)

        if response.stop_reason != "tool_use":
            # Final text response
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")),
                "Désolé, je n'ai pas pu générer une réponse.",
            )
            log.info("chat_completed", tool_calls_count=len(executed_tool_calls))
            return {"message": final_text, "tool_calls": [tc.model_dump() for tc in executed_tool_calls]}

        # Execute all tool_use blocks via the MCP server
        tool_results = []
        messages.append({"role": "assistant", "content": response.content})

        for block in response.content:
            if block.type != "tool_use":
                continue

            log.info("executing_mcp_tool", tool=block.name, tool_input=block.input)
            mcp_result = await call_tool(block.name, block.input)
            result_text = mcp_result[0].text if mcp_result else json.dumps({"error": "no result"})

            executed_tool_calls.append(
                ToolCall(tool_name=block.name, input=block.input, output=result_text)
            )
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_text,
            })

        messages.append({"role": "user", "content": tool_results})

    # Fallback if max iterations hit
    return {
        "message": "La requête a nécessité trop d'itérations. Veuillez reformuler.",
        "tool_calls": [tc.model_dump() for tc in executed_tool_calls],
    }
