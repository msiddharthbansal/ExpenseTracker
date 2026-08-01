import logging

from fastapi import FastAPI

from src.routes.categories import router as categories_router
from src.routes.expenses import router as expenses_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Smart Expense Tracker API")
app.include_router(expenses_router)
app.include_router(categories_router)
