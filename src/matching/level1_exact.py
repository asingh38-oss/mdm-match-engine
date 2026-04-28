"""
level1_exact.py — Level 1 of the matching pipeline: exact match check.

If the cleaned company name AND address are identical after normalization,
we can assign a high confidence score immediately without LLM calls.
We also do a fuzzy match at a high threshold here to catch minor typos
before handing off to the LLM agents.

This is intentionally fast and cheap — save LLM calls for the hard cases.
"""

from rapidfuzz import fuzz
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Fuzzy thresholds for Level 1
EXACT_NAME_THRESHOLD = 100       # 100 = truly identical after cleanup
FUZZY_NAME_THRESHOLD = 97        # very high — catch only obvious typos like "Boieng"
EXACT_ADDRESS_THRESHOLD = 100
FUZZY_ADDRESS_THRESHOLD = 95


def exact_match_score(record_a: dict, record_b: dict) -> dict:
    """
    Level 1 match check: exact and near-exact comparison of name + address fields.

    Returns a result dict:
        - name_score: 0-100 fuzzy similarity for company name
        - address_score: 0-100 fuzzy similarity for address
        - level1_score: combined score (0-100) from this level only
        - is_exact_match: bool, True if we're very confident this is a match at Level 1
        - reasoning: human-readable string explaining the result
    """
    name_a = record_a.get("name_expanded") or record_a.get("name_clean", "")
    name_b = record_b.get("name_expanded") or record_b.get("name_clean", "")

    addr_a = record_a.get("address_expanded") or record_a.get("address_clean", "")
    addr_b = record_b.get("address_expanded") or record_b.get("address_clean", "")

    # City + zip add confidence to address matching
    city_a = record_a.get("city_clean", "")
    city_b = record_b.get("city_clean", "")
    zip_a = str(record_a.get("zip_clean", ""))
    zip_b = str(record_b.get("zip_clean", ""))

    # Compute fuzzy similarity scores (token sort ratio handles word reordering)
    name_score = int(fuzz.token_sort_ratio(name_a, name_b))
    addr_score = int(fuzz.token_sort_ratio(addr_a, addr_b))
    city_score = int(fuzz.ratio(city_a, city_b))

    # Zip exact match is a strong signal
    zip_match = zip_a == zip_b and zip_a != ""

    # Combine into a Level 1 score
    # Weighted: name matters more than address at this level
    level1_score = (name_score * 0.6) + (addr_score * 0.3) + (city_score * 0.1)
    if zip_match:
        level1_score = min(level1_score + 5, 100)

    is_exact = name_score >= FUZZY_NAME_THRESHOLD and addr_score >= FUZZY_ADDRESS_THRESHOLD

    # Build reasoning string
    reasons = []
    reasons.append(f"Name similarity: {name_score}/100 ('{name_a}' vs '{name_b}')")
    reasons.append(f"Address similarity: {addr_score}/100")
    if city_score == 100:
        reasons.append("Cities match exactly")
    if zip_match:
        reasons.append(f"ZIP codes match ({zip_a})")
    if is_exact:
        reasons.append("Passed Level 1 exact/near-exact threshold — skipping to score computation")

    return {
        "name_score": name_score,
        "address_score": addr_score,
        "city_score": city_score,
        "zip_match": zip_match,
        "level1_score": round(level1_score, 2),
        "is_exact_match": is_exact,
        "reasoning": "; ".join(reasons),
    }


if __name__ == "__main__":
    a = {"name_clean": "boeing company inc", "name_expanded": "boeing company incorporated", "address_clean": "100 north riverside plaza", "address_expanded": "100 north riverside plaza", "city_clean": "chicago", "zip_clean": "60606"}
    b = {"name_clean": "the boeing company inc", "name_expanded": "boeing company incorporated", "address_clean": "100 n riverside plz", "address_expanded": "100 north riverside place", "city_clean": "chicago", "zip_clean": "60606"}

    result = exact_match_score(a, b)
    for k, v in result.items():
        print(f"  {k}: {v}")