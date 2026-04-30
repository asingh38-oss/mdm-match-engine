import pytest
from src.matching.level5_scoring import compute_final_score


def make_strong_match():
    return {
        "level1": {"name_score": 95, "address_score": 98, "city_score": 100, "zip_match": True},
        "level2": {"geo_score": 95, "same_location": True, "different_office": False, "distance_miles": 0.0},
        "level3": {"name_match_score": 98, "is_same_company": True, "relationship": "exact_match", "reasoning": "Names are identical."},
        "level4": {"address_match_score": 97, "is_same_address": True, "issues_found": [], "reasoning": "Addresses match."},
    }


def make_weak_match():
    return {
        "level1": {"name_score": 20, "address_score": 10, "city_score": 15, "zip_match": False},
        "level2": {"geo_score": 10, "same_location": False, "different_office": True, "distance_miles": 500.0},
        "level3": {"name_match_score": 15, "is_same_company": False, "relationship": "none", "reasoning": "Names differ."},
        "level4": {"address_match_score": 10, "is_same_address": False, "issues_found": ["mismatch"], "reasoning": "Addresses differ."},
    }


def make_middle_match():
    return {
        "level1": {"name_score": 65, "address_score": 60, "city_score": 70, "zip_match": True},
        "level2": {"geo_score": 60, "same_location": True, "different_office": False, "distance_miles": 2.0},
        "level3": {"name_match_score": 70, "is_same_company": True, "relationship": "partial_match", "reasoning": "Names somewhat similar."},
        "level4": {"address_match_score": 65, "is_same_address": True, "issues_found": [], "reasoning": "Addresses close."},
    }


def test_strong_match_high_confidence():
    result = compute_final_score(make_strong_match())
    assert result["confidence_score"] > 85
    assert result["classification"] == "High Confidence Match"


def test_weak_match_non_match():
    result = compute_final_score(make_weak_match())
    assert result["confidence_score"] < 60
    assert result["classification"] == "Non-Match"


def test_middle_match_potential():
    result = compute_final_score(make_middle_match())
    assert 60 <= result["confidence_score"] <= 85
    assert result["classification"] == "Potential Match"


def test_score_bounds():
    result = compute_final_score(make_strong_match())
    assert 0 <= result["confidence_score"] <= 100


def test_reasoning_exists_and_not_empty():
    result = compute_final_score(make_middle_match())
    assert "reasoning" in result
    assert isinstance(result["reasoning"], str)
    assert len(result["reasoning"].strip()) > 0


def test_score_breakdown_has_5_entries():
    result = compute_final_score(make_middle_match())
    assert "score_breakdown" in result
    assert isinstance(result["score_breakdown"], dict)
    assert len(result["score_breakdown"]) == 5


def test_empty_input_does_not_crash():
    result = compute_final_score({})
    assert result is not None
    assert "confidence_score" in result
    assert "classification" in result