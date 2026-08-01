import logging
import uuid
from datetime import date

from src import storage
from src.models import Category, Expense, ExpenseCreate

logger = logging.getLogger(__name__)


def add(expense_create: ExpenseCreate) -> Expense:
    expense = Expense(id=str(uuid.uuid4()), **expense_create.model_dump())
    with storage.FILE_LOCK:
        expenses = storage.read_all()
        expenses.append(expense.model_dump(mode="json"))
        storage.write_all(expenses)
    logger.info("Added expense %s in category %s", expense.id, expense.category.value)
    return expense


def get_all(
    category: Category | None = None,
    title: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    month: int | None = None,
    year: int | None = None,
) -> list[Expense]:
    expenses = [Expense(**item) for item in storage.read_all()]
    if category is not None:
        expenses = [e for e in expenses if e.category == category]
    if title is not None:
        needle = title.lower()
        expenses = [e for e in expenses if needle in e.title.lower()]
    if min_amount is not None:
        expenses = [e for e in expenses if e.amount >= min_amount]
    if max_amount is not None:
        expenses = [e for e in expenses if e.amount <= max_amount]
    if start_date is not None:
        expenses = [e for e in expenses if e.date >= start_date]
    if end_date is not None:
        expenses = [e for e in expenses if e.date <= end_date]
    if month is not None:
        expenses = [e for e in expenses if e.date.month == month]
    if year is not None:
        expenses = [e for e in expenses if e.date.year == year]
    logger.info("Retrieved %d expenses (filters applied)", len(expenses))
    return expenses


def delete(expense_id: str) -> bool:
    with storage.FILE_LOCK:
        expenses = storage.read_all()
        remaining = [e for e in expenses if e["id"] != expense_id]
        if len(remaining) == len(expenses):
            return False
        storage.write_all(remaining)
    logger.info("Deleted expense %s", expense_id)
    return True
