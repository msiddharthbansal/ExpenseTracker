import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src import repository, services
from src.models import Expense, ExpenseCreate, ExpenseFilter, ExpenseSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expenses", tags=["expenses"])


def get_repository():
    return repository


@router.post("", response_model=Expense, status_code=status.HTTP_201_CREATED)
def add_expense(expense_in: ExpenseCreate, repo=Depends(get_repository)) -> Expense:
    try:
        return repo.add(expense_in)
    except Exception:
        logger.exception("Failed to save expense")
        raise HTTPException(status_code=500, detail="Failed to save expense")


@router.get("", response_model=list[Expense])
def get_expenses(filters: Annotated[ExpenseFilter, Query()], repo=Depends(get_repository)) -> list[Expense]:
    if filters.is_impossible():
        return []
    try:
        return repo.get_all(**filters.model_dump())
    except Exception:
        logger.exception("Failed to retrieve expenses")
        raise HTTPException(status_code=500, detail="Failed to retrieve expenses")


@router.get("/summary", response_model=ExpenseSummary)
def get_expense_summary(repo=Depends(get_repository)) -> ExpenseSummary:
    try:
        return services.compute_summary(repo.get_all())
    except Exception:
        logger.exception("Failed to compute expense summary")
        raise HTTPException(status_code=500, detail="Failed to compute expense summary")


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: uuid.UUID, repo=Depends(get_repository)) -> None:
    try:
        deleted = repo.delete(str(expense_id))
    except Exception:
        logger.exception("Failed to delete expense %s", expense_id)
        raise HTTPException(status_code=500, detail="Failed to delete expense")
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
