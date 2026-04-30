"""
tests/unit/test_orchestrator.py — tests for run_matching_pipeline

mocks OpenAI and Google Maps API calls to avoid real API calls.
"""

import unittest
from unittest.mock import patch, MagicMock

from src.matching.orchestrator import run_matching_pipeline


class TestRunMatchingPipeline(unittest.TestCase):
    """Test cases for run_matching_pipeline function."""

    def _create_mock_records(self):
        """Create sample records for testing."""
        return (
            {
                "original_name": "Honeywell International Inc",
                "name_clean": "honeywell international inc",
                "name_expanded": "Honeywell International Incorporated",
                "address_clean": "300 south tryon street",
                "address_expanded": "300 South Tryon Street",
                "city_clean": "charlotte",
                "state_clean": "nc",
                "zip_clean": "28202",
                "country_clean": "usa",
            },
            {
                "original_name": "Honeywell Intl",
                "name_clean": "honeywell intl",
                "name_expanded": "Honeywell International",
                "address_clean": "300 south tryon street",
                "address_expanded": "300 South Tryon Street",
                "city_clean": "charlotte",
                "state_clean": "nc",
                "zip_clean": "28202",
                "country_clean": "united states",
            },
        )

    @patch("src.matching.level2_geo.requests.get")
    @patch("src.matching.level3_name.OpenAI")
    @patch("src.matching.level4_address.OpenAI")
    def test_result_has_all_expected_keys(self, mock_l4, mock_l3, mock_requests):
        """Test that result contains all required keys."""
        # Setup mocks
        mock_requests.return_value.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 35.22, "lng": -80.84}}}]
        }
        
        mock_l3.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"name_match_score": 95, "is_same_company": true, '
            '"relationship": "exact match", "reasoning": "same company"}'
        )
        
        mock_l4.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"address_match_score": 95, "is_same_address": true, '
            '"issues_found": [], "reasoning": "same address"}'
        )

        record_a, record_b = self._create_mock_records()
        result = run_matching_pipeline(record_a, record_b)

        # Assert all expected keys are present
        expected_keys = [
            "record_a",
            "record_b",
            "confidence_score",
            "classification",
            "reasoning",
            "score_breakdown",
            "level_results",
        ]
        for key in expected_keys:
            self.assertIn(key, result, f"Missing expected key: {key}")

    @patch("src.matching.level2_geo.requests.get")
    @patch("src.matching.level3_name.OpenAI")
    @patch("src.matching.level4_address.OpenAI")
    def test_classification_is_valid(self, mock_l4, mock_l3, mock_requests):
        """Test that classification is one of the valid values."""
        valid_classifications = [
            "High Confidence Match",
            "Potential Match",
            "Non-Match",
        ]

        # Test with high confidence match response
        mock_requests.return_value.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 35.22, "lng": -80.84}}}]
        }
        
        mock_l3.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"name_match_score": 95, "is_same_company": true, '
            '"relationship": "exact match", "reasoning": "same"}'
        )
        
        mock_l4.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"address_match_score": 95, "is_same_address": true, '
            '"issues_found": [], "reasoning": "same"}'
        )

        record_a, record_b = self._create_mock_records()
        result = run_matching_pipeline(record_a, record_b)

        self.assertIn(
            result["classification"],
            valid_classifications,
            f"Invalid classification: {result['classification']}",
        )

    @patch("src.matching.level2_geo.requests.get")
    @patch("src.matching.level3_name.OpenAI")
    @patch("src.matching.level4_address.OpenAI")
    def test_confidence_score_in_valid_range(self, mock_l4, mock_l3, mock_requests):
        """Test that confidence_score is between 0 and 100."""
        # Setup mocks
        mock_requests.return_value.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 35.22, "lng": -80.84}}}]
        }
        
        mock_l3.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"name_match_score": 95, "is_same_company": true, '
            '"relationship": "exact match", "reasoning": "same"}'
        )
        
        mock_l4.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"address_match_score": 95, "is_same_address": true, '
            '"issues_found": [], "reasoning": "same"}'
        )

        record_a, record_b = self._create_mock_records()
        result = run_matching_pipeline(record_a, record_b)

        self.assertGreaterEqual(
            result["confidence_score"],
            0,
            f"Confidence score {result['confidence_score']} is less than 0",
        )
        self.assertLessEqual(
            result["confidence_score"],
            100,
            f"Confidence score {result['confidence_score']} is greater than 100",
        )

    @patch("src.matching.level2_geo.requests.get")
    @patch("src.matching.level3_name.OpenAI")
    @patch("src.matching.level4_address.OpenAI")
    def test_potential_match_classification(self, mock_l4, mock_l3, mock_requests):
        """Test that Potential Match classification is returned for mid-range scores."""
        # Setup mocks for potential match (lower scores)
        mock_requests.return_value.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 35.22, "lng": -80.84}}}]
        }
        
        mock_l3.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"name_match_score": 60, "is_same_company": false, '
            '"relationship": "unknown", "reasoning": "unclear"}'
        )
        
        mock_l4.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"address_match_score": 55, "is_same_address": false, '
            '"issues_found": ["zip code mismatch"], "reasoning": "possible"}'
        )

        record_a, record_b = self._create_mock_records()
        result = run_matching_pipeline(record_a, record_b)

        self.assertIn(result["classification"], ["High Confidence Match", "Potential Match", "Non-Match"])

    @patch("src.matching.level2_geo.requests.get")
    @patch("src.matching.level3_name.OpenAI")
    @patch("src.matching.level4_address.OpenAI")
    def test_non_match_classification(self, mock_l4, mock_l3, mock_requests):
        """Test that Non-Match classification is returned for low scores."""
        # Setup mocks for non-match (very low scores)
        mock_requests.return_value.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 35.22, "lng": -80.84}}}]
        }
        
        mock_l3.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"name_match_score": 10, "is_same_company": false, '
            '"relationship": "different", "reasoning": "different companies"}'
        )
        
        mock_l4.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"address_match_score": 15, "is_same_address": false, '
            '"issues_found": ["completely different addresses"], "reasoning": "different"}'
        )

        record_a, record_b = self._create_mock_records()
        result = run_matching_pipeline(record_a, record_b)

        self.assertIn(result["classification"], ["High Confidence Match", "Potential Match", "Non-Match"])

    @patch("src.matching.level2_geo.requests.get")
    @patch("src.matching.level3_name.OpenAI")
    @patch("src.matching.level4_address.OpenAI")
    def test_level_results_contains_all_levels(self, mock_l4, mock_l3, mock_requests):
        """Test that level_results contains results from all 4 levels."""
        # Setup mocks
        mock_requests.return_value.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 35.22, "lng": -80.84}}}]
        }
        
        mock_l3.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"name_match_score": 95, "is_same_company": true, '
            '"relationship": "exact match", "reasoning": "same"}'
        )
        
        mock_l4.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"address_match_score": 95, "is_same_address": true, '
            '"issues_found": [], "reasoning": "same"}'
        )

        record_a, record_b = self._create_mock_records()
        result = run_matching_pipeline(record_a, record_b)

        level_results = result["level_results"]
        
        # Check that all 4 levels have results
        for level in ["level1", "level2", "level3", "level4"]:
            self.assertIn(
                level,
                level_results,
                f"Missing level results for {level}",
            )


if __name__ == "__main__":
    unittest.main()