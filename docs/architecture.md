# MDM Match Engine — Technical Design Document
*Week 1 Deliverable | Honeywell Capstone Project*

---

## Overview

This document covers the architecture, data flow, and technical decisions for the MDM Match Engine. It's meant to be the source of truth for the team during development so we're all building toward the same thing.

---

## Problem We're Solving

Honeywell's MDM system has duplicate Customer Master records caused by:
- Same company entered with slightly different names ("Boeing" vs "The Boeing Company")
- Multilingual entries of the same company (Japanese Toyota vs English Toyota)
- Address typos and formatting inconsistencies
- Abbreviations vs full words ("Intl" vs "International")
- Parent-subsidiary and trade name relationships ("Alphabet" vs "Google")

Our goal is to build a pipeline that catches these duplicates automatically.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT: MDM Records                       │
│         { name, address, city, state, zip, country }            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PRE-PROCESSING PIPELINE                      │
│                                                                 │
│  1. Language Detection (langdetect)                            │
│  2. Translation to English (Google Translate via deep-translator)│
│  3. Text Cleanup (lowercase, trim, strip punctuation, articles) │
│  4. Unicode Transliteration (unidecode)                        │
│  5. Entity Suffix Normalization (LLC → LLC, L.L.C. → LLC, etc.)│
│  6. LLM Abbreviation Expansion (Intl → International)         │
│  7. Street Abbreviation Expansion (Ave → Avenue, etc.)         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EMBEDDING GENERATION                          │
│                                                                 │
│  Format: "company: {name} || address: {addr} || city: {city}   │
│           || country: {country}"                               │
│  Model: all-MiniLM-L6-v2 (sentence-transformers)              │
│  Index: FAISS (cosine similarity via normalized inner product)  │
│  Output: Candidate pairs where similarity > threshold p        │
└────────────────────────────┬────────────────────────────────────┘
                             │ Candidate pairs (avoids O(n²))
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  5-LEVEL MATCHING ENGINE                        │
│                                                                 │
│  Level 1: Exact / Near-Exact Match                             │
│    → rapidfuzz token_sort_ratio on cleaned name + address      │
│    → If score ≥ 97/95 on both → short-circuit to Level 5      │
│                                                                 │
│  Level 2: Geo Distance Check                                   │
│    → Geocode both addresses via Google Maps API                │
│    → Distance < x miles + name match → same location          │
│    → Distance > y miles → likely different office              │
│                                                                 │
│  Level 3: Company Name Verification Agent (LLM)               │
│    → Handles: typos, abbreviations, parent-subsidiary,        │
│      trade names, transliterations                             │
│    → Returns: match decision + confidence + reasoning          │
│                                                                 │
│  Level 4: Address Deep Analysis Agent (LLM)                   │
│    → Decomposes address components                             │
│    → Checks: zip typos, street spelling, city-street mismatch │
│    → Returns: address match confidence + reasoning             │
│                                                                 │
│  Level 5: Final Score Computation                              │
│    → Combines signals from Levels 1–4 with weights            │
│    → Outputs: 0–100 confidence score + classification         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       OUTPUT                                    │
│                                                                 │
│  Per candidate pair:                                           │
│  {                                                             │
│    record_a_id, record_b_id,                                   │
│    confidence_score: 0-100,                                    │
│    classification: "High Confidence Match" |                   │
│                    "Potential Match" |                         │
│                    "Non-Match",                                │
│    reasoning: "Company names match after abbreviation         │
│                expansion. Same ZIP code. Address differs       │
│                slightly but geo check confirms same building." │
│  }                                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Scoring Weights (Preliminary — will tune in Week 3)

| Signal | Weight |
|--------|--------|
| Level 1 — Exact/fuzzy name match | 30% |
| Level 1 — Exact/fuzzy address match | 15% |
| Level 2 — Geo distance result | 20% |
| Level 3 — LLM name verification confidence | 25% |
| Level 4 — Address deep analysis confidence | 10% |

These weights are a starting guess. We'll calibrate against our test dataset in Week 3.

---

## Classification Thresholds

| Score | Label |
|-------|-------|
| > 85 | High Confidence Match |
| 60–85 | Potential Match (needs human review) |
| < 60 | Non-Match |

---

## Tool / API Selections

### LLM
- **Primary**: OpenAI GPT-4o
- **Reasoning**: Good multilingual support, reliable structured output, available via API
- **Fallback**: Anthropic Claude (swap in via `LLM_PROVIDER` env var)

### Translation
- **Primary**: Google Translate via `deep-translator` Python library
- **Why not an LLM for this?**: Translation is a solved problem and a dedicated API is cheaper + faster at scale. LLM handles the harder stuff (name verification, address analysis).

### Geo API
- **Primary**: Google Maps Geocoding API
- **Why**: Most comprehensive address coverage globally, handles international addresses well

### Embedding Model
- **Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Why**: Fast, lightweight, good semantic similarity. Doesn't need to be state-of-the-art since it's just for candidate selection — the LLM agents handle the hard matching.

### Vector Index
- **Library**: FAISS (Facebook AI Similarity Search)
- **Why**: Industry standard, runs locally, no external dependency

---

## Data Flow

```
CSV/DB Export → pandas DataFrame
→ clean_record() [cleaner.py]
→ enrich_record_with_translations() [language.py]
→ expand_record_abbreviations() [abbreviations.py]
→ generate_embeddings() [embeddings.py]
→ find_candidate_pairs() [embeddings.py]
→ For each pair → run_matching_pipeline() [orchestrator.py]
→ Output results DataFrame / JSON
```

---

## Known Edge Cases to Test Against

1. **Transliterations**: Japanese Toyota (株式会社トヨタ) vs English Toyota
2. **Parent-subsidiary**: Google LLC vs Alphabet Inc.
3. **Trade names**: Kentucky Fried Chicken vs KFC
4. **Multiple offices**: Lockheed Martin HQ vs Lockheed Martin plant in different city
5. **Typos in company name**: "Boieng" vs "Boeing"
6. **Typos in address**: "Rockldge Dr" vs "Rockledge Drive"
7. **Abbreviation variants**: "Intl Business Machines Corp" vs "International Business Machines"
8. **Non-standard address formats**: PO Box vs street address for same company
9. **Different country format**: "US" vs "USA" vs "United States"

---

## Open Questions (for team discussion)

- What's the actual volume of records in Honeywell's MDM? Affects whether FAISS flat index is sufficient or we need a more scalable approach.
- Do we have ground truth labels (known duplicates) to evaluate against?
- Are there specific language distributions we know about? (Helps us prioritize translation testing)
- What happens with matches between a parent company and its subsidiaries — do we flag those or treat as non-matches?

---

*Last updated: Week 1*
