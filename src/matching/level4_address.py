"""
level4_address.py — level 4: address deep analysis agent

uses GPT to do a detailed component-level comparison of two addresses.
checks for zip typos, street spelling errors, missing unit numbers, city mismatches, etc.

builds on level 2 (geo) — geo tells us how far apart they are,
this tells us *why* the addresses look different even if they're close.
"""

import json
from openai import OpenAI
from src.utils.config import OPENAI_API_KEY, LLM_MODEL
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _safe_json_parse(text: str) -> dict:
    """tries to parse JSON from the model response, handles edge cases"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # sometimes GPT wraps it in markdown code blocks, strip those
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise ValueError(f"couldn't parse JSON from response: {text[:100]}")


def analyze_addresses(record_a: dict, record_b: dict) -> dict:
    """
    level 4 check — uses GPT to compare two addresses at a component level.

    returns a dict with:
        - address_match_score: 0-100
        - is_same_address: bool
        - issues_found: list of strings describing discrepancies
        - reasoning: plain english explanation
    """
    # build address strings from record fields
    def build_addr(r):
        parts = [
            r.get("address_expanded") or r.get("address_clean", ""),
            r.get("city_clean", ""),
            r.get("state_clean", ""),
            r.get("zip_clean", ""),
            r.get("country_clean", ""),
        ]
        return ", ".join(p for p in parts if p)

    addr_a = build_addr(record_a)
    addr_b = build_addr(record_b)

    if not addr_a or not addr_b:
        logger.warning("empty address string, skipping level 4")
        return {
            "address_match_score": 50,
            "is_same_address": False,
            "issues_found": ["one or both addresses are empty"],
            "reasoning": "can't analyze empty addresses",
        }

    logger.info(f"analyzing addresses: '{addr_a[:60]}' vs '{addr_b[:60]}'")

    prompt = f"""You are an address matching assistant for a Master Data Management system.

Compare these two addresses and decide if they refer to the same physical location.

Address 1: {addr_a}
Address 2: {addr_b}

Break each address into components (street number, street name, city, state, zip, country)
and compare them carefully. Account for common variations like:
- St vs Street, Rd vs Road, Ave vs Avenue
- abbreviations and punctuation differences
- missing or extra unit/suite numbers
- minor typos in street names or zip codes

Return ONLY valid JSON in this exact format:
{{
  "address_match_score": <0-100 integer>,
  "is_same_address": <true or false>,
  "issues_found": ["list", "of", "issues"],
  "reasoning": "brief plain english explanation"
}}

Guidelines:
- identical or near-identical addresses → 95+
- same address with minor formatting differences → 85-95
- same street but different unit → 60-80
- different zip codes → investigate, could be typo or different location
- different city or state → likely not the same address, score 0-30
- Return ONLY the JSON object, no extra text"""

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,
        )

        result = _safe_json_parse(response.choices[0].message.content.strip())

        score = int(result.get("address_match_score", 0))
        score = max(0, min(100, score))  # clamp to 0-100

        logger.info(f"address analysis complete: score={score}, same_address={result.get('is_same_address')}")

        return {
            "address_match_score": score,
            "is_same_address": bool(result.get("is_same_address", False)),
            "issues_found": result.get("issues_found", []),
            "reasoning": str(result.get("reasoning", "no explanation provided")),
        }

    except Exception as e:
        logger.error(f"address analysis failed: {e}")
        return {
            "address_match_score": 50,  # neutral fallback
            "is_same_address": False,
            "issues_found": [f"analysis failed: {str(e)}"],
            "reasoning": "GPT analysis failed, falling back to neutral score",
        }


if __name__ == "__main__":
    test_pairs = [
        (
            {"address_clean": "100 north riverside plaza", "city_clean": "chicago", "state_clean": "il", "zip_clean": "60606", "country_clean": "usa"},
            {"address_clean": "100 n riverside plz", "city_clean": "chicago", "state_clean": "il", "zip_clean": "60606", "country_clean": "united states"},
        ),
        (
            {"address_clean": "100 rockledge drive", "city_clean": "bethesda", "state_clean": "md", "zip_clean": "20817", "country_clean": "usa"},
            {"address_clean": "100 rockldge dr", "city_clean": "bethesda", "state_clean": "md", "zip_clean": "20817", "country_clean": "usa"},
        ),
        (
            {"address_clean": "123 main street", "city_clean": "chicago", "state_clean": "il", "zip_clean": "60601", "country_clean": "usa"},
            {"address_clean": "123 main street", "city_clean": "austin", "state_clean": "tx", "zip_clean": "78701", "country_clean": "usa"},
        ),
    ]

    for a, b in test_pairs:
        print(f"\n'{a['address_clean']}, {a['city_clean']}' vs '{b['address_clean']}, {b['city_clean']}'")
        result = analyze_addresses(a, b)
        for k, v in result.items():
            print(f"  {k}: {v}")