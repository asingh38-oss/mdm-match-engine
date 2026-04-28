"""
level5_scoring.py — level 5: final score computation

takes all the signals from levels 1-4 and combines them into
a single 0-100 confidence score + classification + reasoning.

weights are based on what we decided in the architecture doc.
we'll tune these in week 3 once we test against more data.
"""

from src.utils.config import classify
from src.utils.logger import get_logger

logger = get_logger(__name__)

# scoring weights — should add up to 1.0
# tuned based on testing, adjust if results look off
WEIGHTS = {
    "level1_name":    0.20,   # fuzzy name match
    "level1_address": 0.10,   # fuzzy address match
    "level2_geo":     0.20,   # geo distance
    "level3_name":    0.30,   # LLM name verification (most reliable signal)
    "level4_address": 0.20,   # LLM address analysis
}


def compute_final_score(level_results: dict) -> dict:
    """
    combines signals from levels 1-4 into a final confidence score.

    args:
        level_results: dict with keys "level1", "level2", "level3", "level4"
                       each containing the result dict from that level

    returns a dict with:
        - confidence_score: 0-100
        - classification: "High Confidence Match" | "Potential Match" | "Non-Match"
        - reasoning: plain english explanation of the final decision
        - score_breakdown: how each level contributed
    """
    l1 = level_results.get("level1", {})
    l2 = level_results.get("level2", {})
    l3 = level_results.get("level3", {})
    l4 = level_results.get("level4", {})

    # pull scores from each level, default to 50 (neutral) if missing
    name_score     = l1.get("name_score", 50)
    address_score  = l1.get("address_score", 50)
    geo_score      = l2.get("geo_score", 50)
    name_llm_score = l3.get("name_match_score", 50)
    addr_llm_score = l4.get("address_match_score", 50)

    # weighted combination
    score = (
        name_score     * WEIGHTS["level1_name"] +
        address_score  * WEIGHTS["level1_address"] +
        geo_score      * WEIGHTS["level2_geo"] +
        name_llm_score * WEIGHTS["level3_name"] +
        addr_llm_score * WEIGHTS["level4_address"]
    )
    score = round(min(max(score, 0), 100), 1)

    classification = classify(score)

    # build score breakdown for transparency
    breakdown = {
        "level1_name_contribution":    round(name_score * WEIGHTS["level1_name"], 1),
        "level1_address_contribution": round(address_score * WEIGHTS["level1_address"], 1),
        "level2_geo_contribution":     round(geo_score * WEIGHTS["level2_geo"], 1),
        "level3_name_contribution":    round(name_llm_score * WEIGHTS["level3_name"], 1),
        "level4_address_contribution": round(addr_llm_score * WEIGHTS["level4_address"], 1),
    }

    # build human readable reasoning
    reasoning_parts = []

    if l3.get("reasoning"):
        reasoning_parts.append(l3["reasoning"])

    if l4.get("reasoning"):
        reasoning_parts.append(l4["reasoning"])

    if l2.get("same_location"):
        reasoning_parts.append(f"Addresses are {l2.get('distance_miles', 0):.2f} miles apart — same location.")
    elif l2.get("different_office"):
        reasoning_parts.append(f"Addresses are {l2.get('distance_miles', 0):.1f} miles apart — likely different offices.")

    if l1.get("zip_match"):
        reasoning_parts.append(f"ZIP codes match ({l1.get('zip_clean', '')})")

    reasoning = " ".join(reasoning_parts) if reasoning_parts else "Scoring based on combined signals from all levels."

    logger.info(f"final score: {score} → {classification}")

    return {
        "confidence_score": score,
        "classification": classification,
        "reasoning": reasoning,
        "score_breakdown": breakdown,
    }


if __name__ == "__main__":
    # test with mock level results
    mock_results = {
        "level1": {"name_score": 77, "address_score": 100, "city_score": 100, "zip_match": True, "zip_clean": "28202"},
        "level2": {"geo_score": 95, "same_location": True, "different_office": False, "distance_miles": 0.0},
        "level3": {"name_match_score": 95, "is_same_company": True, "relationship": "legal entity variation", "reasoning": "Names differ only by legal entity suffix."},
        "level4": {"address_match_score": 98, "is_same_address": True, "issues_found": ["country name variation"], "reasoning": "Addresses are identical except country format."},
    }

    result = compute_final_score(mock_results)
    print(f"\nconfidence score: {result['confidence_score']}")
    print(f"classification: {result['classification']}")
    print(f"reasoning: {result['reasoning']}")
    print(f"\nbreakdown:")
    for k, v in result["score_breakdown"].items():
        print(f"  {k}: {v}")