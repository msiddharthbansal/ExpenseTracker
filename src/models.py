from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class Category(str, Enum):
    FOOD = "Food"
    TRAVEL = "Travel"
    BILLS = "Bills"
    SHOPPING = "Shopping"
    UTILITIES = "Utilities"
    ENTERTAINMENT = "Entertainment"
    OTHER = "Other"


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    category: Category
    date: date

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("title must not be blank")
        return trimmed

    @field_validator("amount")
    @classmethod
    def round_amount(cls, value: float) -> float:
        return round(value, 2)


class Expense(ExpenseCreate):
    id: str


class ExpenseSummary(BaseModel):
    total: float
    by_category: dict[Category, float]


class ExpenseFilter(BaseModel):
    category: Category | None = None
    title: str | None = None
    min_amount: float | None = Field(default=None, ge=0)
    max_amount: float | None = Field(default=None, ge=0)
    start_date: date | None = Field(default=None, ge=date(2000, 1, 1), le=date(2100, 12, 31))
    end_date: date | None = Field(default=None, ge=date(2000, 1, 1), le=date(2100, 12, 31))
    month: int | None = Field(default=None, ge=1, le=12)
    year: int | None = Field(default=None, ge=1900, le=2100)

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.min_amount is not None and self.max_amount is not None and self.min_amount > self.max_amount:
            raise ValueError("min_amount must not be greater than max_amount")
        if self.start_date is not None and self.end_date is not None and self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        if self.title is not None:
            self.title = self.title.strip()
            if not self.title:
                raise ValueError("title must not be empty")

            if len(self.title) > 200:
                raise ValueError("title must not exceed 100 characters")
        return self

    def is_impossible(self) -> bool:
        if self.start_date is None or self.end_date is None:
            return False
        if self.year is not None:
            if self.year < self.start_date.year or self.year > self.end_date.year:
                return True
        if self.month is not None:
            possible_months = set()
            current = date(self.start_date.year, self.start_date.month, 1)
            end = date(self.end_date.year, self.end_date.month, 1)
            while current <= end:
                possible_months.add(current.month)
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)
            if self.month not in possible_months:
                return True
        return False
