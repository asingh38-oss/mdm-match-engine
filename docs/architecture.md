# MDM Match Engine — Technical Design Doc
Week 1 | Honeywell Capstone

This doc covers the architecture, data flow, and tool decisions for the match engine. Trying to keep this updated as we build so everyone's on the same page.

## Problem We're Solving

Honeywell's MDM system has duplicate Customer Master records showing up because of things like same company entered with slightly different names ("Boeing" vs "The Boeing Company"), multilingual entries of the same company (Japanese Toyota vs English Toyota), address typos, abbreviations vs full words ("Intl" vs "International"), and parent-subsidiary relationships ("Alphabet" vs "Google").

The goal is to build a pipeline that catches these automatically instead of someone having to manually find them.

## Architecture

```
input: MDM records { name, address, city, state, zip, country }
      │
      ▼
pre-processing
  1. language detection
  2. translation to english
  3. text cleanup (lowercase, trim, punctuation, articles)
  4. unicode transliteration
  5. entity suffix normalization (L.L.C. → LLC, etc.)
  6. abbreviation expansion via LLM (Intl → International)
  7. street abbreviation expansion (Ave → Avenue, etc.)
      │
      ▼
embedding generation
  - each record gets encoded as:
    "company: {name} || address: {addr} || city: {city} || country: {country}"
  - indexed with FAISS for similarity search
  - candidate pairs pulled above similarity threshold
  - avoids O(n²) brute force comparison
      │
      ▼
5-level matching engine
  level 1 → exact / near-exact match (rapidfuzz)
  level 2 → geo distance check (google maps API)
  level 3 → company name verification (LLM)
  level 4 → address deep analysis (LLM)
  level 5 → final score computation
      │
      ▼
output per pair:
  {
    record_a_id, record_b_id,
    confidence_score: 0-100,
    classification: "High Confidence Match" | "Potential Match" | "Non-Match",
    reasoning: "plain english explanation of why it matched or didn't"
  }
```

## Scoring Weights

These are preliminary — we'll tune them in week 3 once we have real data to test against.

| signal | weight |
|--------|--------|
| level 1 — exact/fuzzy name match | 30% |
| level 1 — exact/fuzzy address match | 15% |
| level 2 — geo distance result | 20% |
| level 3 — LLM name verification confidence | 25% |
| level 4 — address deep analysis confidence | 10% |

## Classification Thresholds

| score | label |
|-------|-------|
| > 85 | High Confidence Match |
| 60–85 | Potential Match (needs human review) |
| < 60 | Non-Match |

## Tool Selections

**LLM — OpenAI GPT-4o**
Good multilingual support and reliable structured output. We added Anthropic Claude as a fallback that can be swapped in via the `LLM_PROVIDER` env var if needed.

**Translation — Google Translate via deep-translator**
We decided not to use the LLM for translation since it's a solved problem and a dedicated API is way cheaper and faster at scale. The LLM handles the harder stuff like name verification and address analysis.

**Geo API — Google Maps Geocoding**
Most comprehensive address coverage globally, handles international addresses well. Needed for level 2 distance checks.

**Embedding Model — all-MiniLM-L6-v2**
Fast and lightweight, good enough for candidate selection. Doesn't need to be state-of-the-art here since the LLM agents do the actual hard matching — this just narrows down the pairs we need to check.

**Vector Index — FAISS**
Runs locally, no external dependency, industry standard for this kind of similarity search.

## Data Flow

```
CSV/DB export
→ clean_record()                     [cleaner.py]
→ enrich_record_with_translations()  [language.py]
→ expand_record_abbreviations()      [abbreviations.py]
→ generate_embeddings()              [embeddings.py]
→ find_candidate_pairs()             [embeddings.py]
→ run_matching_pipeline()            [orchestrator.py]  ← week 2
→ output results as JSON / CSV
```

## Edge Cases We're Testing Against

1. transliterations — Japanese Toyota (株式会社トヨタ) vs English Toyota
2. parent-subsidiary — Google LLC vs Alphabet Inc.
3. trade names — Kentucky Fried Chicken vs KFC
4. multiple offices — Lockheed Martin HQ vs a different Lockheed Martin location
5. typos in company name — "Boieng" vs "Boeing"
6. typos in address — "Rockldge Dr" vs "Rockledge Drive"
7. abbreviation variants — "Intl Business Machines Corp" vs "International Business Machines"
8. non-standard address formats — PO Box vs street address for same company
9. country format differences — "US" vs "USA" vs "United States"

## Open Questions

- What's the actual record volume in Honeywell's MDM? Will affect whether a FAISS flat index is good enough or if we need something more scalable.
- Do we have ground truth labels (known duplicates) to evaluate against?
- What language distributions exist in the real data? Helps us prioritize translation testing.
- How do we handle parent-subsidiary matches — flag them as matches or non-matches?

