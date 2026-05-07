# Project Requirements Traceability

This document maps the capstone brief to the current proof-of-concept implementation so the team can quickly explain scope coverage during reviews.

## Core Objective

Build an enterprise-style MDM matching engine that compares likely duplicate customer master records and returns:

- a `0-100` confidence score
- a classification bucket
- a human-readable reasoning summary

## Requirement Mapping

| requirement from brief | current implementation area | notes |
|---|---|---|
| multilingual normalization | `src/preprocessing/language.py`, `src/preprocessing/cleaner.py` | translation and unicode normalization are handled in preprocessing |
| abbreviation handling | `src/preprocessing/abbreviations.py` | LLM-assisted expansion supports improved name consistency |
| embedding-based candidate selection | `src/preprocessing/embeddings.py` | narrows comparisons before the multi-level matcher runs |
| exact match stage | `src/matching/level1_exact.py` | first-pass name and address agreement checks |
| geo-distance stage | `src/matching/level2_geo.py` | uses Google geocoding and distance thresholds |
| reasoning-based company name verification | `src/matching/level3_name.py` | LLM-assisted judgment for typos, aliases, and related-company patterns |
| address-aware deep analysis | `src/matching/level4_address.py` | LLM-assisted address component review |
| final score computation | `src/matching/level5_scoring.py` | combines signals into one confidence score |
| match classification thresholds | `src/utils/config.py`, `src/matching/level5_scoring.py` | supports high-confidence, potential, and non-match outcomes |
| end-to-end orchestration | `src/matching/orchestrator.py`, `run.py` | coordinates all matching levels for each candidate pair |

## Alignment With Weekly Plan

### Week 1

- preprocessing pipeline exists
- candidate generation exists
- technical design notes exist in `docs/architecture.md`
- threshold notes exist in `docs/threshold_calibration.md`

### Week 2

- levels 2 through 4 are implemented as separate matching stages
- orchestration logic exists to run those stages in sequence

### Week 3

- score computation and classification exist
- reasoning output is included in final results
- findings are captured in `docs/findings.md`

## Demo Talking Points

- The system avoids brute-force pairwise comparison by generating candidate pairs first.
- The matching decision is explainable because each level contributes evidence to the final result.
- The architecture is modular enough to tune thresholds or swap providers later.
- The same staged design can be extended to other master-data domains after the customer POC.

## Current POC Boundaries

- external APIs still influence completeness and runtime stability
- geo quality depends on Google Maps configuration and address quality
- threshold calibration is still a tuning exercise, not a finalized production policy
- parent-subsidiary handling may need business-rule clarification before production use
