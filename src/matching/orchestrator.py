"""
orchestrator.py — runs a candidate pair through all 5 matching levels

takes two processed records, runs levels 1-4, then computes
the final score and classification in level 5.
"""

from src.matching.level1_exact import exact_match_score
from src.matching.level2_geo import geo_distance_check
from src.matching.level3_name import verify_company_names
from src.matching.level4_address import analyze_addresses
from src.matching.level5_scoring import compute_final_score
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_matching_pipeline(record_a: dict, record_b: dict) -> dict:
    """
    runs a pair of records through all 5 matching levels.
    returns the full result including final score and classification.
    """
    name_a = record_a.get("name_clean", "unknown")
    name_b = record_b.get("name_clean", "unknown")
    logger.info(f"matching: '{name_a}' vs '{name_b}'")

    level_results = {}

    # level 1 — fast fuzzy match, no API calls
    logger.info("running level 1...")
    level_results["level1"] = exact_match_score(record_a, record_b)

    # level 2 — geo distance check
    logger.info("running level 2...")
    level_results["level2"] = geo_distance_check(record_a, record_b)

    # level 3 — LLM company name verification
    logger.info("running level 3...")
    level_results["level3"] = verify_company_names(record_a, record_b)

    # level 4 — LLM address deep analysis
    logger.info("running level 4...")
    level_results["level4"] = analyze_addresses(record_a, record_b)

    # level 5 — combine everything into final score
    logger.info("running level 5...")
    final = compute_final_score(level_results)

    return {
        "record_a": record_a.get("original_name") or record_a.get("name_clean", ""),
        "record_b": record_b.get("original_name") or record_b.get("name_clean", ""),
        "confidence_score": final["confidence_score"],
        "classification": final["classification"],
        "reasoning": final["reasoning"],
        "score_breakdown": final["score_breakdown"],
        "level_results": level_results,
    }


if __name__ == "__main__":
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

    result = run_matching_pipeline(a, b)

    print(f"\n{'='*50}")
    print(f"  {result['record_a']}  <>  {result['record_b']}")
    print(f"{'='*50}")
    print(f"  score:          {result['confidence_score']}/100")
    print(f"  classification: {result['classification']}")
    print(f"  reasoning:      {result['reasoning']}")
    print(f"\n  score breakdown:")
    for k, v in result["score_breakdown"].items():
        print(f"    {k}: {v}")