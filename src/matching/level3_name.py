"""
level3_name.py — Level 3 of the matching pipeline: company name verification agent.

Use GPT-4o to semantically analyze two company names and determine if they likely refer
to the same company. This handles complex cases like:
  - Different legal entity types (Inc vs LLC vs Corp)
  - Parent company vs subsidiary relationships
  - Holding company vs operating company
  - Acronym vs full name (IBM vs International Business Machines)
  - Regional variations (Company Ltd vs Company Inc)

"""

import json
from openai import OpenAI
from src.utils.config import LLM_MODEL, OPENAI_API_KEY
from src.utils.logger import get_logger

logger = get_logger(__name__)


def verify_company_names(record_a: dict, record_b: dict) -> dict:
    """
    Level 3 company name verification — use GPT-4o to semantically analyze
    whether two company names likely refer to the same company.

    Args:
        record_a: first record dict with 'name_expanded' or 'name_clean'
        record_b: second record dict with 'name_expanded' or 'name_clean'

    Returns:
        dict with keys:
            - name_match_score: 0-100 confidence that names refer to same company
            - is_same_company: bool, True if GPT believes they're the same entity
            - relationship: str, classification of relationship (e.g. "exact match", "parent-subsidiary", "holding-operating")
            - reasoning: str, plain english explanation of the GPT's analysis
    """
    name_a = record_a.get("name_expanded") or record_a.get("name_clean", "")
    name_b = record_b.get("name_expanded") or record_b.get("name_clean", "")

    if not name_a or not name_b:
        logger.warning("empty company names provided to verify_company_names")
        return {
            "name_match_score": 0,
            "is_same_company": False,
            "relationship": "unknown",
            "reasoning": "One or both company names are empty",
        }

    logger.info(f"Verifying company names: '{name_a}' vs '{name_b}'")

    prompt = f"""You are an expert data analyst specializing in Master Data Management (MDM) and company record matching.

Your task: Analyze the two company names below and determine if they likely refer to the same company entity.

Company A: {name_a}
Company B: {name_b}

Consider the following scenarios:
1. **Exact match**: Names are identical or nearly identical (e.g., "Apple Inc" vs "Apple Inc")
2. **Legal entity variations**: Same company, different entity types (e.g., "Microsoft Corporation" vs "Microsoft Inc")
3. **Abbreviation variations**: Same company, different abbreviation format (e.g., "IBM" vs "International Business Machines")
4. **Parent-subsidiary**: One is a subsidiary of the other (e.g., "Google LLC" vs "Alphabet Inc" — related but DIFFERENT entities)
5. **Acronym vs full name**: Same company using different name forms (e.g., "General Motors" vs "GM")
6. **Regional variations**: Same company, different regional naming (e.g., "Banco Santander SA" vs "Santander Bank")
7. **False positives**: Different companies that sound similar (e.g., "Apple Inc" vs "Applebee's")

Return a JSON object with exactly these fields:
{{
    "name_match_score": <0-100 integer representing confidence they're the same company>,
    "is_same_company": <boolean — true if names very likely refer to the SAME company entity>,
    "relationship": <string — one of: "exact match", "legal entity variation", "abbreviation variation", "acronym match", "regional variation", "parent-subsidiary", "different companies", "unclear">,
    "reasoning": <string — brief explanation of the analysis, 1-2 sentences>
}}

Guidelines:
- A parent-subsidiary relationship (e.g., Alphabet-Google) should score 40-60 because they are RELATED but SEPARATE entities
- A legal entity variation (Microsoft Inc vs Microsoft Corporation) should score 90+
- An exact match or clear abbreviation match should score 95+
- Different companies should score 0-20
- Return ONLY the JSON object, no additional text
"""

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,
        )

        response_text = response.choices[0].message.content.strip()

        # Parse JSON from response
        result = json.loads(response_text)

        # Validate and sanitize the response
        name_match_score = int(result.get("name_match_score", 0))
        name_match_score = max(0, min(100, name_match_score))  # clamp to 0-100

        is_same_company = bool(result.get("is_same_company", False))
        relationship = str(result.get("relationship", "unclear")).lower()
        reasoning = str(result.get("reasoning", "No explanation provided"))

        logger.info(
            f"Company name verification complete: score={name_match_score}, "
            f"same_company={is_same_company}, relationship={relationship}"
        )

        return {
            "name_match_score": name_match_score,
            "is_same_company": is_same_company,
            "relationship": relationship,
            "reasoning": reasoning,
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse GPT response as JSON: {e}")
        return {
            "name_match_score": 0,
            "is_same_company": False,
            "relationship": "error",
            "reasoning": f"Failed to parse GPT response: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Company name verification failed: {e}")
        return {
            "name_match_score": 0,
            "is_same_company": False,
            "relationship": "error",
            "reasoning": f"Verification failed: {str(e)}",
        }


if __name__ == "__main__":
    test_pairs = [
        (
            {"name_clean": "Apple Inc", "name_expanded": "Apple Incorporated"},
            {"name_clean": "Apple Inc", "name_expanded": "Apple Incorporated"},
        ),
        (
            {"name_clean": "IBM", "name_expanded": "International Business Machines"},
            {"name_clean": "International Business Machines Corp", "name_expanded": "International Business Machines Corporation"},
        ),
        (
            {"name_clean": "Google LLC", "name_expanded": "Google LLC"},
            {"name_clean": "Alphabet Inc", "name_expanded": "Alphabet Incorporated"},
        ),
        (
            {"name_clean": "Microsoft Corp", "name_expanded": "Microsoft Corporation"},
            {"name_clean": "Apple Inc", "name_expanded": "Apple Incorporated"},
        ),
        (
            {"name_clean": "Gen Motors", "name_expanded": "General Motors"},
            {"name_clean": "GM Corp", "name_expanded": "General Motors Corporation"},
        ),
    ]

    print("Testing company name verification...\n")
    for i, (record_a, record_b) in enumerate(test_pairs, 1):
        print(f"Test {i}: '{record_a['name_expanded']}' vs '{record_b['name_expanded']}'")
        result = verify_company_names(record_a, record_b)
        for key, value in result.items():
            print(f"  {key}: {value}")
        print()
