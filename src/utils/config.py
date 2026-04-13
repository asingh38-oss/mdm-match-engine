"""
config.py — Central place for all config, thresholds, and constants.
Load environment variables here so the rest of the codebase doesn't
have to deal with os.getenv() everywhere.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- Geo ---
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GEO_MATCH_DISTANCE_MILES = float(os.getenv("GEO_MATCH_DISTANCE_MILES", 0.5))
GEO_DIFF_OFFICE_MILES = float(os.getenv("GEO_DIFF_OFFICE_MILES", 50.0))

# --- Matching thresholds ---
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.75))
HIGH_CONFIDENCE_THRESHOLD = int(os.getenv("HIGH_CONFIDENCE_THRESHOLD", 85))
POTENTIAL_MATCH_THRESHOLD = int(os.getenv("POTENTIAL_MATCH_THRESHOLD", 60))

# --- Embedding ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # fast + good enough for candidate selection
EMBEDDING_FIELD_FORMAT = "company: {name} || address: {address} || city: {city} || country: {country}"

# --- Classification labels ---
CLASS_HIGH = "High Confidence Match"
CLASS_POTENTIAL = "Potential Match"
CLASS_NONE = "Non-Match"

def classify(score: float) -> str:
    if score > HIGH_CONFIDENCE_THRESHOLD:
        return CLASS_HIGH
    elif score >= POTENTIAL_MATCH_THRESHOLD:
        return CLASS_POTENTIAL
    else:
        return CLASS_NONE
