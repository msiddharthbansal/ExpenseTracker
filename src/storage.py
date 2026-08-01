import json
import logging
import os
import threading
from typing import Any

from src.config import DATA_FILE

logger = logging.getLogger(__name__)

FILE_LOCK = threading.Lock()


def read_all() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        return []
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array in {DATA_FILE}")
        if not all(isinstance(item, dict) for item in data):
            raise ValueError(f"Expected every expense to be a JSON object in {DATA_FILE}")
        return data
    except (json.JSONDecodeError, OSError):
        logger.exception("Failed to read data from %s", DATA_FILE)
        raise


def write_all(expenses: list[dict[str, Any]]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = DATA_FILE.with_suffix(".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(expenses, f, indent=2, ensure_ascii=False, default=str,)
            f.flush()
            os.fsync(f.fileno())
        tmp_path.replace(DATA_FILE)
    except OSError:
        logger.exception("Failed to write data to %s", DATA_FILE)
        raise
