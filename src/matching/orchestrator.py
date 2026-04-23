"""
orchestrator.py — runs a candidate pair through all 4 matching levels

takes two processed records, runs them through levels 1-4 in order,
and returns all the signals combined. level 5 scoring gets added in week 3.
"""

from src.matching.level1_exact import exact_match_score
from src.matching.level2_geo import geo_distance_check
from src.matching.level3_name import verify_company_names
from src.matching.level4_address import analyze_addresses
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_matching_pipeline(record_a: dict, record_b: dict) -> dict:
    """
    runs a pair of records through all 4 matching levels.
    returns a combined result dict with signals from each level.

    level 5 final scoring will be added in week 3.
    """
    name_a = record_a.get("name_clean", "unknown")
    name_b = record_b.get("name_clean", "unknown")
    logger.info(f"matching: '{name_a}' vs '{name_b}'")

    results = {}

    # level 1 — fast fuzzy match, no API calls
    logger.info("running level 1...")
    results["level1"] = exact_match_score(record_a, record_b)

    # level 2 — geo distance check, skip if level 1 already flagged exact match
    logger.info("running level 2...")
    results["level2"] = geo_distance_check(record_a, record_b)

    # level 3 — LLM company name verification
    logger.info("running level 3...")
    results["level3"] = verify_company_names(record_a, record_b)

    # level 4 — LLM address deep analysis
    logger.info("running level 4...")
    results["level4"] = analyze_addresses(record_a, record_b)

    logger.info("matching complete")
    return results


if __name__ == "__main__":
    # test with two honeywell records from our sample dataset
    a = {
        "name_clean": "honeywell international INC",
        "name_expanded": "Honeywell International Incorporated",
        "address_clean": "300 south tryon street",
        "address_expanded": "300 south tryon street",
        "city_clean": "charlotte",
        "state_clean": "nc",
        "zip_clean": "28202",
        "country_clean": "usa",
    }
    b = {
        "name_clean": "honeywell intl",
        "name_expanded": "Honeywell International",
        "address_clean": "300 south tryon street",
        "address_expanded": "300 south tryon street",
        "city_clean": "charlotte",
        "state_clean": "nc",
        "zip_clean": "28202",
        "country_clean": "united states",
    }

    results = run_matching_pipeline(a, b)

    for level, data in results.items():
        print(f"\n{level}:")
        for k, v in data.items():
            print(f"  {k}: {v}")