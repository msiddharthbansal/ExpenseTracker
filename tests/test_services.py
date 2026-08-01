from datetime import date

from src import services
from src.models import Category, Expense


def make_expense(amount: float, category: Category, id_: str = "1") -> Expense:
    return Expense(id=id_, title="Item", amount=amount, category=category, date=date(2026, 8, 1))


def test_compute_summary_returns_zero_total_and_empty_breakdown_for_no_expenses():
    summary = services.compute_summary([])

    assert summary.total == 0.0
    assert summary.by_category == {}


def test_compute_summary_computes_total_and_category_breakdown():
    expenses = [
        make_expense(10, Category.FOOD, "1"),
        make_expense(5, Category.FOOD, "2"),
        make_expense(200, Category.TRAVEL, "3"),
    ]

    summary = services.compute_summary(expenses)

    assert summary.total == 215.0
    assert summary.by_category == {Category.FOOD: 15.0, Category.TRAVEL: 200.0}


def test_compute_summary_rounds_floating_point_drift_to_two_decimal_places():
    expenses = [
        make_expense(0.1, Category.FOOD, "1"),
        make_expense(0.2, Category.FOOD, "2"),
    ]

    summary = services.compute_summary(expenses)

    assert summary.total == 0.3
    assert summary.by_category == {Category.FOOD: 0.3}
