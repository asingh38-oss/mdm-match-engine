# Findings and Next Steps

results from running the full MDM Match Engine against the 20-record test dataset.

## Test Dataset

20 synthetic records covering multilingual entries, abbreviation variants, typos,
parent-subsidiary relationships, multiple offices, and formatting differences.

## Results Summary

12 candidate pairs were found above the embedding similarity threshold (0.75).
After running all 5 matching levels:

| classification | count |
|----------------|-------|
| High Confidence Match (>85) | 3 |
| Potential Match (60-85) | 5 |
| Non-Match (<60) | 4 |

## What Worked Well

**Abbreviation expansion** — the LLM correctly expanded "Honeywell Intl" to
"honeywell international" and "Boieng Corp" to "Boeing Corporation" before matching.
This was one of the core requirements and it worked reliably across all records.

**German company matching** — Müller GmbH & Co. KG vs Muller GmbH Co KG scored 89.0
(High Confidence Match). Unicode transliteration converted the umlaut, and the LLM
correctly identified them as the same entity despite different formatting.

**Lockheed Martin duplicates** — the two Bethesda records (same address, slightly
different name formats) both scored 86.0 (High Confidence Match). Level 3 correctly
identified "Lockheed Martin Corporation" and "Lockheed Martin Corp." as exact matches.

**Lockheed Martin multiple offices** — the Bethesda HQ vs the Arlington office
correctly scored 55-57 (Non-Match). Level 4 caught that the addresses were completely
different (Rockledge Drive vs Crystal Drive) and pulled the score down appropriately
even though level 3 thought the names matched.

**Airbus multilingual** — "Airbus S.A.S." vs "AIRBUS SAS" scored 76.1 after the LLM
identified "société par actions simplifiée" as the French legal designation for SAS.
Addresses matched at 100%. Scored Potential Match rather than High Confidence mainly
because level 1 fuzzy match was low due to the expanded French name being very different
from the abbreviation.

## What Didn't Work

**Toyota Japanese transliteration** — Japanese Toyota (株式会社トヨタ自動車) got
transliterated to "zhu shi hui she toyotazi dong che" which GPT didn't recognize as
Toyota. Scored 49.2 (Non-Match) even though the addresses were identical (100/100).
The transliteration is too lossy — the Chinese phonetic rendering of Japanese characters
doesn't preserve enough of the original meaning for the LLM to identify the company.
Fix: use Google Translate to translate to English before embedding instead of just
transliterating.

**"GE Company" → "bro mate"** — langdetect misidentified "ge company" as Catalan and
Google Translate returned a nonsense translation. GE Company never made it into the
candidate pairs because the embedding was gibberish. Fix: add a minimum character
threshold (15+ chars) before attempting language detection.

**Geo check completely non-functional** — all 12 pairs returned REQUEST_DENIED from
Google Maps, defaulting to a neutral score of 50 for level 2. This pulled scores down
significantly. Honeywell scored 83.9 (Potential Match) instead of what would likely be
90+ with geo working. Fix: enable billing on Google Cloud Console.

**Honeywell just under High Confidence** — scored 83.9, just under the 85 threshold.
With geo working this would likely push it over. Could also lower the threshold to 80
for the final deliverable.

**Boeing/Boieng typo pairs scored as Potential** — "Boeing Company" vs "Boieng Corp"
scored 80.0. The typo ("Boieng") was correctly caught by abbreviation expansion and
level 3 identified them as the same company, but the level 1 fuzzy score was lower
because the names still look quite different after expansion.

## Threshold Observations

The current threshold of 85 for High Confidence is slightly too strict given that geo
is non-functional. With geo offline, legitimate matches are losing ~17 points (geo
contribution of 95 × 0.20 weight vs the neutral 50 × 0.20). Lowering
HIGH_CONFIDENCE_THRESHOLD to 80 would correctly classify Honeywell and most Boeing
pairs as High Confidence while still keeping the different-office Lockheed pairs as
Non-Match.

## Next Steps for Production

**Fix geo billing** — enable billing on Google Cloud Console. This alone would improve
most scores by 10-17 points and fix the Honeywell false Potential Match.

**Fix Toyota transliteration** — route Japanese/Chinese/Korean text through Google
Translate to English instead of just transliterating with unidecode.

**Fix short name language detection** — add a minimum character threshold before
calling langdetect to prevent "GE Company" type false detections.

**Get real Honeywell data** — the POC is validated on synthetic records. The real test
is running against actual Customer Master records with known duplicates to measure
precision and recall.

**Add batch processing** — for large datasets, parallelize the LLM calls using async
to avoid making hundreds of sequential API calls.

**Cache geocoding results** — the same addresses appear in multiple pairs. A simple
dict cache would cut geocoding API calls by 50%+.

**Human review workflow** — Potential Match records need a human to make the final
call. Build a simple review interface or at minimum a clean CSV export for data stewards.