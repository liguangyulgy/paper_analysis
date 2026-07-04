from __future__ import annotations

from src.utils.normalizers import normalize_doi, normalize_pmcid, normalize_pmid, normalize_title


def test_normalize_doi_removes_prefix_case_and_trailing_punctuation():
    assert normalize_doi(" DOI: 10.1234/ABC. ") == "10.1234/abc"
    assert normalize_doi("https://doi.org/10.5555/Example);") == "10.5555/example"
    assert normalize_doi("http://dx.doi.org/10.7777/MixedCase") == "10.7777/mixedcase"


def test_normalize_pmid_keeps_digits_only():
    assert normalize_pmid("PMID: 12345678") == "12345678"
    assert normalize_pmid(" 12 34-56 ") == "123456"


def test_normalize_pmcid_uppercases_and_adds_prefix_for_numeric_values():
    assert normalize_pmcid("pmcid: pmc12345.") == "PMC12345"
    assert normalize_pmcid("12345") == "PMC12345"


def test_normalize_title_casefolds_and_collapses_whitespace():
    assert normalize_title("  A   Humanized Mouse STUDY  ") == "a humanized mouse study"
