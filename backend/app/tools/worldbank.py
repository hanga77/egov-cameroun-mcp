import httpx
import structlog

logger = structlog.get_logger()

WB_BASE = "https://api.worldbank.org/v2"

INDICATORS = {
    "gdp": "NY.GDP.MKTP.CD",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "inflation": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "population": "SP.POP.TOTL",
    "poverty_rate": "SI.POV.DDAY",
    "literacy_rate": "SE.ADT.LITR.ZS",
    "exports": "NE.EXP.GNFS.CD",
    "imports": "NE.IMP.GNFS.CD",
}


async def get_statistical_data(indicator: str, start_year: int = 2018, end_year: int = 2023) -> dict:
    """
    Récupère des données statistiques du Cameroun via l'API publique de la Banque Mondiale.
    Appel HTTP réel vers api.worldbank.org.
    """
    log = logger.bind(tool="get_statistical_data", indicator=indicator)

    # Resolve alias or use raw code
    wb_code = INDICATORS.get(indicator.lower(), indicator.upper())

    url = f"{WB_BASE}/country/CMR/indicator/{wb_code}"
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 50,
    }

    log.info("calling_worldbank_api", url=url, params=params)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            log.info("worldbank_response", status_code=response.status_code)
            response.raise_for_status()

            data = response.json()
            if not data or len(data) < 2:
                return {"success": False, "error": "Réponse inattendue de la Banque Mondiale."}

            meta = data[0]
            records = data[1] or []

            series = [
                {"year": r["date"], "value": r["value"]}
                for r in records
                if r.get("value") is not None
            ]
            series.sort(key=lambda x: x["year"])

            if not series:
                return {
                    "success": True,
                    "indicator": wb_code,
                    "country": "Cameroun",
                    "data": [],
                    "message": "Aucune donnée disponible pour cette période.",
                }

            indicator_meta = records[0].get("indicator", {}) if records else {}

            return {
                "success": True,
                "indicator_code": wb_code,
                "indicator_name": indicator_meta.get("value", wb_code),
                "country": "Cameroun",
                "source": "Banque Mondiale (api.worldbank.org)",
                "total_records": meta.get("total", len(series)),
                "data": series,
                "latest": series[-1] if series else None,
            }

    except httpx.TimeoutException:
        log.warning("worldbank_timeout")
        return {"success": False, "error": "Délai d'attente dépassé pour l'API Banque Mondiale."}
    except httpx.HTTPStatusError as exc:
        log.error("worldbank_http_error", status=exc.response.status_code)
        return {"success": False, "error": f"Erreur HTTP {exc.response.status_code} de la Banque Mondiale."}
    except Exception as exc:
        log.error("worldbank_error", error=str(exc))
        return {"success": False, "error": str(exc)}
