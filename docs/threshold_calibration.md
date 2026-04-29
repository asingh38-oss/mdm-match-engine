# Threshold Calibration

## Goal

The goal of threshold calibration is to decide what match score should count as a true match in the MDM matching pipeline. Since the pipeline gives a score for possible record matches, we need to test different thresholds and choose one that balances accuracy, false matches, and missed matches.

## Pipeline Tested

The full matching pipeline was run end to end through the matching orchestrator.

Pipeline order:

1. Level 1 matching
2. Level 2 matching
3. Level 3 matching
4. Level 4 address matching

Each level adds more detail to the matching process. Earlier levels find possible candidate matches, while later levels provide stronger comparison and reasoning.

## Thresholds Tested

The following threshold values were tested:

- 0.60
- 0.70
- 0.75
- 0.80
- 0.85
- 0.90

Lower thresholds allowed more records to be marked as matches, but also increased the chance of false positives. Higher thresholds were stricter, but they missed some records that were likely the same entity.

## Results Summary

| Threshold | Result |
|---|---|
| 0.60 | Too loose. More possible matches were found, but there were also more incorrect matches. |
| 0.70 | Better, but still allowed some questionable matches. |
| 0.75 | Good balance between catching matches and avoiding obvious false positives. |
| 0.80 | Strong overall threshold. Most matches looked reliable. |
| 0.85 | More strict, but some likely matches were missed. |
| 0.90 | Too strict. Only very obvious matches were accepted. |

## Chosen Threshold

The selected threshold is:

```python
MATCH_THRESHOLD = 0.80
