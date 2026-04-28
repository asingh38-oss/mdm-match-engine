"""
loader.py — reads a CSV file and returns records as a list of dicts

nothing fancy, just wraps the csv module so the rest of the
code doesn't have to deal with file I/O directly
"""

import csv
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_records(csv_path: str) -> list[dict]:
    """
    Load records from a CSV. Expected columns: name, address, city, state, zip, country
    Missing columns just get set to None, won't crash.
    """
    records = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append({
                    "name":    row.get("name"),
                    "address": row.get("address"),
                    "city":    row.get("city"),
                    "state":   row.get("state"),
                    "zip":     row.get("zip"),
                    "country": row.get("country"),
                })
    except FileNotFoundError:
        logger.error(f"file not found: {csv_path}")
        return []
    except Exception as e:
        logger.error(f"something went wrong loading the CSV: {e}")
        return []

    logger.info(f"loaded {len(records)} records from {csv_path}")
    return records