# src/matching/level4_address.py

import json
from openai import OpenAI

client = OpenAI()


def _safe_json_loads(text: str):
    """
    Try to parse model output as JSON.
    Falls back to extracting the first JSON object if needed.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise ValueError("Could not parse JSON from model response.")


def analyze_addresses(address_1: str, address_2: str, model: str = "gpt-4.1-mini"):
    """
    Compare two addresses by decomposing them into components and asking GPT
    to reason about whether they refer to the same place.

    Returns:
        {
            "address_match_score": float,
            "is_same_address": bool,
            "issues_found": list,
            "reasoning": str
        }
    """

    prompt = f"""
You are an address matching assistant for master data management.

Your task is to compare these two addresses and decide whether they refer to the same physical address.

Address 1:
{address_1}

Address 2:
{address_2}

Instructions:
1. Break each address into likely parts if possible:
   - street number
   - street name
   - street type
   - apartment/unit/suite
   - city
   - state
   - postal code
   - country
2. Compare each component carefully.
3. Account for common variations:
   - St vs Street
   - Rd vs Road
   - Apt vs Apartment
   - missing unit numbers
   - abbreviations
   - punctuation differences
   - minor formatting differences
4. Identify possible problems such as:
   - different street number
   - different postal code
   - missing unit number
   - mismatched city/state
   - unclear formatting
5. Return ONLY valid JSON in this exact format:

{{
  "address_match_score": 0.0,
  "is_same_address": false,
  "issues_found": [],
  "reasoning": ""
}}

Rules:
- address_match_score must be between 0 and 1
- is_same_address should be true only if the two addresses likely refer to the same location
- issues_found should be a list of short strings
- reasoning should be brief but clear
"""

    response = client.responses.create(
        model=model,
        input=prompt
    )

    text = response.output_text.strip()
    result = _safe_json_loads(text)

    return {
        "address_match_score": float(result.get("address_match_score", 0.0)),
        "is_same_address": bool(result.get("is_same_address", False)),
        "issues_found": result.get("issues_found", []),
        "reasoning": result.get("reasoning", "")
    }


if __name__ == "__main__":
    a1 = "123 N Main St Apt 4B, Charlotte, NC 28202, USA"
    a2 = "123 North Main Street #4B, Charlotte, NC 28202"

    result = analyze_addresses(a1, a2)
    print(json.dumps(result, indent=2))
