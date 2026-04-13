"""
test_cleaner.py — Unit tests for the text normalization pipeline.
Run with: pytest tests/unit/test_cleaner.py -v
"""

import pytest
from src.preprocessing.cleaner import (
    basic_clean,
    strip_articles,
    normalize_entity_suffixes,
    clean_company_name,
    clean_address_field,
)


class TestBasicClean:
    def test_lowercase(self):
        assert basic_clean("BOEING") == "boeing"

    def test_strips_whitespace(self):
        assert basic_clean("  Boeing  ") == "boeing"

    def test_removes_punctuation(self):
        assert basic_clean("Boeing, Inc.") == "boeing inc"

    def test_collapses_internal_spaces(self):
        assert basic_clean("Boeing   Company") == "boeing company"

    def test_empty_string(self):
        assert basic_clean("") == ""

    def test_none_returns_empty(self):
        assert basic_clean(None) == ""


class TestStripArticles:
    def test_strips_the(self):
        assert strip_articles("the boeing company") == "boeing company"

    def test_strips_a(self):
        assert strip_articles("a company") == "company"

    def test_no_article(self):
        assert strip_articles("boeing company") == "boeing company"

    def test_article_in_middle_not_stripped(self):
        # Only strips leading articles
        assert strip_articles("bank of the west") == "bank of the west"


class TestEntitySuffixes:
    def test_llc_normalization(self):
        assert normalize_entity_suffixes("company l.l.c.") == "company LLC"

    def test_inc_normalization(self):
        assert normalize_entity_suffixes("company inc.") == "company INC"

    def test_corp_normalization(self):
        assert normalize_entity_suffixes("boeing corp") == "boeing CORP"

    def test_gmbh_normalization(self):
        assert normalize_entity_suffixes("siemens gmbh") == "siemens GMBH"


class TestCleanCompanyName:
    def test_full_pipeline(self):
        result = clean_company_name("The Boeing Company, Inc.")
        assert "the" not in result.split()   # article stripped
        assert "INC" in result               # suffix normalized
        assert result == result.strip()      # no trailing whitespace

    def test_handles_unicode(self):
        result = clean_company_name("Müller GmbH")
        assert "Muller" in result or "muller" in result   # transliterated

    def test_empty_returns_empty(self):
        assert clean_company_name("") == ""
