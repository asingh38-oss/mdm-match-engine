"""
abbreviations.py — LLM-based abbreviation expansion for company names.

Some duplicates exist just because one record uses "Intl" and another uses
"International", or "Mfg" vs "Manufacturing". We use an LLM to expand
known abbreviations before matching so these don't trip up the pipeline.

We also handle common street abbreviations here (St → Street, Ave → Avenue, etc.)
since that helps with address matching downstream.
"""

import os
from openai import OpenAI
from src.utils.config import LLM_MODEL, OPENAI_API_KEY
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Hardcoded street abbreviation map — no LLM needed for these
STREET_ABBREV_MAP = {
    r"\bst\b": "street",
    r"\bave\b": "avenue",
    r"\bblvd\b": "boulevard",
    r"\bdr\b": "drive",
    r"\brd\b": "road",
    r"\bln\b": "lane",
    r"\bct\b": "court",
    r"\bpl\b": "place",
    r"\bhwy\b": "highway",
    r"\bpkwy\b": "parkway",
    r"\bsq\b": "square",
    r"\bn\b": "north",
    r"\bs\b": "south",
    r"\be\b": "east",
    r"\bw\b": "west",
    r"\bste\b": "suite",
    r"\bapt\b": "apartment",
    r"\bfl\b": "floor",
}

import re

def expand_street_abbreviations(address: str) -> str:
    """Rule-based expansion of common street abbreviations. Fast, no API call."""
    for pattern, replacement in STREET_ABBREV_MAP.items():
        address = re.sub(pattern, replacement, address, flags=re.IGNORECASE)
    return address


def expand_company_abbreviations_llm(name: str) -> str:
    """
    Use an LLM to expand abbreviations in a company name.
    Returns the expanded name, or the original if the LLM doesn't change it.

    Examples:
        "Intl Business Machines" → "International Business Machines"
        "Gen Motors Corp" → "General Motors Corporation"
        "Am Airlines" → "American Airlines"
    """
    if not name or len(name) < 3:
        return name

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""You are a data cleaning assistant for a Master Data Management system.

Your task: Expand any abbreviations in the following company name to their full form.

Rules:
- Only expand clear, common abbreviations (e.g., "Intl" → "International", "Mfg" → "Manufacturing")
- Do NOT change proper nouns or acronyms that are themselves the official name (e.g., "IBM", "BMW", "HSBC" should stay as-is)
- Do NOT add words that aren't implied by the abbreviation
- If there are no abbreviations to expand, return the name unchanged
- Return ONLY the resulting company name, nothing else

Company name: {name}"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100,
        )
        expanded = response.choices[0].message.content.strip()
        if expanded and expanded.lower() != name.lower():
            logger.info(f"Abbreviation expanded: '{name}' → '{expanded}'")
        return expanded if expanded else name
    except Exception as e:
        logger.warning(f"Abbreviation expansion failed for '{name}': {e}")
        return name  # graceful fallback


def expand_record_abbreviations(record: dict) -> dict:
    """
    Runs abbreviation expansion on a cleaned record.
    Updates name_translated and address_translated fields in-place.
    """
    name = record.get("name_translated", record.get("name_clean", ""))
    address = record.get("address_translated", record.get("address_clean", ""))

    record["name_expanded"] = expand_company_abbreviations_llm(name)
    record["address_expanded"] = expand_street_abbreviations(address)

    return record


if __name__ == "__main__":
    test_names = [
        "Intl Business Machines Corp",
        "Gen Dynamics",
        "Am Express Co",
        "Natl Grid PLC",
        "IBM",       # should stay as IBM
        "BMW AG",    # should stay as BMW AG
    ]

    for name in test_names:
        expanded = expand_company_abbreviations_llm(name)
        print(f"{name!r:40} → {expanded!r}")
