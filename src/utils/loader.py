"""
loader.py — Data loader for CSV files.
Reads CSV into record dict format expected by the pipeline.
"""

import csv
from typing import List, Dict, Any
from .logger import get_logger


def load_records(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load records from a CSV file into a list of dictionaries.

    Each dictionary contains keys: name, address, city, state, zip, country.
    Missing columns are handled gracefully by setting them to None.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        List[Dict[str, Any]]: List of record dictionaries.
    """
    logger = get_logger(__name__)
    records = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = {
                    'name': row.get('name'),
                    'address': row.get('address'),
                    'city': row.get('city'),
                    'state': row.get('state'),
                    'zip': row.get('zip'),
                    'country': row.get('country'),
                }
                records.append(record)
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return []

    logger.info(f"Loaded {len(records)} records from {csv_path}")
    return records