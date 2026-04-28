"""
run.py — main entry point for the MDM match engine

usage:
    python run.py
    python run.py --input data/test/sample_records.csv
"""

import argparse
from src.utils.loader import load_records
from src.preprocessing.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="MDM Match Engine")
    parser.add_argument("--input", default="data/test/sample_records.csv",
                        help="path to input CSV file")
    args = parser.parse_args()

    print(f"\nMDM Match Engine — Week 1")
    print(f"input: {args.input}\n")

    # load records from csv
    records = load_records(args.input)
    if not records:
        print("couldn't load any records, check the file path")
        return

    # run the pipeline — abbreviation expansion is slow since it calls the LLM
    # for each record, so this might take a minute
    print(f"running pipeline on {len(records)} records...")
    print("(step 3 - abbreviation expansion - is slow, it makes one API call per record)\n")

    processed, pairs = run_pipeline(records)

    # print results
    if not pairs:
        print("no candidate pairs found — try lowering SIMILARITY_THRESHOLD in .env")
        return

    print(f"\nfound {len(pairs)} candidate pairs:\n")
    for i, (a, b, sim) in enumerate(pairs, 1):
        name_a = processed[a].get("name_expanded") or processed[a].get("name_clean", "")
        name_b = processed[b].get("name_expanded") or processed[b].get("name_clean", "")
        print(f"  {i}. [{sim:.3f}]  {name_a!r}  <->  {name_b!r}")

    print(f"\nnext step: run these {len(pairs)} pairs through the level 1-5 matching engine (week 2)")


if __name__ == "__main__":
    main()