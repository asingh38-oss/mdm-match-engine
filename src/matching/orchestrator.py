# src/matching/orchestrator.py

from src.matching.level1 import run_level1
from src.matching.level2 import run_level2
from src.matching.level3 import run_level3
from src.matching.level4 import run_level4


def run_pipeline(records):
    print("Running Level 1...")
    level1_matches = run_level1(records)

    print("Running Level 2...")
    level2_matches = run_level2(level1_matches)

    print("Running Level 3...")
    level3_matches = run_level3(level2_matches)

    print("Running Level 4...")
    level4_matches = run_level4(level3_matches)

    return level4_matches


if __name__ == "__main__":
    # sample test input (replace with your real data loader)
    sample_records = [
        {"name": "John Smith", "email": "john@gmail.com"},
        {"name": "Jon Smith", "email": "johnsmith@gmail.com"},
        {"name": "Jane Doe", "email": "jane@gmail.com"},
    ]

    results = run_pipeline(sample_records)

    print("\nFinal Matches:")
    for r in results:
        print(r)
