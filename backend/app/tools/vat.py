import structlog
from datetime import datetime

logger = structlog.get_logger()

# Taux TVA Cameroun — Code Général des Impôts 2026
TVA_RATE = 0.1925  # 19.25%
TVA_REDUCED_RATE = 0.0  # Exonération pour certains secteurs (santé, éducation)

# Délai légal de dépôt : 15 du mois suivant la période
FILING_DAY = 15


def calculate_vat(revenue_ht: float, period: str) -> dict:
    """
    Calcule la déclaration TVA selon le Code Général des Impôts du Cameroun.
    Taux standard : 19.25% (article 128 CGI Cameroun).
    """
    log = logger.bind(tool="calculate_vat", period=period, revenue_ht=revenue_ht)
    log.info("calculating_vat")

    try:
        year, month = map(int, period.split("-"))
        period_label = datetime(year, month, 1).strftime("%B %Y")
    except ValueError:
        return {"success": False, "error": "Format de période invalide. Utilisez YYYY-MM."}

    if revenue_ht <= 0:
        return {"success": False, "error": "Le chiffre d'affaires HT doit être positif."}

    tva_amount = round(revenue_ht * TVA_RATE, 0)
    revenue_ttc = round(revenue_ht + tva_amount, 0)

    # Deadline: 15th of following month
    next_month = month % 12 + 1
    deadline_year = year + 1 if month == 12 else year
    deadline = f"{deadline_year}-{next_month:02d}-{FILING_DAY:02d}"

    return {
        "success": True,
        "period": period,
        "period_label": period_label,
        "revenue_ht_fcfa": revenue_ht,
        "tva_rate": f"{TVA_RATE * 100:.2f}%",
        "tva_amount_fcfa": tva_amount,
        "revenue_ttc_fcfa": revenue_ttc,
        "filing_deadline": deadline,
        "declaration_summary": {
            "CA_HT": f"{revenue_ht:,.0f} FCFA",
            "TVA_collectée": f"{tva_amount:,.0f} FCFA",
            "Total_TTC": f"{revenue_ttc:,.0f} FCFA",
            "Délai_dépôt": f"À déposer avant le {deadline}",
        },
        "legal_basis": "Article 128 CGI Cameroun 2026 — Taux standard 19.25%",
        "portal": "https://teledeclaration-dgi.cm",
    }
