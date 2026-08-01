from fastapi import APIRouter

from src.models import Category

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[Category])
def list_categories() -> list[Category]:
    return list(Category)
