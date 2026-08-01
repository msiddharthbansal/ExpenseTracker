import logging

from src.models import Category, Expense, ExpenseSummary

logger = logging.getLogger(__name__)


def compute_summary(expenses: list[Expense]) -> ExpenseSummary:
    totals_by_category: dict[Category, float] = {}
    for expense in expenses:
        totals_by_category[expense.category] = totals_by_category.get(expense.category, 0.0) + expense.amount

    by_category = {category: round(amount, 2) for category, amount in totals_by_category.items()}
    total = round(sum(totals_by_category.values()), 2)

    logger.info("Computed expense summary: total=%.2f across %d categories", total, len(by_category))
    return ExpenseSummary(total=total, by_category=by_category)
