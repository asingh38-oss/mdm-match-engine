"""
run.py — main entry point for the MDM match engine

loads records from a CSV, runs preprocessing, finds candidate pairs,
then runs each pair through the full 5-level matching pipeline.
outputs results to the terminal and saves to a CSV.

usage:
    python run.py
    python run.py --input data/test/sample_records.csv
    python run.py --input data/test/sample_records.csv --output data/results.csv
"""

import argparse
import csv
from src.utils.loader import load_records
from src.preprocessing.pipeline import run_pipeline
from src.matching.orchestrator import run_matching_pipeline


def main():
    parser = argparse.ArgumentParser(description="MDM Match Engine")
    parser.add_argument("--input", default="data/test/sample_records.csv", help="path to input CSV")
    parser.add_argument("--output", default="data/results.csv", help="path to save results CSV")
    args = parser.parse_args()

    print(f"\nMDM Match Engine — Week 3 (Final)")
    print(f"input: {args.input}\n")

    # load records
    records = load_records(args.input)
    if not records:
        print("couldn't load any records, check the file path")
        return

    # run preprocessing — this takes a minute since it makes one API call per record
    print(f"running preprocessing pipeline on {len(records)} records...")
    print("(abbreviation expansion is slow — one API call per record)\n")
    processed, pairs = run_pipeline(records)

    if not pairs:
        print("no candidate pairs found — try lowering SIMILARITY_THRESHOLD in .env")
        return

    print(f"found {len(pairs)} candidate pairs, running matching pipeline...\n")

    # run each pair through all 5 levels
    results = []
    for i, (a, b, sim) in enumerate(pairs, 1):
        print(f"  [{i}/{len(pairs)}] matching pair...")
        result = run_matching_pipeline(processed[a], processed[b])
        result["embedding_similarity"] = round(sim, 3)
        results.append(result)

    # print summary
    print(f"\n{'='*65}")
    print(f"  RESULTS — {len(results)} pairs evaluated")
    print(f"{'='*65}\n")

    high = [r for r in results if r["classification"] == "High Confidence Match"]
    potential = [r for r in results if r["classification"] == "Potential Match"]
    non_match = [r for r in results if r["classification"] == "Non-Match"]

    print(f"  High Confidence Matches:  {len(high)}")
    print(f"  Potential Matches:        {len(potential)}")
    print(f"  Non-Matches:              {len(non_match)}")
    print()

    for r in results:
        score = r["confidence_score"]
        label = r["classification"]
        print(f"  [{score:5.1f}] {label}")
        print(f"         {r['record_a']}")
        print(f"         {r['record_b']}")
        print(f"         {r['reasoning'][:120]}")
        print()

    # save to CSV
    if results:
        fieldnames = ["record_a", "record_b", "confidence_score", "classification", "reasoning", "embedding_similarity"]
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
        print(f"results saved to {args.output}")


if __name__ == "__main__":
    main()