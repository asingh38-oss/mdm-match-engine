"""
test_loader.py
run with: pytest tests/unit/test_loader.py -v
"""

import csv
import pytest
from src.utils.loader import load_records


@pytest.fixture
def sample_csv(tmp_path):
    # make a small test csv in a temp folder
    f = tmp_path / "test.csv"
    with open(f, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "address", "city", "state", "zip", "country"])
        writer.writeheader()
        writer.writerow({"name": "Boeing", "address": "100 N Riverside", "city": "Chicago", "state": "IL", "zip": "60606", "country": "USA"})
        writer.writerow({"name": "Airbus", "address": "1 Rond Point", "city": "Blagnac", "state": "", "zip": "31707", "country": "France"})
        writer.writerow({"name": "Lockheed Martin", "address": "6801 Rockledge Dr", "city": "Bethesda", "state": "MD", "zip": "20817", "country": "USA"})
    return f


@pytest.fixture
def missing_columns_csv(tmp_path):
    # csv that only has name column, rest are missing
    f = tmp_path / "missing.csv"
    with open(f, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["name"])
        writer.writeheader()
        writer.writerow({"name": "Boeing"})
    return f


def test_loads_correct_count(sample_csv):
    records = load_records(str(sample_csv))
    assert len(records) == 3


def test_returns_list_of_dicts(sample_csv):
    records = load_records(str(sample_csv))
    assert isinstance(records, list)
    assert isinstance(records[0], dict)


def test_record_has_expected_keys(sample_csv):
    records = load_records(str(sample_csv))
    for key in ["name", "address", "city", "state", "zip", "country"]:
        assert key in records[0]


def test_values_are_correct(sample_csv):
    records = load_records(str(sample_csv))
    assert records[0]["name"] == "Boeing"
    assert records[0]["city"] == "Chicago"


def test_missing_columns_doesnt_crash(missing_columns_csv):
    # missing columns should come back as None, not throw an error
    records = load_records(str(missing_columns_csv))
    assert isinstance(records, list)
    assert records[0]["address"] is None


def test_bad_path_returns_empty_list():
    records = load_records("data/doesnt_exist.csv")
    assert records == []