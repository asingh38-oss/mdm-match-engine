"""
cleaner.py — Text normalization and cleanup for MDM records.

Handles: lowercase, whitespace trimming, punctuation removal,
article stripping, and unicode transliteration.

This runs first in the pipeline before language detection or LLM calls
since clean text makes everything downstream more reliable.
"""

import re
import unicodedata
from unidecode import unidecode


# Articles and common filler words we strip from company names
# Add more as we find them in the actual MDM data
ARTICLES_TO_STRIP = {
    "the", "a", "an",           # English
    "le", "la", "les", "un",    # French
    "der", "die", "das", "ein", # German
    "el", "la", "los", "las",   # Spanish
    "il", "lo", "la", "gli",    # Italian
}

# Common legal entity suffixes — we keep these but normalize them
# so "LLC" and "L.L.C." and "llc" all become "LLC"
ENTITY_SUFFIX_MAP = {
    r"\bl\.?l\.?c\.?\b": "LLC",
    r"\binc\.?\b": "INC",
    r"\bcorp\.?\b": "CORP",
    r"\bco\.?\b": "CO",
    r"\bltd\.?\b": "LTD",
    r"\bgmbh\b": "GMBH",
    r"\bs\.?a\.?\b": "SA",
    r"\bb\.?v\.?\b": "BV",
    r"\bplc\b": "PLC",
    r"\bpte\.?\b": "PTE",
    r"\bpvt\.?\b": "PVT",
    r"\bsrl\b": "SRL",
    r"\bspa\b": "SPA",
    r"\bag\b": "AG",
    r"\bnv\b": "NV",
    r"\bllp\b": "LLP",
}


def normalize_unicode(text: str) -> str:
    """
    Normalize unicode characters. Converts things like accented characters
    to their ASCII equivalents (e.g. "Müller" → "Muller").
    Useful for fuzzy matching across different encodings.
    """
    if not text:
        return ""
    # First normalize unicode form
    text = unicodedata.normalize("NFKC", text)
    # Then transliterate to ASCII
    return unidecode(text)


def basic_clean(text: str) -> str:
    """
    Core cleaning step:
    - Lowercase
    - Strip leading/trailing whitespace
    - Collapse internal whitespace
    - Remove punctuation except hyphens (needed for some addresses)
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\-]", " ", text)   # remove punctuation, keep hyphens
    text = re.sub(r"\s+", " ", text)          # collapse whitespace
    return text.strip()


def strip_articles(text: str) -> str:
    """
    Remove leading articles from company names.
    "The Boeing Company" → "Boeing Company"
    """
    words = text.split()
    if words and words[0].lower() in ARTICLES_TO_STRIP:
        words = words[1:]
    return " ".join(words)


def normalize_entity_suffixes(text: str) -> str:
    """
    Standardize legal entity suffixes so they don't throw off matching.
    Works on already-lowercased text, then uppercases the matched suffix.
    """
    for pattern, replacement in ENTITY_SUFFIX_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def clean_company_name(name: str) -> str:
    """
    Full normalization pipeline for a company name field.
    Run this before embedding generation or LLM calls.
    """
    if not name:
        return ""
    name = normalize_unicode(name)
    name = basic_clean(name)
    name = strip_articles(name)
    name = normalize_entity_suffixes(name)
    return name.strip()


def clean_address_field(field: str) -> str:
    """
    Normalize a single address component (street, city, state, etc.).
    Lighter touch than company name — we want to preserve structure.
    """
    if not field:
        return ""
    field = normalize_unicode(field)
    field = basic_clean(field)
    return field.strip()


def clean_record(record: dict) -> dict:
    """
    Clean a full MDM record dict.

    Expected keys: name, address, city, state, zip, country
    Returns a new dict with cleaned values + originals preserved.
    """
    cleaned = {
        "original_name": record.get("name", ""),
        "original_address": record.get("address", ""),
        "original_city": record.get("city", ""),
        "original_state": record.get("state", ""),
        "original_zip": record.get("zip", ""),
        "original_country": record.get("country", ""),
        "name_clean": clean_company_name(record.get("name", "")),
        "address_clean": clean_address_field(record.get("address", "")),
        "city_clean": clean_address_field(record.get("city", "")),
        "state_clean": clean_address_field(record.get("state", "")),
        "zip_clean": str(record.get("zip", "")).strip(),
        "country_clean": clean_address_field(record.get("country", "")),
    }
    return cleaned


# Quick sanity check if you run this file directly
if __name__ == "__main__":
    test_cases = [
        {"name": "The Boeing Company, Inc.", "address": "100 N. Riverside Plaza", "city": "Chicago", "state": "IL", "zip": "60606", "country": "USA"},
        {"name": "Müller GmbH & Co. KG", "address": "Industriestraße 12", "city": "München", "state": "Bavaria", "zip": "80333", "country": "Germany"},
        {"name": "ALPHABET INC", "address": "1600 Amphitheatre Pkwy", "city": "Mountain View", "state": "CA", "zip": "94043", "country": "United States"},
    ]

    for record in test_cases:
        cleaned = clean_record(record)
        print(f"Original: {record['name']!r:40} → Cleaned: {cleaned['name_clean']!r}")
