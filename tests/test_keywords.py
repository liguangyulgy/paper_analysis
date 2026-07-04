from __future__ import annotations

from src.analysis.keywords import KeywordRule, load_keyword_rules, match_keywords


def test_load_keyword_rules_supports_flat_keyword_groups(tmp_path):
    config = tmp_path / "keywords.yaml"
    config.write_text(
        """
company_keywords:
  - genOway
model_keywords:
  - BRGSF
""",
        encoding="utf-8",
    )

    rules = load_keyword_rules(config)

    assert [(rule.keyword, rule.keyword_group) for rule in rules] == [
        ("genOway", "company"),
        ("BRGSF", "model"),
    ]


def test_match_keywords_returns_field_and_evidence_sentence():
    rules = [
        KeywordRule(keyword="genOway", keyword_group="company", source_config="test"),
        KeywordRule(keyword="BRGSF", keyword_group="model", source_config="test"),
    ]

    hits = match_keywords(
        {
            "title": "BRGSF mouse model study",
            "abstract": "The mouse model was obtained from genOway. Other text follows.",
        },
        rules,
    )

    assert [(hit.keyword, hit.keyword_group, hit.matched_field) for hit in hits] == [
        ("BRGSF", "model", "title"),
        ("genOway", "company", "abstract"),
    ]
    assert hits[1].evidence_sentence == "The mouse model was obtained from genOway."
