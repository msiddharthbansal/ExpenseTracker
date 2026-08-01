from fastapi.testclient import TestClient

from src.main import app
from src.models import Category

client = TestClient(app)

VALID_PAYLOAD = {"title": "Coffee", "amount": 4.5, "category": "Food", "date": "2026-08-01"}


def test_add_expense_success():
    response = client.post("/expenses", json=VALID_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Coffee"
    assert body["amount"] == 4.5
    assert body["category"] == "Food"
    assert body["date"] == "2026-08-01"
    assert "id" in body and body["id"]


def test_add_expense_negative_amount_rejected():
    response = client.post("/expenses", json={**VALID_PAYLOAD, "amount": -5})

    assert response.status_code == 422


def test_add_expense_zero_amount_rejected():
    response = client.post("/expenses", json={**VALID_PAYLOAD, "amount": 0})

    assert response.status_code == 422


def test_add_expense_blank_title_rejected():
    response = client.post("/expenses", json={**VALID_PAYLOAD, "title": "   "})

    assert response.status_code == 422


def test_add_expense_invalid_category_rejected():
    response = client.post("/expenses", json={**VALID_PAYLOAD, "category": "Nope"})

    assert response.status_code == 422


def test_add_expense_invalid_date_rejected():
    response = client.post("/expenses", json={**VALID_PAYLOAD, "date": "not-a-date"})

    assert response.status_code == 422


def test_add_expense_missing_field_rejected():
    payload = dict(VALID_PAYLOAD)
    del payload["amount"]

    response = client.post("/expenses", json=payload)

    assert response.status_code == 422


def test_list_categories_returns_all_enum_values():
    response = client.get("/categories")

    assert response.status_code == 200
    assert response.json() == [c.value for c in Category]


def test_get_expenses_returns_empty_list_when_none_added():
    response = client.get("/expenses")

    assert response.status_code == 200
    assert response.json() == []


def test_get_expenses_returns_added_expenses():
    added = client.post("/expenses", json=VALID_PAYLOAD).json()

    response = client.get("/expenses")

    assert response.status_code == 200
    assert response.json() == [added]


def test_get_expenses_filters_by_category():
    food = client.post("/expenses", json=VALID_PAYLOAD).json()
    client.post("/expenses", json={**VALID_PAYLOAD, "title": "Flight", "category": "Travel"})

    response = client.get("/expenses", params={"category": "Food"})

    assert response.status_code == 200
    assert response.json() == [food]


def test_get_expenses_filter_with_no_matches_returns_empty_list():
    client.post("/expenses", json=VALID_PAYLOAD)

    response = client.get("/expenses", params={"category": "Travel"})

    assert response.status_code == 200
    assert response.json() == []


def test_get_expenses_invalid_category_filter_rejected():
    response = client.get("/expenses", params={"category": "Nope"})

    assert response.status_code == 422


def test_get_expense_summary_empty():
    response = client.get("/expenses/summary")

    assert response.status_code == 200
    assert response.json() == {"total": 0.0, "by_category": {}}


def test_get_expense_summary_computes_total_and_category_breakdown():
    client.post("/expenses", json=VALID_PAYLOAD)
    client.post("/expenses", json={**VALID_PAYLOAD, "amount": 5.5})
    client.post("/expenses", json={**VALID_PAYLOAD, "title": "Flight", "amount": 200, "category": "Travel"})

    response = client.get("/expenses/summary")

    assert response.status_code == 200
    assert response.json() == {"total": 210.0, "by_category": {"Food": 10.0, "Travel": 200.0}}


def test_delete_expense_success_removes_it():
    expense_id = client.post("/expenses", json=VALID_PAYLOAD).json()["id"]

    response = client.delete(f"/expenses/{expense_id}")

    assert response.status_code == 204
    assert client.get("/expenses").json() == []


def test_delete_expense_nonexistent_id_returns_404():
    response = client.delete("/expenses/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_delete_expense_twice_returns_404_second_time():
    expense_id = client.post("/expenses", json=VALID_PAYLOAD).json()["id"]

    first = client.delete(f"/expenses/{expense_id}")
    second = client.delete(f"/expenses/{expense_id}")

    assert first.status_code == 204
    assert second.status_code == 404


def test_delete_expense_malformed_id_rejected():
    response = client.delete("/expenses/not-a-uuid")

    assert response.status_code == 422


def test_search_expenses_by_title_substring_case_insensitive():
    client.post("/expenses", json={**VALID_PAYLOAD, "title": "Morning Coffee Run"})
    client.post("/expenses", json={**VALID_PAYLOAD, "title": "Flight", "category": "Travel"})

    response = client.get("/expenses", params={"title": "coffee"})

    assert response.status_code == 200
    assert [e["title"] for e in response.json()] == ["Morning Coffee Run"]


def test_search_expenses_by_amount_range():
    client.post("/expenses", json={**VALID_PAYLOAD, "amount": 5})
    client.post("/expenses", json={**VALID_PAYLOAD, "amount": 500})

    response = client.get("/expenses", params={"min_amount": 1, "max_amount": 10})

    assert response.status_code == 200
    assert [e["amount"] for e in response.json()] == [5.0]


def test_search_expenses_by_date_range():
    client.post("/expenses", json={**VALID_PAYLOAD, "date": "2026-08-01"})
    client.post("/expenses", json={**VALID_PAYLOAD, "date": "2026-09-01"})

    response = client.get("/expenses", params={"start_date": "2026-07-01", "end_date": "2026-08-15"})

    assert response.status_code == 200
    assert [e["date"] for e in response.json()] == ["2026-08-01"]


def test_search_expenses_by_month_and_year():
    client.post("/expenses", json={**VALID_PAYLOAD, "date": "2026-08-01"})
    client.post("/expenses", json={**VALID_PAYLOAD, "date": "2025-08-01"})
    client.post("/expenses", json={**VALID_PAYLOAD, "date": "2026-09-01"})

    response = client.get("/expenses", params={"month": 8, "year": 2026})

    assert response.status_code == 200
    assert [e["date"] for e in response.json()] == ["2026-08-01"]


def test_search_expenses_combines_filters_with_and():
    client.post("/expenses", json={**VALID_PAYLOAD, "title": "Coffee", "amount": 5})
    client.post("/expenses", json={**VALID_PAYLOAD, "title": "Coffee", "amount": 50})
    client.post("/expenses", json={**VALID_PAYLOAD, "title": "Flight", "amount": 5, "category": "Travel"})

    response = client.get("/expenses", params={"category": "Food", "title": "coffee", "max_amount": 10})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["amount"] == 5.0


def test_search_expenses_no_matches_returns_empty_list():
    client.post("/expenses", json=VALID_PAYLOAD)

    response = client.get("/expenses", params={"title": "nonexistent"})

    assert response.status_code == 200
    assert response.json() == []


def test_search_expenses_invalid_amount_range_rejected():
    response = client.get("/expenses", params={"min_amount": 10, "max_amount": 5})

    assert response.status_code == 422


def test_search_expenses_invalid_date_range_rejected():
    response = client.get("/expenses", params={"start_date": "2026-08-15", "end_date": "2026-08-01"})

    assert response.status_code == 422


def test_search_expenses_invalid_month_rejected():
    response = client.get("/expenses", params={"month": 13})

    assert response.status_code == 422
