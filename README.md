# Smart Expense Tracker API

A REST API for managing personal expenses, built with FastAPI and a local JSON file for storage (no database).

## Status

All features from the spec are implemented:

- **Add an expense** — `POST /expenses`
- **List valid categories** — `GET /categories`
- **View all expenses** — `GET /expenses`
- **Filter expenses by category** — `GET /expenses?category=Food`
- **Category-wise and total expense summary** — `GET /expenses/summary`
- **Delete an expense** — `DELETE /expenses/{id}`
- **Search expenses** — `GET /expenses` with any combination of `title`, `category`, `min_amount`, `max_amount`, `start_date`, `end_date`, `month`, `year`

## Requirements

- Python 3.10+

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the server

```bash
source .venv/bin/activate
uvicorn src.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive docs (Swagger UI) at `http://127.0.0.1:8000/docs`.

## Run the tests

```bash
source .venv/bin/activate
pytest
```

Tests write to an isolated temporary data file (via a pytest fixture) and never touch the real `data/expenses.json`.

## Example: add an expense

```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"title": "Coffee", "amount": 4.5, "category": "Food", "date": "2026-08-01"}'
```

Valid `category` values: `Food`, `Travel`, `Bills`, `Shopping`, `Utilities`, `Entertainment`, `Other`.

`amount` must be greater than 0. `date` must be in `YYYY-MM-DD` format. `title` must not be blank.

## Example: list valid categories

```bash
curl http://127.0.0.1:8000/categories
```

Returns the fixed list of category values above — useful for populating a category picker in a UI without hardcoding the list client-side.

## Example: view all expenses

```bash
curl http://127.0.0.1:8000/expenses
```

Returns a JSON array of all stored expenses (empty array if none exist yet).

## Example: filter expenses by category

```bash
curl "http://127.0.0.1:8000/expenses?category=Food"
```

Same endpoint as "view all", with an optional `category` query parameter. Returns only expenses matching that category (empty array if none match). An invalid category value returns `422`.

## Example: search expenses

`GET /expenses` also accepts these optional query parameters, all combinable (every provided filter must match — logical AND):

| Param | Meaning |
|---|---|
| `title` | Case-insensitive substring match against the expense title |
| `category` | Exact category match |
| `min_amount` / `max_amount` | Inclusive amount range |
| `start_date` / `end_date` | Inclusive date range (`YYYY-MM-DD`) |
| `month` | Calendar month (1–12), any year, unless `year` is also given |
| `year` | Calendar year, any month, unless `month` is also given |

```bash
curl "http://127.0.0.1:8000/expenses?title=coffee&category=Food&max_amount=10&month=8&year=2026"
```

Returns `422` if `min_amount > max_amount` or `start_date` is after `end_date`. Returns an empty array if no expenses match.

## Example: category-wise and total expense summary

```bash
curl http://127.0.0.1:8000/expenses/summary
```

```json
{
  "total": 210.0,
  "by_category": {
    "Food": 10.0,
    "Travel": 200.0
  }
}
```

`total` is the sum of all expenses; `by_category` only includes categories that have at least one expense. Both are rounded to 2 decimal places. With no expenses, returns `{"total": 0.0, "by_category": {}}`.

## Example: delete an expense

```bash
curl -X DELETE http://127.0.0.1:8000/expenses/<id>
```

Returns `204 No Content` on success. Returns `404` if the id doesn't exist (including deleting the same id twice), and `422` if the id isn't a validly formatted UUID.

## Data storage

Expenses are stored as a JSON array in `data/expenses.json`, created automatically on first write. This file is git-ignored since it's runtime data, not source.

## Project structure

```
src/
  config.py          
  models.py           # Pydantic models: Category enum, ExpenseCreate, Expense, ExpenseSummary, ExpenseFilter
  storage.py           # thread-safe JSON file read/write (lock + atomic write)
  repository.py         # CRUD + multi-criteria search over expenses
  services.py            
  routes/expenses.py       # POST /expenses, GET /expenses (search/filter), GET /expenses/summary, DELETE /expenses/{id}
  routes/categories.py    # GET /categories route handler
  main.py                
tests/
  test_repository.py    # unit tests, no HTTP layer
  test_services.py        # unit tests for summary computation, no HTTP or storage
  test_routes.py          # integration tests via FastAPI TestClient
```
