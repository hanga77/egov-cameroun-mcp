import httpx
import structlog

logger = structlog.get_logger()

CNPS_VERIFY_URL = "https://cons.cnps.cm/DeclarationSalaires/CompteAssure/VerifInfoAssu.php"


async def verify_cnps_matricule(matricule: str) -> dict:
    """
    Vérifie un matricule CNPS via le portail e-services public de la CNPS Cameroun.
    Effectue un appel HTTP réel vers cons.cnps.cm.
    """
    matricule = matricule.strip().upper()

    if not matricule:
        return {"success": False, "error": "Le matricule ne peut pas être vide."}

    log = logger.bind(tool="verify_cnps_matricule", matricule=matricule)
    log.info("calling_cnps_api")

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # The CNPS public form accepts GET with the matricule as query param
            response = await client.get(
                CNPS_VERIFY_URL,
                params={"op": "create", "matricule": matricule},
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; eGovCMR/1.0)",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            log.info("cnps_response", status_code=response.status_code)

            if response.status_code == 200:
                body = response.text.lower()
                # Detect whether the CNPS portal returned a found/not-found indicator
                if "introuvable" in body or "not found" in body or "invalid" in body:
                    return {
                        "success": True,
                        "found": False,
                        "matricule": matricule,
                        "message": "Matricule non trouvé dans la base CNPS.",
                    }
                if "assuré" in body or "assure" in body or "nom" in body or "prenom" in body:
                    return {
                        "success": True,
                        "found": True,
                        "matricule": matricule,
                        "message": "Matricule CNPS valide et enregistré.",
                        "source": "CNPS Cameroun e-services",
                    }
                # Generic success — portal responded but content unclear
                return {
                    "success": True,
                    "found": None,
                    "matricule": matricule,
                    "message": "Le portail CNPS a répondu. Vérification manuelle recommandée.",
                    "portal_url": "https://e-services.cnps.cm",
                }
            else:
                return {
                    "success": False,
                    "error": f"Le portail CNPS a retourné le statut HTTP {response.status_code}.",
                }

    except httpx.TimeoutException:
        log.warning("cnps_timeout")
        return {"success": False, "error": "Délai d'attente dépassé. Le portail CNPS est momentanément indisponible."}
    except httpx.RequestError as exc:
        log.error("cnps_request_error", error=str(exc))
        return {"success": False, "error": f"Erreur réseau lors de la connexion au portail CNPS: {exc}"}
