import pytest
import os
import pandas as pd

# Try different possible import paths for loader
try:
    from src.loader import load_csv
except ImportError:
    try:
        from src.data.loader import load_csv
    except ImportError:
        load_csv = None


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    file_path = tmp_path / "sample.csv"
    data = pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "email": ["a@test.com", "b@test.com", "c@test.com"]
    })
    data.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def missing_column_csv(tmp_path):
    """CSV missing required column (email)."""
    file_path = tmp_path / "missing.csv"
    data = pd.DataFrame({
        "id": [1, 2],
        "name": ["Alice", "Bob"]
    })
    data.to_csv(file_path, index=False)
    return file_path


def test_loader_import():
    """Ensure loader function exists."""
    assert load_csv is not None, "load_csv function not found in expected modules"


def test_load_csv_success(sample_csv):
    """Test CSV loads correctly and returns correct number of records."""
    records = load_csv(sample_csv)

    assert records is not None
    assert len(records) == 3


def test_load_csv_structure(sample_csv):
    """Test records have expected structure."""
    records = load_csv(sample_csv)

    # Assuming list of dicts
    assert isinstance(records, list)
    assert isinstance(records[0], dict)

    assert "id" in records[0]
    assert "name" in records[0]
    assert "email" in records[0]


def test_missing_columns(missing_column_csv):
    """Test loader handles missing required columns."""
    with pytest.raises(Exception):
        load_csv(missing_column_csv)


def test_empty_file(tmp_path):
    """Test empty CSV handling."""
    file_path = tmp_path / "empty.csv"
    pd.DataFrame().to_csv(file_path, index=False)

    with pytest.raises(Exception):
        load_csv(file_path)
