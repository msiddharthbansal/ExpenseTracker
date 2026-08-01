from datetime import date

from src import repository, storage
from src.models import Category, ExpenseCreate


def test_add_creates_expense_with_generated_id():
    expense_in = ExpenseCreate(title="Coffee", amount=4.5, category=Category.FOOD, date=date(2026, 8, 1))

    expense = repository.add(expense_in)

    assert expense.id
    assert expense.title == "Coffee"
    assert expense.amount == 4.5
    assert expense.category == Category.FOOD
    assert expense.date == date(2026, 8, 1)


def test_add_persists_to_storage():
    expense_in = ExpenseCreate(title="Lunch", amount=12, category=Category.FOOD, date=date(2026, 8, 1))

    expense = repository.add(expense_in)

    stored = storage.read_all()
    assert len(stored) == 1
    assert stored[0]["id"] == expense.id
    assert stored[0]["title"] == "Lunch"


def test_add_multiple_expenses_appends_rather_than_overwrites():
    for i in range(3):
        repository.add(ExpenseCreate(title=f"Item{i}", amount=1, category=Category.OTHER, date=date(2026, 8, 1)))

    assert len(storage.read_all()) == 3


def test_add_rounds_amount_to_two_decimal_places():
    expense = repository.add(
        ExpenseCreate(title="Snack", amount=1.005, category=Category.FOOD, date=date(2026, 8, 1))
    )

    assert expense.amount == 1.0


def test_get_all_returns_empty_list_when_no_expenses():
    assert repository.get_all() == []


def test_get_all_returns_all_added_expenses():
    added = [
        repository.add(ExpenseCreate(title=f"Item{i}", amount=1, category=Category.OTHER, date=date(2026, 8, 1)))
        for i in range(3)
    ]

    retrieved = repository.get_all()

    assert [e.id for e in retrieved] == [e.id for e in added]


def test_get_all_filters_by_category():
    food = repository.add(ExpenseCreate(title="Lunch", amount=10, category=Category.FOOD, date=date(2026, 8, 1)))
    repository.add(ExpenseCreate(title="Flight", amount=200, category=Category.TRAVEL, date=date(2026, 8, 1)))

    retrieved = repository.get_all(category=Category.FOOD)

    assert [e.id for e in retrieved] == [food.id]


def test_get_all_filter_with_no_matches_returns_empty_list():
    repository.add(ExpenseCreate(title="Lunch", amount=10, category=Category.FOOD, date=date(2026, 8, 1)))

    assert repository.get_all(category=Category.TRAVEL) == []


def test_delete_removes_expense_and_returns_true():
    expense = repository.add(ExpenseCreate(title="Lunch", amount=10, category=Category.FOOD, date=date(2026, 8, 1)))

    assert repository.delete(expense.id) is True
    assert repository.get_all() == []


def test_delete_nonexistent_id_returns_false():
    assert repository.delete("does-not-exist") is False


def test_delete_only_removes_matching_expense():
    keep = repository.add(ExpenseCreate(title="Lunch", amount=10, category=Category.FOOD, date=date(2026, 8, 1)))
    remove = repository.add(ExpenseCreate(title="Flight", amount=200, category=Category.TRAVEL, date=date(2026, 8, 1)))

    assert repository.delete(remove.id) is True
    assert [e.id for e in repository.get_all()] == [keep.id]


def test_get_all_filters_by_title_substring_case_insensitive():
    coffee = repository.add(ExpenseCreate(title="Morning Coffee Run", amount=5, category=Category.FOOD, date=date(2026, 8, 1)))
    repository.add(ExpenseCreate(title="Flight", amount=200, category=Category.TRAVEL, date=date(2026, 8, 1)))

    assert [e.id for e in repository.get_all(title="coffee")] == [coffee.id]


def test_get_all_filters_by_amount_range():
    cheap = repository.add(ExpenseCreate(title="Snack", amount=5, category=Category.FOOD, date=date(2026, 8, 1)))
    repository.add(ExpenseCreate(title="Flight", amount=200, category=Category.TRAVEL, date=date(2026, 8, 1)))

    assert [e.id for e in repository.get_all(min_amount=1, max_amount=10)] == [cheap.id]


def test_get_all_filters_by_date_range():
    early = repository.add(ExpenseCreate(title="Lunch", amount=10, category=Category.FOOD, date=date(2026, 8, 1)))
    repository.add(ExpenseCreate(title="Dinner", amount=10, category=Category.FOOD, date=date(2026, 9, 1)))

    retrieved = repository.get_all(start_date=date(2026, 7, 1), end_date=date(2026, 8, 15))

    assert [e.id for e in retrieved] == [early.id]


def test_get_all_filters_by_month_across_years():
    august_2025 = repository.add(ExpenseCreate(title="Lunch", amount=10, category=Category.FOOD, date=date(2025, 8, 1)))
    august_2026 = repository.add(ExpenseCreate(title="Dinner", amount=10, category=Category.FOOD, date=date(2026, 8, 1)))
    repository.add(ExpenseCreate(title="Snack", amount=10, category=Category.FOOD, date=date(2026, 9, 1)))

    retrieved = repository.get_all(month=8)

    assert {e.id for e in retrieved} == {august_2025.id, august_2026.id}


def test_get_all_filters_by_year_across_months():
    jan = repository.add(ExpenseCreate(title="Lunch", amount=10, category=Category.FOOD, date=date(2026, 1, 1)))
    repository.add(ExpenseCreate(title="Dinner", amount=10, category=Category.FOOD, date=date(2025, 1, 1)))

    assert [e.id for e in repository.get_all(year=2026)] == [jan.id]


def test_get_all_filters_by_month_and_year_combined():
    match = repository.add(ExpenseCreate(title="Lunch", amount=10, category=Category.FOOD, date=date(2026, 8, 1)))
    repository.add(ExpenseCreate(title="Dinner", amount=10, category=Category.FOOD, date=date(2025, 8, 1)))

    assert [e.id for e in repository.get_all(month=8, year=2026)] == [match.id]


def test_get_all_combines_multiple_filters_with_and():
    match = repository.add(ExpenseCreate(title="Coffee", amount=5, category=Category.FOOD, date=date(2026, 8, 1)))
    repository.add(ExpenseCreate(title="Coffee", amount=50, category=Category.FOOD, date=date(2026, 8, 1)))
    repository.add(ExpenseCreate(title="Flight", amount=5, category=Category.TRAVEL, date=date(2026, 8, 1)))

    retrieved = repository.get_all(category=Category.FOOD, title="coffee", max_amount=10)

    assert [e.id for e in retrieved] == [match.id]
