"""
level4_address.py — level 4: address deep analysis agent
TODO: implement analyze_addresses() — see teammate guidelines
"""

from src.utils.logger import get_logger
logger = get_logger(__name__)


def analyze_addresses(record_a: dict, record_b: dict) -> dict:
    # placeholder until teammate implements this
    logger.warning("level 4 not implemented yet, returning neutral score")
    return {
        "address_match_score": 50,
        "is_same_address": False,
        "issues_found": ["level 4 not implemented yet"],
        "reasoning": "address analysis not implemented yet",
    }
