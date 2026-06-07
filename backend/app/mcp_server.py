import json
import structlog
from mcp.server import Server
from mcp.types import Tool, TextContent

from app.tools import (
    verify_cnps_matricule,
    get_statistical_data,
    calculate_vat,
    calculate_cnps_contributions,
    get_tax_deadlines,
)

logger = structlog.get_logger()

mcp = Server("egov-cameroon-mcp")


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="verify_cnps_matricule",
            description=(
                "Vérifie qu'un matricule CNPS existe dans la base de données de la Caisse Nationale "
                "de Prévoyance Sociale du Cameroun. Effectue un appel réseau réel vers le portail "
                "e-services de la CNPS (cons.cnps.cm)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "matricule": {
                        "type": "string",
                        "description": "Numéro de matricule CNPS à vérifier (ex: C123456789)",
                    }
                },
                "required": ["matricule"],
            },
        ),
        Tool(
            name="get_statistical_data",
            description=(
                "Récupère des données statistiques économiques et démographiques du Cameroun "
                "via l'API publique de la Banque Mondiale. Indicateurs disponibles : gdp, "
                "gdp_per_capita, inflation, unemployment, population, poverty_rate, exports, imports."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "indicator": {
                        "type": "string",
                        "description": "Nom ou code de l'indicateur (ex: gdp, inflation, population)",
                    },
                    "start_year": {
                        "type": "integer",
                        "description": "Année de début (ex: 2018)",
                        "default": 2018,
                    },
                    "end_year": {
                        "type": "integer",
                        "description": "Année de fin (ex: 2023)",
                        "default": 2023,
                    },
                },
                "required": ["indicator"],
            },
        ),
        Tool(
            name="calculate_vat",
            description=(
                "Calcule la déclaration TVA mensuelle d'une entreprise camerounaise selon le "
                "Code Général des Impôts (taux 19.25%). Retourne le montant TVA collecté, "
                "le total TTC et la date limite de dépôt."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "revenue_ht": {
                        "type": "number",
                        "description": "Chiffre d'affaires hors taxes en FCFA",
                    },
                    "period": {
                        "type": "string",
                        "description": "Période fiscale au format YYYY-MM (ex: 2026-03)",
                    },
                },
                "required": ["revenue_ht", "period"],
            },
        ),
        Tool(
            name="calculate_cnps_contributions",
            description=(
                "Calcule les cotisations sociales CNPS pour une liste d'employés selon les taux "
                "légaux camerounais (employé 4.2%, employeur ~13.15%, plafond 750 000 FCFA/mois). "
                "Retourne le détail par employé et le total."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "employees": {
                        "type": "array",
                        "description": "Liste des employés avec leur salaire brut",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Nom de l'employé"},
                                "gross_salary": {
                                    "type": "number",
                                    "description": "Salaire brut mensuel en FCFA",
                                },
                            },
                            "required": ["name", "gross_salary"],
                        },
                    }
                },
                "required": ["employees"],
            },
        ),
        Tool(
            name="get_tax_deadlines",
            description=(
                "Retourne les échéances fiscales et sociales pour un mois et une année donnés "
                "au Cameroun : TVA, AIB, IRCM, CNPS, DSF annuelle, IS. "
                "Source : calendrier légal DGI Cameroun (impots.cm)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "month": {
                        "type": "integer",
                        "description": "Mois (1–12)",
                        "minimum": 1,
                        "maximum": 12,
                    },
                    "year": {
                        "type": "integer",
                        "description": "Année (ex: 2026)",
                        "minimum": 2020,
                        "maximum": 2030,
                    },
                },
                "required": ["month", "year"],
            },
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    log = logger.bind(mcp_tool=name, args=arguments)
    log.info("mcp_tool_called")

    try:
        if name == "verify_cnps_matricule":
            result = await verify_cnps_matricule(arguments["matricule"])

        elif name == "get_statistical_data":
            result = await get_statistical_data(
                indicator=arguments["indicator"],
                start_year=arguments.get("start_year", 2018),
                end_year=arguments.get("end_year", 2023),
            )

        elif name == "calculate_vat":
            result = calculate_vat(
                revenue_ht=float(arguments["revenue_ht"]),
                period=arguments["period"],
            )

        elif name == "calculate_cnps_contributions":
            result = calculate_cnps_contributions(employees=arguments["employees"])

        elif name == "get_tax_deadlines":
            result = get_tax_deadlines(
                month=int(arguments["month"]),
                year=int(arguments["year"]),
            )

        else:
            result = {"error": f"Outil inconnu : {name}"}

        log.info("mcp_tool_success", tool=name)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    except KeyError as exc:
        log.error("mcp_tool_missing_arg", error=str(exc))
        return [TextContent(type="text", text=json.dumps({"error": f"Argument manquant : {exc}"}))]
    except Exception as exc:
        log.error("mcp_tool_error", error=str(exc))
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]
