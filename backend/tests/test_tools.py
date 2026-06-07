import pytest
from app.tools.vat import calculate_vat
from app.tools.contributions import calculate_cnps_contributions
from app.tools.deadlines import get_tax_deadlines


class TestCalculateVAT:
    def test_standard_calculation(self):
        result = calculate_vat(revenue_ht=1_000_000, period="2026-03")
        assert result["success"] is True
        assert result["tva_amount_fcfa"] == 192_500
        assert result["revenue_ttc_fcfa"] == 1_192_500
        assert result["filing_deadline"] == "2026-04-15"

    def test_december_deadline_crosses_year(self):
        result = calculate_vat(revenue_ht=500_000, period="2025-12")
        assert result["filing_deadline"] == "2026-01-15"

    def test_invalid_period_format(self):
        result = calculate_vat(revenue_ht=100_000, period="march-2026")
        assert result["success"] is False
        assert "invalide" in result["error"].lower()

    def test_zero_revenue_rejected(self):
        result = calculate_vat(revenue_ht=0, period="2026-03")
        assert result["success"] is False

    def test_tva_rate_label(self):
        result = calculate_vat(revenue_ht=100_000, period="2026-01")
        assert result["tva_rate"] == "19.25%"


class TestCNPSContributions:
    def test_single_employee_below_ceiling(self):
        result = calculate_cnps_contributions([{"name": "Alice", "gross_salary": 300_000}])
        assert result["success"] is True
        assert len(result["details"]) == 1
        emp = result["details"][0]
        assert emp["salary_capped"] is False
        # Employee contribution: 4.2% of 300,000 = 12,600
        assert emp["employee"]["total"] == "12 600 FCFA"

    def test_salary_above_ceiling_is_capped(self):
        result = calculate_cnps_contributions([{"name": "Bob", "gross_salary": 1_000_000}])
        emp = result["details"][0]
        assert emp["salary_capped"] is True
        assert emp["cotisation_base_fcfa"] == 750_000

    def test_multiple_employees(self):
        employees = [
            {"name": "Alice", "gross_salary": 200_000},
            {"name": "Bob", "gross_salary": 400_000},
        ]
        result = calculate_cnps_contributions(employees)
        assert result["employees_count"] == 2
        assert result["success"] is True

    def test_invalid_salary_returns_error(self):
        result = calculate_cnps_contributions([{"name": "Bad", "gross_salary": -100}])
        assert "error" in result["details"][0]


class TestTaxDeadlines:
    def test_monthly_deadlines_count(self):
        result = get_tax_deadlines(month=3, year=2026)
        assert result["success"] is True
        # Should have TVA, AIB, IRCM, CNPS = 4 monthly deadlines
        monthly = [d for d in result["deadlines"] if not d["is_annual"]]
        assert len(monthly) == 4

    def test_december_includes_annual_deadlines(self):
        result = get_tax_deadlines(month=12, year=2025)
        annual = [d for d in result["deadlines"] if d["is_annual"]]
        assert len(annual) >= 2  # DSF + IS

    def test_march_due_date_for_april_period(self):
        result = get_tax_deadlines(month=3, year=2026)
        tva = next(d for d in result["deadlines"] if d["type"] == "TVA")
        assert tva["due_date"] == "2026-04-15"

    def test_invalid_month_rejected(self):
        result = get_tax_deadlines(month=13, year=2026)
        assert result["success"] is False

    def test_overdue_flag(self):
        result = get_tax_deadlines(month=1, year=2020)
        for d in result["deadlines"]:
            assert d["overdue"] is True
