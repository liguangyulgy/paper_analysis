from __future__ import annotations

from src.analysis.evidence_classifier import classify_paper_evidence


def test_supplier_usage_is_level_a():
    candidates = classify_paper_evidence(
        {
            "title": "A model paper",
            "abstract": "Humanized mice were provided by genOway for this study.",
            "affiliations": "",
        }
    )

    supplier = [candidate for candidate in candidates if candidate.evidence_type == "supplier_usage"]

    assert len(supplier) == 1
    assert supplier[0].evidence_level == "A"
    assert supplier[0].needs_review is False


def test_affiliation_is_level_c_not_supplier_usage():
    candidates = classify_paper_evidence(
        {
            "title": "A mouse model paper",
            "abstract": "The study used mice.",
            "affiliations": "genOway, Lyon, France.",
        }
    )

    assert [(candidate.evidence_type, candidate.evidence_level) for candidate in candidates] == [
        ("author_affiliation", "C"),
    ]


def test_model_keyword_only_is_level_d():
    candidates = classify_paper_evidence(
        {
            "title": "Humanized BRGSF-HIS mice",
            "abstract": "",
            "affiliations": "",
        }
    )

    assert any(candidate.evidence_type == "keyword_only" for candidate in candidates)
    assert all(candidate.evidence_level == "D" for candidate in candidates)
