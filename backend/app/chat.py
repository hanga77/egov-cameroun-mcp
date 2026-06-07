import json
import structlog
from openai import OpenAI

from app.config import settings
from app.models import ChatMessage, ToolCall
from app.mcp_server import call_tool, list_tools

logger = structlog.get_logger()

SYSTEM_PROMPT = """Tu es un assistant IA pour les services gouvernementaux du Cameroun.
Tu aides les entreprises et les citoyens a :
- Verifier des matricules CNPS
- Calculer leurs declarations TVA
- Calculer leurs cotisations sociales CNPS
- Consulter les echeances fiscales DGI
- Obtenir des statistiques economiques sur le Cameroun

Tu reponds en francais ou en anglais selon la langue de l'utilisateur.
Utilise les outils disponibles pour fournir des resultats precis et bases sur les donnees reelles.
Presente les montants en FCFA avec formatage lisible (ex: 1 500 000 FCFA).
Sois concis, precis et professionnel."""


async def process_chat(message: str, history: list[ChatMessage]) -> dict:
    """
    Orchestre un echange avec DeepSeek en utilisant les outils MCP definis.
    DeepSeek decide quels outils appeler (tool use compatible OpenAI),
    les appels sont executes sur le serveur MCP,
    les resultats sont renvoyes a DeepSeek pour generer la reponse finale.
    """
    log = logger.bind(message_len=len(message))
    log.info("chat_request_received")

    if not settings.deepseek_api_key:
        return {
            "message": "Cle API DeepSeek non configuree. Veuillez definir DEEPSEEK_API_KEY.",
            "tool_calls": [],
        }

    # DeepSeek uses OpenAI-compatible API
    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url="https://api.deepseek.com",
    )

    # Build tool definitions from MCP tool list (OpenAI format)
    mcp_tools = await list_tools()
    tools = [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.inputSchema,
            },
        }
        for t in mcp_tools
    ]

    # Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": message})

    executed_tool_calls: list[ToolCall] = []
    max_iterations = 5

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=4096,
        )
        log.info("deepseek_response", finish_reason=response.choices[0].finish_reason)

        choice = response.choices[0]

        if choice.finish_reason != "tool_calls":
            final_text = choice.message.content or "Desole, je n'ai pas pu generer une reponse."
            log.info("chat_completed", tool_calls_count=len(executed_tool_calls))
            return {
                "message": final_text,
                "tool_calls": [tc.model_dump() for tc in executed_tool_calls],
            }

        # Append assistant message with tool_calls
        messages.append(choice.message.model_dump(exclude_unset=True))

        # Execute each tool call via MCP server
        for tc in choice.message.tool_calls:
            tool_name = tc.function.name
            try:
                tool_input = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                tool_input = {}

            log.info("executing_mcp_tool", tool=tool_name, tool_input=tool_input)
            mcp_result = await call_tool(tool_name, tool_input)
            result_text = mcp_result[0].text if mcp_result else json.dumps({"error": "no result"})

            executed_tool_calls.append(
                ToolCall(tool_name=tool_name, input=tool_input, output=result_text)
            )

            # Append tool result in OpenAI format
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_text,
            })

    return {
        "message": "La requete a necessite trop d'iterations. Veuillez reformuler.",
        "tool_calls": [tc.model_dump() for tc in executed_tool_calls],
    }
