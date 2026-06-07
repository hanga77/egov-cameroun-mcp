import structlog

logger = structlog.get_logger()

# Taux de cotisations CNPS Cameroun (Loi n92/007 du 14 aout 1992)
EMPLOYEE_RATE = 0.042
EMPLOYER_PENSION_RATE = 0.042
EMPLOYER_HEALTH_RATE = 0.0
EMPLOYER_AT_RATE = 0.0175
EMPLOYER_FAM_RATE = 0.07
SALARY_CEILING = 750_000


def _fmt(n: float) -> str:
    """Format integer with spaces as thousands separator + FCFA suffix."""
    s = str(int(n))
    groups = []
    while s:
        groups.append(s[-3:])
        s = s[:-3]
    return " ".join(reversed(groups)) + " FCFA"


def calculate_cnps_contributions(employees: list[dict]) -> dict:
    """
    Calcule les cotisations CNPS par employe selon les taux legaux camerounais.
    Plafond : 750 000 FCFA/mois. Source : CNPS Cameroun / Code du Travail.
    """
    log = logger.bind(tool="calculate_cnps_contributions", count=len(employees))
    log.info("calculating_contributions")

    results = []
    total_employee = 0.0
    total_employer = 0.0

    for emp in employees:
        name = emp.get("name", "Employe")
        salary = float(emp.get("gross_salary", 0))

        if salary <= 0:
            results.append({"name": name, "error": "Salaire invalide"})
            continue

        base = min(salary, SALARY_CEILING)
        capped = base < salary

        emp_contribution = round(base * EMPLOYEE_RATE, 0)
        employer_pension = round(base * EMPLOYER_PENSION_RATE, 0)
        employer_at = round(base * EMPLOYER_AT_RATE, 0)
        employer_fam = round(base * EMPLOYER_FAM_RATE, 0)
        employer_total = employer_pension + employer_at + employer_fam

        total_employee += emp_contribution
        total_employer += employer_total

        results.append({
            "name": name,
            "gross_salary_fcfa": salary,
            "cotisation_base_fcfa": base,
            "salary_capped": capped,
            "employee": {
                "vieillesse_invalidite_deces": f"{_fmt(emp_contribution)} ({EMPLOYEE_RATE*100:.1f}%)",
                "total": _fmt(emp_contribution),
            },
            "employer": {
                "vieillesse_pension": f"{_fmt(employer_pension)} ({EMPLOYER_PENSION_RATE*100:.1f}%)",
                "accidents_travail": f"{_fmt(employer_at)} ({EMPLOYER_AT_RATE*100:.2f}%)",
                "prestations_familiales": f"{_fmt(employer_fam)} ({EMPLOYER_FAM_RATE*100:.1f}%)",
                "total": _fmt(employer_total),
            },
            "net_salary_estimate_fcfa": round(salary - emp_contribution, 0),
            "total_cost_employer_fcfa": round(salary + employer_total, 0),
        })

    grand_total = total_employee + total_employer

    return {
        "success": True,
        "employees_count": len(results),
        "salary_ceiling_fcfa": SALARY_CEILING,
        "details": results,
        "summary": {
            "total_employee_contributions": _fmt(total_employee),
            "total_employer_contributions": _fmt(total_employer),
            "grand_total_cnps": _fmt(grand_total),
        },
        "legal_basis": "Loi n92/007 du 14 aout 1992 - Code du Travail Cameroun",
        "rates": {
            "employee_vieillesse": "4.2%",
            "employer_pension": "4.2%",
            "employer_at_min": "1.75%",
            "employer_familiales": "7%",
            "plafond_mensuel": "750 000 FCFA",
        },
    }
