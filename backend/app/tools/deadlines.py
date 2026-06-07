import structlog
from datetime import date, datetime

logger = structlog.get_logger()

# Calendrier fiscal DGI Cameroun — source : impots.cm
# Délais légaux par type d'obligation
DEADLINES_RULES = {
    "tva": {
        "label": "Déclaration TVA mensuelle",
        "day": 15,
        "offset_months": 1,
        "description": "À déposer le 15 du mois suivant la période imposable",
    },
    "aib": {
        "label": "Acompte Impôt sur les Bénéfices (AIB)",
        "day": 15,
        "offset_months": 1,
        "description": "Versement mensuel de l'AIB — 15 du mois suivant",
    },
    "ircm": {
        "label": "IRCM / Retenues à la source",
        "day": 15,
        "offset_months": 1,
        "description": "Reversement des retenues à la source — 15 du mois suivant",
    },
    "cnps": {
        "label": "Déclaration CNPS mensuelle",
        "day": 15,
        "offset_months": 1,
        "description": "Déclaration et paiement des cotisations sociales — 15 du mois suivant",
    },
    "dsf": {
        "label": "Déclaration Statistique et Fiscale (DSF)",
        "day": 15,
        "offset_months": 3,
        "description": "Dépôt de la DSF annuelle — 15 mars de l'année suivante",
        "annual": True,
    },
    "is": {
        "label": "Impôt sur les Sociétés (IS) — solde",
        "day": 15,
        "offset_months": 3,
        "description": "Solde IS annuel — 15 mars de l'année suivante",
        "annual": True,
    },
}


def get_tax_deadlines(month: int, year: int) -> dict:
    """
    Retourne les échéances fiscales DGI et CNPS pour un mois/année donné.
    Calcul dynamique basé sur le calendrier légal camerounais.
    """
    log = logger.bind(tool="get_tax_deadlines", month=month, year=year)
    log.info("computing_deadlines")

    if not (1 <= month <= 12):
        return {"success": False, "error": "Le mois doit être entre 1 et 12."}
    if year < 2020 or year > 2030:
        return {"success": False, "error": "Année hors plage valide (2020–2030)."}

    period_label = datetime(year, month, 1).strftime("%B %Y")
    deadlines = []

    for key, rule in DEADLINES_RULES.items():
        if rule.get("annual"):
            # Annual deadlines: apply to December period only, due in March next year
            if month == 12:
                due_year = year + 1
                due_month = 3
                due_date = date(due_year, due_month, rule["day"])
                deadlines.append({
                    "type": key.upper(),
                    "label": rule["label"],
                    "due_date": due_date.isoformat(),
                    "description": rule["description"],
                    "is_annual": True,
                })
        else:
            # Monthly deadlines: due 15th of following month
            due_month = month % 12 + 1
            due_year = year + 1 if month == 12 else year
            try:
                due_date = date(due_year, due_month, rule["day"])
            except ValueError:
                continue
            deadlines.append({
                "type": key.upper(),
                "label": rule["label"],
                "due_date": due_date.isoformat(),
                "description": rule["description"],
                "is_annual": False,
            })

    # Sort by due date
    deadlines.sort(key=lambda x: x["due_date"])

    # Flag overdue
    today = date.today()
    for d in deadlines:
        d["overdue"] = date.fromisoformat(d["due_date"]) < today

    return {
        "success": True,
        "period": f"{year}-{month:02d}",
        "period_label": period_label,
        "deadlines": deadlines,
        "count": len(deadlines),
        "source": "DGI Cameroun — impots.cm",
        "note": "Délais susceptibles d'être modifiés par circulaire DGI. Vérifiez sur impots.cm.",
    }
